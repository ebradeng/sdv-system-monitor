import datetime

from mock_tire_pressure import SIGNALS
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
