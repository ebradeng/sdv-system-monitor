"""Subscribe to the tire pressure signals in the Kuksa Databroker and print every update.

Used to check the mock feeder works. The Zenoh connector will later do the
same subscription, but forward the values to the cloud instead of printing.

Run:  python watch_signal.py --port 55555
"""
import argparse

from kuksa_client.grpc import VSSClient

from mock_tire_pressure import SIGNALS


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55555)
    parser.add_argument("--signal", nargs="+", default=list(SIGNALS.values()),
                        help="one or more VSS paths (default: all four tires)")
    args = parser.parse_args()

    with VSSClient(args.host, args.port) as client:
        print(f"Watching {len(args.signal)} signal(s) on {args.host}:{args.port} (Ctrl+C to stop)")
        try:
            for updates in client.subscribe_current_values(args.signal):
                for path, dp in updates.items():
                    if dp is not None and dp.value is not None:  # skip "no value yet"
                        print(f"{dp.timestamp.astimezone():%H:%M:%S}  {path} = {dp.value}")
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
