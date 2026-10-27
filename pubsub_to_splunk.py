
import json
from getpass import getpass

import requests
from google.cloud import pubsub_v1

PROJECT_ID = "sdv-system-monitor"
SUBSCRIPTION_ID = "sdv-telemetry-sub"
SPLUNK_URL = "http://127.0.0.1:8088/services/collector/event"

token = getpass("Enter your Splunk HEC token: ").strip()

headers = {
    "Authorization": f"Splunk {token}"
}


def forward_message(message):
    try:
        try:
            data = json.loads(message.data.decode("utf-8"))

            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object")

        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            print(f"Skipping invalid message: {error}")
            message.ack()
            return

        payload = {
            "index": "sdv",
            "source": "google-cloud-pubsub",
            "sourcetype": "_json",
            "event": data
        }

        response = requests.post(
            SPLUNK_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"Splunk response: {response.status_code} {response.text}")
        response.raise_for_status()

        if response.json().get("code") != 0:
            raise ValueError(response.text)

        message.ack()
        print(f"Sent vehicle {data.get('vehicle_id', 'unknown')} to Splunk")

    except Exception as error:
        print(f"Forwarding failed: {error}")
        message.nack()


def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription = subscriber.subscription_path(
        PROJECT_ID, SUBSCRIPTION_ID
    )

    print("Listening for Google Cloud messages...")

    with subscriber:
        future = subscriber.subscribe(
            subscription,
            callback=forward_message
        )

        try:
            future.result()
        except KeyboardInterrupt:
            future.cancel()
            print("Bridge stopped.")


if __name__ == "__main__":
    main()
