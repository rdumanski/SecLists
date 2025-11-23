"""
Poll the CME FedWatch Tool and send WhatsApp alerts when the Ease
probability changes.

Environment variables:
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_WHATSAPP_FROM (e.g. "whatsapp:+12345678900")
- TWILIO_WHATSAPP_TO (e.g. "whatsapp:+10987654321")

The script uses a simple polling loop; use --run-once for local tests.
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any, Optional

DEFAULT_FEED_URL = "https://www.cmegroup.com/CmeWS/mvc/InterestRates/FedWatchToolData"
DEFAULT_POLL_SECONDS = 15 * 60


def fetch_json(url: str, timeout: float = 10.0) -> Any:
    """Retrieve JSON content from *url* using the standard library."""
    request = urllib.request.Request(url, headers={"User-Agent": "SecLists FedWatch Notifier"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # type: ignore[call-arg]
        charset = response.headers.get_content_charset() or "utf-8"
        raw_body = response.read().decode(charset)
    return json.loads(raw_body)


def _extract_numeric(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().rstrip("%")
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def find_ease_probability(payload: Any) -> Optional[float]:
    """Search any nested JSON payload for the first value labeled "ease"."""
    stack = [payload]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, value in current.items():
                if isinstance(key, str) and "ease" in key.lower():
                    numeric = _extract_numeric(value)
                    if numeric is not None:
                        return numeric
                stack.append(value)
        elif isinstance(current, list):
            stack.extend(current)
    return None


def build_change_message(url: str, previous: Optional[float], current: float) -> str:
    if previous is None:
        return f"FedWatch Ease probability is {current}% (monitoring started). Source: {url}"
    return (
        "FedWatch Ease probability changed "
        f"from {previous}% to {current}%. Source: {url}"
    )


def send_whatsapp_message(body: str) -> None:
    from twilio.rest import Client
    import os

    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    from_number = os.environ["TWILIO_WHATSAPP_FROM"]
    to_number = os.environ["TWILIO_WHATSAPP_TO"]

    client = Client(account_sid, auth_token)
    client.messages.create(body=body, from_=from_number, to=to_number)


def monitor(url: str, poll_seconds: int, notify_on_start: bool, run_once: bool) -> None:
    previous: Optional[float] = None

    while True:
        try:
            payload = fetch_json(url)
            current = find_ease_probability(payload)
            if current is None:
                print("Could not locate an Ease probability in the feed.")
            else:
                should_alert = notify_on_start and previous is None
                if previous is not None and current != previous:
                    should_alert = True
                if should_alert:
                    message = build_change_message(url, previous, current)
                    send_whatsapp_message(message)
                    print(f"Alert sent: {message}")
                previous = current
        except (urllib.error.URLError, json.JSONDecodeError) as error:
            print(f"Failed to refresh feed: {error}")
        if run_once:
            return
        time.sleep(poll_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor CME FedWatch Ease probability via WhatsApp.")
    parser.add_argument("--url", default=DEFAULT_FEED_URL, help="JSON feed URL for the FedWatch Tool")
    parser.add_argument(
        "--poll-seconds", type=int, default=DEFAULT_POLL_SECONDS, help="Polling interval in seconds"
    )
    parser.add_argument(
        "--notify-on-start",
        action="store_true",
        help="Send a WhatsApp message with the initial Ease probability",
    )
    parser.add_argument(
        "--run-once", action="store_true", help="Fetch the feed a single time (useful for smoke tests)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    options = parse_args()
    monitor(
        url=options.url,
        poll_seconds=options.poll_seconds,
        notify_on_start=options.notify_on_start,
        run_once=options.run_once,
    )
