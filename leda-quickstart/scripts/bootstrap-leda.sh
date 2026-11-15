#!/bin/sh
set -eu

fail() {
    echo "Leda bootstrap failed; inspect the preceding error" >&2
    touch /tmp/sdv-bootstrap-error
}
trap fail EXIT

vehicle_id=${VEHICLE_ID:-sdv1}
case "$vehicle_id" in
    ''|*[!a-zA-Z0-9_-]*) echo "Invalid VEHICLE_ID: $vehicle_id" >&2; exit 1 ;;
esac

ssh_opts="-o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
echo "Waiting for Leda SSH..."
attempt=0
until ssh $ssh_opts -p 2222 root@127.0.0.1 true; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 120 ]; then
        echo "Timed out waiting for Leda" >&2
        exit 1
    fi
    sleep 5
done

for image in zenoh-1.10.1.tar sdv-telemetry-tire-v1.tar; do
    if [ ! -f "/startup_mounts/images/$image" ]; then
        echo "Missing image archive: /startup_mounts/images/$image" >&2
        exit 1
    fi
done

ssh $ssh_opts -p 2222 root@127.0.0.1 mkdir -p /data/sdv-images
scp $ssh_opts -P 2222 /startup_mounts/images/zenoh-1.10.1.tar \
    /startup_mounts/images/sdv-telemetry-tire-v1.tar root@127.0.0.1:/data/sdv-images/

ssh $ssh_opts -p 2222 root@127.0.0.1 sh -s -- "$vehicle_id" <<'GUEST'
set -eu
vehicle_id=$1
attempt=0
until kanto-cm list >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    if [ "$attempt" -ge 60 ]; then
        echo "Timed out waiting for Kanto" >&2
        exit 1
    fi
    sleep 5
done

ctr --namespace kanto-cm images import /data/sdv-images/zenoh-1.10.1.tar
ctr --namespace kanto-cm images import /data/sdv-images/sdv-telemetry-tire-v1.tar

ensure_container() {
    name=$1
    image=$2
    shift 2
    if kanto-cm get --name "$name" >/dev/null 2>&1; then
        actual=$(kanto-cm get --name "$name" | python3 -c 'import json,sys; print(json.load(sys.stdin)["image"]["name"])')
        if [ "$actual" != "$image" ]; then
            echo "$name already exists with unexpected image $actual; refusing to replace it" >&2
            exit 1
        fi
        if ! kanto-cm get --name "$name" | python3 -c '
import json, sys
data = json.load(sys.stdin)
expected = sys.argv[1:]
actual = (data.get("config") or {}).get("cmd") or []
if data["host_config"]["network_mode"] != "host" or (expected and actual != expected):
    print("Existing container configuration does not match bootstrap; refusing to replace it", file=sys.stderr)
    sys.exit(1)
' "$@"; then
            echo "Configuration mismatch for $name" >&2
            exit 1
        fi
        running=$(kanto-cm get --name "$name" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["running"])')
        if [ "$running" = "True" ]; then
            echo "$name is already running"
            return
        fi
    else
        kanto-cm create --name "$name" --network host --rp unless-stopped "$image" "$@"
    fi
    kanto-cm start --name "$name"
    attempt=0
    while [ "$(kanto-cm get --name "$name" | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"]["running"])')" != "True" ]; do
        attempt=$((attempt + 1))
        if [ "$attempt" -ge 30 ]; then
            echo "$name did not reach running state" >&2
            exit 1
        fi
        sleep 2
    done
}

ensure_container zenoh-router docker.io/eclipse/zenoh:1.10.1
ensure_container sdv-tire-connector docker.io/library/sdv-telemetry:tire-v1 \
    python /app/zenoh_connector.py --host 127.0.0.1 --port 30555 \
    --vehicle-id "$vehicle_id" --connect tcp/127.0.0.1:7447 --require-complete
ensure_container sdv-http-bridge docker.io/library/sdv-telemetry:tire-v1 \
    env SDV_API_KEY=local-test-key python /app/zenoh_to_cloud.py \
    --connect tcp/127.0.0.1:7447 --url http://10.0.2.2:18080
GUEST

touch /tmp/sdv-bootstrap-ready
trap - EXIT
echo "Leda bootstrap completed; HTTP target is the local receiver."
