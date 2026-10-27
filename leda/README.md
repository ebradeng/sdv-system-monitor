# Leda: Kuksa Mock Sensor + Zenoh Connector

Simulated tire pressure for one vehicle, running inside **Eclipse Leda**:

```
mock_tire_pressure.py ──▶ Kuksa databroker (in Leda) ──▶ zenoh_connector.py ──Zenoh──▶ ../bridges/zenoh_to_cloud.py ──HTTP──▶ Google Cloud
```

| | |
|---|---|
| Signals | `Vehicle.Chassis.Axle.Row{1,2}.Wheel.{Left,Right}.Tire.Pressure` (VSS, `uint16`, kPa) |
| Values | around 230 kPa, each tire varies on its own, 1 reading per second |
| Zenoh key | `sdv/<vehicle-id>/tire_pressure` (default `sdv/sdv1/tire_pressure`) |
| Payload (JSON) | `{"vehicleId": "sdv1", "timestamp": "...", "tirePressure_kPa": {"frontLeft": 230, "frontRight": 229, "rearLeft": 231, "rearRight": 228}}` |

Tested with **Leda v0.1.0-M3** (QEMU ARM64) on macOS.

## Files

| File | Purpose |
|---|---|
| `mock_tire_pressure.py` | Mock sensor: writes all four tire pressures to the Kuksa databroker |
| `zenoh_connector.py` | Subscribes to the four signals in Kuksa and publishes each update over Zenoh as JSON |
| `zenoh_listener.py` | Prints everything received on Zenoh (a stand-in for the cloud when testing) |
| `watch_signal.py` | Prints the tire signals straight from Kuksa (to check the sensor works) |
| `docker-compose.yml` | Local Kuksa databroker for testing without Leda |
| `test_*.py` | Unit tests (`pytest`) |

## 1. Setup (on your computer)

Needs Python 3.11+.

```bash
cd leda
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

## 2. Start Leda

1. Download `eclipse-leda-qemu-arm64.tar.xz` (Apple Silicon) or `eclipse-leda-qemu-x86_64.tar.xz` (Intel/AMD)
   from [Leda's official releases](https://github.com/eclipse-leda/leda-distro/releases/tag/v0.1.0-M3) and extract it.
2. Start it from that folder with `./run-leda.sh` (needs QEMU). Booting takes a few minutes.
3. Log in as `root` (no password). Wait about a minute, then check `kanto-cm list` shows `databroker` **Running**.

Leda's databroker is on port **30555**, and SSH on port **2222**. Inside Leda, the host computer is at `10.0.2.2`.

## 3. Install Zenoh in Leda (one time)

Leda has Python and a Kuksa client but no `pip`, and its system disk is small, so Zenoh goes on the `/data` disk
(it survives reboots). Run from your computer, in this folder:

```bash
ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@127.0.0.1 "python3 -m venv --system-site-packages /data/sdv-venv && /data/sdv-venv/bin/python -m pip install --only-binary=:all: eclipse-zenoh==1.10.1 && mkdir -p /data/sdv-mvp"
```

```bash
scp -O -P 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null mock_tire_pressure.py zenoh_connector.py root@127.0.0.1:/data/sdv-mvp/
```

Re-run the `scp` command whenever the scripts change.

## 4. Run it

Use separate terminals, started in this order (receiver first, so no messages are missed).

**Terminal 1 (your computer): receiver.** Either print the messages:

```bash
python zenoh_listener.py --listen tcp/127.0.0.1:7447
```

or send them to Google Cloud with the bridge in `../bridges/` (same `.venv` activated):

```bash
cd ../bridges
export SDV_API_KEY='paste-the-key-here'
python zenoh_to_cloud.py
```

**Terminal 2 (inside Leda): Zenoh connector.**

```bash
ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@127.0.0.1
cd /data/sdv-mvp && /data/sdv-venv/bin/python zenoh_connector.py --port 30555 --connect tcp/10.0.2.2:7447
```

Wait for `Subscribed to Kuksa Databroker`.

**Terminal 3 (inside Leda): mock sensor.**

```bash
ssh -p 2222 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@127.0.0.1
cd /data/sdv-mvp && /data/sdv-venv/bin/python mock_tire_pressure.py --port 30555
```

About once a second, the sensor prints the four values, the connector prints `sent {...}`, and
terminal 1 shows the message (or `-> cloud: sent` with the bridge).

To check a value directly in Kuksa (inside Leda):

```bash
kuksa-client --port 30555 --protocol grpc --insecure
```

then `getValue Vehicle.Chassis.Axle.Row1.Wheel.Left.Tire.Pressure` (Row1 = front, Row2 = rear). Type `quit` to exit.

## Testing without Leda

```bash
docker compose up -d
python watch_signal.py
python mock_tire_pressure.py
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `Failed to get "write" lock` when starting Leda | Leda is already running in another window |
| `ssh: ... Connection refused` | You ran `ssh` inside Leda; run it from your computer |
| Receiver shows nothing | Start the receiver before the connector, and check the connector printed `Subscribed...` |
| `kanto-cm list` / `sdv-health` shows failures right after login | Leda is still starting; wait a minute |
| `sdv-health` shows Cloud Connector FAILED | Expected: that is Leda's Azure connector, which we don't use |
| Bridge shows `FAILED (HTTP 401)` | Missing or wrong API key: set `SDV_API_KEY` again |
| Leda freezes at boot | Its files are in a cloud-synced folder (iCloud/OneDrive); move them to a normal folder |
