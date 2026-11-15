#!/bin/sh
set -eu

rm -f /tmp/sdv-bootstrap-ready /tmp/sdv-bootstrap-error
python3 -u /startup_mounts/scripts/local-receiver.py &
receiver_pid=$!
echo "$receiver_pid" > /tmp/sdv-local-receiver.pid
sleep 1
if ! kill -0 "$receiver_pid" 2>/dev/null; then
    echo "Local HTTP receiver failed to start" >&2
    exit 1
fi
/bin/sh /startup_mounts/scripts/bootstrap-leda.sh &
exec /bin/bash /docker/leda-quickstart-docker-entrypoint-x86.sh
