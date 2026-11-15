# System design

This document describes the intended design, not a claim that every component
is implemented. See the [architecture diagram](architecture.svg).

## Scope and deployment

The immediate milestone is **one** vehicle using the official x86_64 Leda
Docker quickstart image, sending simulated tire pressure to the existing
Google Cloud Run HTTP endpoint. The intended system expands this to four
vehicles and adds CARLA data.

On the Windows 11 desktop, Docker Compose will start one quickstart container
per vehicle. Each outer container runs QEMU, which runs a Leda OS instance.
Each Leda instance has its own Kuksa Databroker and Zenoh instance. Startup
should automatically create the Zenoh containers inside Leda using Kanto.
The Compose services and their vehicle identities must be distinct.

The same logical vehicle ID must identify a vehicle across the outer container,
Leda, the telemetry payload, and the mapping from CARLA through the bridge.
The mechanism for configuring and propagating that ID, and the mapping to
CARLA's own identifiers, are still open. Each Kuksa instance must be reachable
from the host through its own unambiguous port mapping; the ports and network
configuration are still open.

## Vehicle data sources and Kuksa

- **Python mock sensors:** Produce internal vehicle signals and write them to
  the vehicle's Kuksa Databroker. The first signal is tire pressure; battery
  and cabin temperature are possible future signals. For the current test the
  tire-pressure script runs on the Windows host, using its vehicle's exposed
  Kuksa port.
- **CARLA and eCAL + iceoryx bridge (planned):** One CARLA server simulates
  four vehicles and their external state, such as speed, acceleration and
  position. A bridge outside the Leda Docker containers reads the simulated
  data and routes it to the matching vehicle's exposed Kuksa port. Neither the
  server nor bridge is implemented yet. Signal selection, conversion, routing
  details and the bridge's internal protocol are open.
- **Kuksa Databroker:** Holds the individual vehicle's VSS signals. It accepts
  updates from the mock sensors and, later, the CARLA bridge, and supplies
  updates to the vehicle's Zenoh connector.

The current tire-pressure mock writes once per second to these VSS paths:

| Wheel | VSS path | Unit |
|---|---|---|
| Front left | `Vehicle.Chassis.Axle.Row1.Wheel.Left.Tire.Pressure` | kPa |
| Front right | `Vehicle.Chassis.Axle.Row1.Wheel.Right.Tire.Pressure` | kPa |
| Rear left | `Vehicle.Chassis.Axle.Row2.Wheel.Left.Tire.Pressure` | kPa |
| Rear right | `Vehicle.Chassis.Axle.Row2.Wheel.Right.Tire.Pressure` | kPa |

## Kuksa to Zenoh to Cloud Run

The vehicle's connector subscribes to Kuksa and publishes JSON over Zenoh.
For tire pressure, the existing key is `sdv/<vehicle-id>/tire_pressure`. The
current payload shape is:

```json
{
  "vehicleId": "sdv1",
  "timestamp": "2026-01-01T00:00:00+00:00",
  "tirePressure_kPa": {
    "frontLeft": 230,
    "frontRight": 229,
    "rearLeft": 231,
    "rearRight": 228
  }
}
```

The timestamp is a UTC ISO 8601 string. The connector can publish partial
updates by default; the quickstart tire-pressure deployment uses
`--require-complete`, waiting until all four values have arrived. New signals
and their message contracts are not yet decided.

For this milestone, the Python connector replaces the KUKSA–Zenoh provider in
the tire-pressure path. The provider publishes individual values on VSS-based
Zenoh keys, rather than assembling the four-wheel cloud JSON. It may be
revisited for other signals later.

Cloud Run accepts **HTTP POST**, not a direct Zenoh connection. The intended
path is for each vehicle to run a Python bridge that subscribes to its Zenoh
telemetry and posts the JSON to the existing endpoint. Ideally the bridge runs
inside that vehicle's Leda instance. The local quickstart test instead posts to
a mock HTTP receiver in the outer Docker container; it must not send cloud
traffic until that test is complete and cloud testing is authorized. The
existing bridge uses `Content-Type: application/json` and an `X-API-Key`
header; credentials must be supplied at runtime, not embedded in the design
or source code.

## Cloud to Splunk

The existing downstream path is Cloud Run HTTP receiver → Google Cloud
Pub/Sub → a Pub/Sub-to-Splunk bridge → Splunk HTTP Event Collector → Splunk
dashboard. Splunk and its bridge run on a different machine from the Windows
simulation host. The current security and reliability approach is sufficient
for this milestone; any changes are future decisions.

## Current implementation versus target

The earlier working tire-pressure path used a QEMU Leda image. The existing
[Leda instructions](leda/README.md) describe a Zenoh-to-HTTP bridge running
on the host, not inside Leda. The quickstart deployment targets automated Kanto
startup of the router, Python connector, and in-Leda HTTP bridge; real Cloud
Run delivery and four-vehicle orchestration remain to be verified. CARLA and its bridge are
future work. The separate [local Kuksa Compose file](leda/docker-compose.yml)
is a development aid, not the Leda quickstart deployment.

For the first milestone, verify end to end that a single quickstart container
boots Leda, starts Zenoh through Kanto, writes mock tire pressures to Kuksa,
publishes them to Zenoh, and posts a correctly identified JSON payload to the
existing Cloud Run endpoint using the intended in-Leda bridge.

## Implemented quickstart tire-pressure pipeline

- Docker Compose starts one x86_64 Leda quickstart container on Windows. Its
  wrapper starts a local HTTP receiver and the bootstrap script alongside the
  original QEMU entrypoint.
- Bootstrap waits for Leda and Kanto, imports the Zenoh and Python telemetry
  image archives, and creates or starts three Kanto containers: `zenoh-router`,
  `sdv-tire-connector`, and `sdv-http-bridge`. It reuses matching existing
  containers and reports configuration mismatches instead of replacing them.
- A separately started Windows mock sensor writes the four tire pressures to
  Kuksa through host port `55555`. The Python connector reads Kuksa inside
  Leda, waits for all four values, and publishes the combined JSON to
  `sdv/sdv1/tire_pressure` through Zenoh. The KUKSA–Zenoh provider is not used
  for this tire-pressure path.
- The in-Leda HTTP bridge subscribes to Zenoh and posts the JSON to the local
  receiver in the outer Docker container. The bootstrap currently configures a
  local test key and endpoint, not Cloud Run.

The local end-to-end path was verified with fresh Windows-generated readings
and HTTP 200 responses. Cloud Run delivery from the quickstart deployment,
four-vehicle orchestration, and the CARLA bridge remain to be verified or
implemented. Build, startup, and persistence instructions are in the
[quickstart guide](leda-quickstart/README.md).
