"""Listen for SDV messages on Zenoh and print them.

Stands in for the cloud side while testing: it receives exactly what
Ethan's Google Cloud service will receive.

Run:  python zenoh_listener.py
      python zenoh_listener.py --connect tcp/<cloud-ip>:7447
      python zenoh_listener.py --listen tcp/0.0.0.0:7447   (connector inside Leda)
"""
import argparse
import threading

from zenoh_connector import open_zenoh


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key", default="sdv/**", help="Zenoh key expression to listen on")
    parser.add_argument("--connect", default=None, help="Zenoh endpoint, e.g. tcp/34.1.2.3:7447")
    parser.add_argument("--listen", default=None,
                        help="accept connections, e.g. tcp/0.0.0.0:7447 for a connector inside Leda")
    args = parser.parse_args()

    session = open_zenoh(args.connect, args.listen)
    session.declare_subscriber(
        args.key, lambda sample: print(f"{sample.key_expr}  {sample.payload.to_string()}", flush=True))
    print(f"Listening on '{args.key}' (Ctrl+C to stop)", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        session.close()


if __name__ == "__main__":
    main()
