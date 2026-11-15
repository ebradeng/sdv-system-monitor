"""Mock tire pressure sensor.

Sends a fake tire pressure reading for all four tires to the Kuksa Databroker
once a second.

Usage:  python mock_tire_pressure.py --port 30555
"""
import argparse
import random
import time

from kuksa_client.grpc import Datapoint, VSSClient

SIGNALS = {
    "front left": "Vehicle.Chassis.Axle.Row1.Wheel.Left.Tire.Pressure",
    "front right": "Vehicle.Chassis.Axle.Row1.Wheel.Right.Tire.Pressure",
    "rear left": "Vehicle.Chassis.Axle.Row2.Wheel.Left.Tire.Pressure",
    "rear right": "Vehicle.Chassis.Axle.Row2.Wheel.Right.Tire.Pressure",
}

NORMAL_KPA = 230  # normal car tire pressure


class TirePressureMock:
    """Produces tire pressure values that drift a little around NORMAL_KPA."""

    def __init__(self, seed=None):
        self.value = NORMAL_KPA
        self.random = random.Random(seed)

    def next_value(self):
        self.value += self.random.uniform(-2, 2)
        self.value += (NORMAL_KPA - self.value) * 0.05  # drift back toward normal
        return round(self.value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=55555)
    args = parser.parse_args()

    tires = {name: TirePressureMock() for name in SIGNALS}

    while True:
        try:
            with VSSClient(args.host, args.port) as client:
                print(f"Connected to Kuksa at {args.host}:{args.port}")
                while True:
                    values = {name: tire.next_value() for name, tire in tires.items()}
                    client.set_current_values(
                        {SIGNALS[name]: Datapoint(value) for name, value in values.items()})
                    print("Tire pressure (kPa):", values)
                    time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as error:
            print(f"Can't reach Kuksa ({error}), retrying in 3 seconds")
            time.sleep(3)


if __name__ == "__main__":
    main()
