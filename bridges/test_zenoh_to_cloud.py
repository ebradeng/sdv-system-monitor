import json

import zenoh_to_cloud
from zenoh_to_cloud import make_request


def test_request_is_a_json_post_with_api_key():
    request = make_request("https://example.test", "secret", '{"vehicleId": "sdv1"}')
    assert request.get_method() == "POST"
    assert request.data == b'{"vehicleId": "sdv1"}'
    assert request.get_header("Content-type") == "application/json"
    assert request.get_header("X-api-key") == "secret"


def test_router_connection_uses_client_mode(monkeypatch):
    settings = {}

    class Config:
        def insert_json5(self, key, value):
            settings[key] = json.loads(value)

    monkeypatch.setattr(zenoh_to_cloud.zenoh, "Config", Config)
    monkeypatch.setattr(zenoh_to_cloud.zenoh, "open", lambda config: config)
    zenoh_to_cloud.open_zenoh(connect="tcp/127.0.0.1:7447")
    assert settings == {
        "mode": "client",
        "connect/endpoints": ["tcp/127.0.0.1:7447"],
    }


def test_listen_mode_is_preserved(monkeypatch):
    settings = {}

    class Config:
        def insert_json5(self, key, value):
            settings[key] = json.loads(value)

    monkeypatch.setattr(zenoh_to_cloud.zenoh, "Config", Config)
    monkeypatch.setattr(zenoh_to_cloud.zenoh, "open", lambda config: config)
    zenoh_to_cloud.open_zenoh(listen="tcp/127.0.0.1:7447")
    assert settings == {"listen/endpoints": ["tcp/127.0.0.1:7447"]}
