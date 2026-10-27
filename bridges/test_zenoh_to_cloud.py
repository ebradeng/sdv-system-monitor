from zenoh_to_cloud import make_request


def test_request_is_a_json_post_with_api_key():
    request = make_request("https://example.test", "secret", '{"vehicleId": "sdv1"}')
    assert request.get_method() == "POST"
    assert request.data == b'{"vehicleId": "sdv1"}'
    assert request.get_header("Content-type") == "application/json"
    assert request.get_header("X-api-key") == "secret"
