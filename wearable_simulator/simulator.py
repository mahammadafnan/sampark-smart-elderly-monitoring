import argparse
import random
import time
from datetime import date

import requests


BACKEND_URL = "http://127.0.0.1:5000"


class WatchState:
    def __init__(self):
        self.current_date = date.today()
        self.steps = 0
        self.rest_cycles_remaining = 0

    def next_steps(self, mode):
        today = date.today()
        if today != self.current_date:
            self.current_date = today
            self.steps = 0
            self.rest_cycles_remaining = 0

        if self.rest_cycles_remaining > 0:
            self.rest_cycles_remaining -= 1
            return self.steps

        if random.random() < 0.28:
            self.rest_cycles_remaining = random.randint(2, 8)
            return self.steps

        if mode == "warning":
            increment = random.choice([0, random.randint(5, 45)])
        else:
            increment = random.randint(20, 220)

        self.steps += increment
        return self.steps


def normal_watch_data(steps=None):
    return {
        "heart_rate": random.randint(65, 95),
        "spo2": random.randint(96, 100),
        "steps": steps if steps is not None else random.randint(2500, 8000),
    }


def warning_watch_data(steps=None):
    return {
        "heart_rate": random.choice([random.randint(45, 54), random.randint(111, 125)]),
        "spo2": random.randint(90, 94),
        "steps": steps if steps is not None else random.randint(200, 1200),
    }


def random_watch_data(steps=None):
    if random.random() < 0.75:
        return normal_watch_data(steps)
    return warning_watch_data(steps)


def send_watch_data(data):
    response = requests.post(f"{BACKEND_URL}/health-data", json=data, timeout=10)
    response.raise_for_status()
    return response.json()


def print_result(record):
    print(
        f"Saved record #{record['id']} | "
        f"HR: {record['heart_rate']} | "
        f"SpO2: {record['spo2']} | "
        f"Steps: {record['steps']} | "
        f"Sleep: {record['sleep_hours']} | "
        f"Risk: {record['risk']}"
    )
    if record["reasons"]:
        print(f"Reasons: {', '.join(record['reasons'])}")
    print()


def get_watch_data(mode, steps=None):
    if mode == "normal":
        return normal_watch_data(steps)
    if mode == "warning":
        return warning_watch_data(steps)
    return random_watch_data(steps)


def run_once(mode):
    data = get_watch_data(mode)
    record = send_watch_data(data)
    print_result(record)


def run_live(mode, interval):
    watch_state = WatchState()
    print("Wearable simulator is running. Press Ctrl+C to stop.")
    while True:
        steps = watch_state.next_steps(mode)
        data = get_watch_data(mode, steps)
        record = send_watch_data(data)
        print_result(record)
        time.sleep(interval)


def parse_args():
    parser = argparse.ArgumentParser(description="Simulate Mi Band / Google Fit data for SAMPARK.")
    parser.add_argument(
        "--mode",
        choices=["normal", "warning", "random"],
        default="random",
        help="Type of watch data to send.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Keep sending data repeatedly.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="Seconds between records in live mode.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        if args.live:
            run_live(args.mode, args.interval)
        else:
            run_once(args.mode)
    except requests.exceptions.ConnectionError:
        print("Backend is not running. Start Flask with 'python app.py' first.")
    except KeyboardInterrupt:
        print("\nWearable simulator stopped.")


if __name__ == "__main__":
    main()
