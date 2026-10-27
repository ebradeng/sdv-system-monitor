"""Zenoh connector for the SDV System Monitor MVP.

Subscribes to the four tire pressure signals in the Kuksa Databroker and
publishes every update over Eclipse Zenoh, so the cloud side can receive it.

Zenoh key:  sdv/<vehicle-id>/tire_pressure
Payload:    {"vehicleId": "sdv1", "timestamp": "...",
             "tirePressure_kPa": {"frontLeft": 230, "frontRight": 229,
                                  "rearLeft": 231, "rearRight": 228}}

Run:  python zenoh_connector.py --port 30555
      python zenoh_connector.py --port 30555 --connect tcp/<cloud-ip>:7447
"""
import argparse
import datetime
import json
import logging
import time

import zenoh
from kuksa_client.grpc import VSSClient

from mock_tire_pressure import SIGNALS

# VSS path -> JSON field name
FIELDS = {
    SIGNALS["front left"]: "frontLeft",
    SIGNALS["front right"]: "frontRight",
    SIGNALS["rear left"]: "rearLeft",
    SIGNALS["rear right"]: "rearRight",
}

log = logging.getLogger("zenoh-connector")


def build_message(vehicle_id, latest, now=None):
    """Turn the latest tire values {vss_path: kPa} into the JSON message sent over Zenoh."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return {
        "vehicleId": vehicle_id,
        "timestamp": now.isoformat(),
        "tirePressure_kPa": {name: latest[path] for path, name in FIELDS.items() if path in latest},
    }


def open_zenoh(connect=None, listen=None):
    conf = zenoh.Config()
    if connect:  # e.g. a Zenoh router on Google Cloud; otherwise peers find each other locally
        conf.insert_json5("connect/endpoints", json.dumps([connect]))
    if listen:  # accept incoming connections, e.g. from a connector running inside Leda
        conf.insert_json5("listen/endpoints", json.dumps([listen]))
    return zenoh.open(conf)


def run(host, port, vehicle_id, connect):
    key = f"sdv/{vehicle_id}/tire_pressure"
    session = open_zenoh(connect)
    publisher = session.declare_publisher(key)
    log.info("Zenoh ready, publishing on '%s'%s", key, f" via {connect}" if connect else "")
    latest = {}
    try:
        while True:
            try:
                with VSSClient(host, port) as client:
                    log.info("Subscribed to Kuksa Databroker at %s:%s", host, port)
                    for updates in client.subscribe_current_values(list(FIELDS)):
                        for path, dp in updates.items():
                            if dp is not None and dp.value is not None:
                                latest[path] = dp.value
                        if latest:
                            msg = build_message(vehicle_id, latest)
                            publisher.put(json.dumps(msg))
                            log.info("sent %s", msg["tirePressure_kPa"])
            except KeyboardInterrupt:
                raise
            except Exception as exc:  # databroker not up yet or connection dropped
                log.warning("Databroker unavailable (%s); retrying in 3 s", exc)
                time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1", help="Kuksa Databroker host")
    parser.add_argument("--port", type=int, default=55555,
                        help="Kuksa Databroker port: 55555 local, 30555 for Leda")
    parser.add_argument("--vehicle-id", default="sdv1")
    parser.add_argument("--connect", default=None,
                        help="Zenoh endpoint to connect to, e.g. tcp/34.1.2.3:7447 (optional)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    run(args.host, args.port, args.vehicle_id, args.connect)


if __name__ == "__main__":
    main()
