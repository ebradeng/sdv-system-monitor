"""Zenoh to cloud bridge.

Receives the car's messages over Zenoh and sends each one to the
Google Cloud HTTP receiver (which publishes it to Pub/Sub -> Splunk).

The API key is read from the SDV_API_KEY environment variable:
    export SDV_API_KEY='...'

Usage:  python zenoh_to_cloud.py
"""
import argparse
import json
import os
import queue
import threading
import urllib.error
import urllib.request

import zenoh

CLOUD_URL = "https://sdv-http-receiver-418057313473.northamerica-northeast2.run.app"


def open_zenoh(listen):
    """Open a Zenoh session that accepts the connector's connection on `listen`."""
    conf = zenoh.Config()
    conf.insert_json5("listen/endpoints", json.dumps([listen]))
    return zenoh.open(conf)


def make_request(url, api_key, body):
    """Build the HTTP POST for one JSON message."""
    return urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )


def send(url, api_key, body):
    """POST one message. Returns the HTTP status code (or None if unreachable)."""
    try:
        with urllib.request.urlopen(make_request(url, api_key, body), timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except urllib.error.URLError as error:
        print(f"Can't reach the cloud: {error.reason}")
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=CLOUD_URL)
    parser.add_argument("--listen", default="tcp/127.0.0.1:7447",
                        help="where the Zenoh connector in Leda connects to")
    args = parser.parse_args()

    api_key = os.environ.get("SDV_API_KEY")
    if not api_key:
        raise SystemExit("Set the API key first:  export SDV_API_KEY='...'")

    # Zenoh delivers messages on its own thread; a queue hands them to the sender.
    messages = queue.Queue()
    session = open_zenoh(args.listen)
    session.declare_subscriber(
        "sdv/**", lambda sample: messages.put((str(sample.key_expr), sample.payload.to_string())))
    print(f"Forwarding Zenoh 'sdv/**' to {args.url} (Ctrl+C to stop)", flush=True)

    def sender():
        while True:
            key, body = messages.get()
            status = send(args.url, api_key, body)
            result = "sent" if status == 200 else f"FAILED (HTTP {status})"
            print(f"{key} -> cloud: {result}", flush=True)

    threading.Thread(target=sender, daemon=True).start()
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        session.close()


if __name__ == "__main__":
    main()
