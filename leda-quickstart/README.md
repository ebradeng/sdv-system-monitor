# Leda Docker quickstart tire-pressure test

This folder is an independent copy of the newer, single-vehicle quickstart
implementation. The original Leda implementation remains in `../leda`.
Run the commands below from this folder in PowerShell.

The Compose service starts the original quickstart entrypoint, a local HTTP
test receiver, and `scripts/bootstrap-leda.sh`. Bootstrap waits for Leda and
Kanto, imports the Zenoh router and tire telemetry image archives into Leda,
and starts three host-networked Kanto containers: `zenoh-router`,
`sdv-tire-connector`, and `sdv-http-bridge`. The bridge posts to the local
receiver in the outer Docker container, not Cloud Run.

The tire sensor runs separately on Windows. The KUKSA–Zenoh provider is not
used for this path: it publishes individual signals rather than the combined
cloud payload.

## Prepare image archives

The two `images/*.tar` archives are local generated inputs and are ignored by
Git. They have been copied to this folder on the current machine. On a fresh
clone, recreate them with:

```powershell
New-Item -ItemType Directory -Force images
docker pull --platform linux/amd64 eclipse/zenoh:1.10.1
docker image save --output images\zenoh-1.10.1.tar eclipse/zenoh:1.10.1
docker build --platform linux/amd64 -f Dockerfile.telemetry -t sdv-telemetry:tire-v1 .
docker image save --output images\sdv-telemetry-tire-v1.tar sdv-telemetry:tire-v1
```

Rebuild and export the telemetry image whenever its Python source changes.
`docker compose up` does not build or export these images. Updating an image
under the same tag does not replace existing inner Kanto containers; explicitly
manage those containers or use a fresh outer container after backing up guest
data.

## Start and inspect

The existing deployment and this copy use the same outer container name and
host ports, so they cannot run simultaneously. Do not remove or recreate your
existing container until you have backed up any guest data you need.

```powershell
docker compose up -d
docker compose ps
docker compose logs -f leda_car_1
```

Healthy means bootstrap completed and the local receiver is running; it does
not prove end-to-end telemetry delivery. Errors appear in the logs. Leda may
take several minutes to boot. To inspect the inner containers:

```powershell
docker exec leda_1 ssh -p 2222 root@127.0.0.1 kanto-cm list
docker exec leda_1 ssh -p 2222 root@127.0.0.1 kanto-cm logs --tail 20 --name sdv-tire-connector
docker exec leda_1 ssh -p 2222 root@127.0.0.1 kanto-cm logs --tail 20 --name sdv-http-bridge
```

Install the requirements in a Windows virtual environment, then run the
sensor in a separate terminal:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\mock_tire_pressure.py --host 127.0.0.1 --port 55555
```

Look for `Local telemetry:` in the Compose logs. The connector waits for all
four wheels before publishing, using vehicle ID `sdv1`. The local receiver
uses a test-only API key; no cloud credentials are required.

The quickstart VM filesystem lives inside its outer container: deleting or
recreating that container discards guest changes unless storage is separately
persisted. Bootstrap stages the images again in a new container.
