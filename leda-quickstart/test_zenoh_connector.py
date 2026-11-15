import datetime
import json
from types import SimpleNamespace

from mock_tire_pressure import SIGNALS
import zenoh_connector
from zenoh_connector import build_message


def test_message_has_vehicle_id_time_and_all_four_tires():
    latest = {path: 230 for path in SIGNALS.values()}
    now = datetime.datetime(2026, 10, 16, 15, 0, tzinfo=datetime.timezone.utc)
    msg = build_message("sdv1", latest, now)
    assert msg == {
        "vehicleId": "sdv1",
        "timestamp": "2026-10-16T15:00:00+00:00",
        "tirePressure_kPa": {"frontLeft": 230, "frontRight": 230, "rearLeft": 230, "rearRight": 230},
    }


def test_message_with_only_some_tires_known():
    msg = build_message("sdv2", {SIGNALS["rear right"]: 215})
    assert msg["vehicleId"] == "sdv2"
    assert msg["tirePressure_kPa"] == {"rearRight": 215}


def test_require_complete_waits_for_all_wheels(monkeypatch):
    published = []
    paths = list(SIGNALS.values())

    class Publisher:
        def put(self, payload):
            published.append(json.loads(payload))

    class Session:
        def declare_publisher(self, key):
            assert key == "sdv/sdv1/tire_pressure"
            return Publisher()

        def close(self):
            pass

    class Client:
        def __init__(self, host, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def subscribe_current_values(self, fields):
            yield {paths[0]: SimpleNamespace(value=230)}
            yield {path: SimpleNamespace(value=231) for path in paths[1:]}
            raise KeyboardInterrupt

    monkeypatch.setattr(zenoh_connector, "open_zenoh", lambda connect: Session())
    monkeypatch.setattr(zenoh_connector, "VSSClient", Client)
    zenoh_connector.run("localhost", 30555, "sdv1", None, require_complete=True)
    assert len(published) == 1
    assert published[0]["tirePressure_kPa"] == {
        "frontLeft": 230, "frontRight": 231, "rearLeft": 231, "rearRight": 231
    }
