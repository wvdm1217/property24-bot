"""Property24 monitoring bot implemented in Python."""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Mapping

import requests
from pydantic import ValidationError

from app.config import MonitorSettings
from app.logger import configure_logging
from app.ntfy import send_message as send_ntfy_message
from app.property24 import ListingTracker, fetch_listing_urls
from app.state import DuckDBStateStore
from app.telegram import send_message as send_telegram_message

PROPERTY_COUNTER_URL = "https://www.property24.com/search/counter"
TELEGRAM_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"

logger = logging.getLogger(__name__)


def send_notification(settings: MonitorSettings, message: str) -> None:
    """Send a notification using the configured notification method."""
    method = settings.notification_method.lower()

    if method == "ntfy":
        send_ntfy_message(
            server=settings.ntfy_server,
            topic=settings.ntfy_topic or "",
            message=message,
        )
    elif method == "telegram":
        send_telegram_message(
            token=settings.telegram_token or "",
            chat_id=settings.telegram_chat_id or "",
            text=message,
        )
    else:
        logger.error("Unknown notification method: %s", method)


def load_search_payload(path: Path) -> Mapping[str, object]:
    """Load the search payload from disk."""

    try:
        with path.open(encoding="utf-8") as payload_file:
            payload = json.load(payload_file)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Payload file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON content in payload file: {path}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Payload file must contain a JSON object")

    return payload


def fetch_property_count(
    payload: Mapping[str, object],
) -> int:
    """Call the Property24 counter endpoint and return the current listing count."""

    body = json.dumps(payload).encode("utf-8")
    req = requests.post(
        PROPERTY_COUNTER_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        timeout=10,
    )

    try:
        data = req.json()
    except requests.RequestException as exc:
        raise RuntimeError("Failed to fetch property count") from exc

    try:
        return int(data["count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Property count missing in response") from exc


def monitor_property_count(
    settings: MonitorSettings,
    payload: Mapping[str, object],
) -> None:
    """Monitor the property count and notify when new listings appear."""

    state_store = DuckDBStateStore(path=settings.state_file)
    state_store.ensure_file()

    previous_count = state_store.get_property_count()
    tracker = ListingTracker(state_store=state_store)
    logger.info(
        "Starting monitor for %s (previous count: %s)",
        settings.location_name,
        previous_count,
    )

    try:
        while True:
            try:
                current_count = fetch_property_count(payload)
            except RuntimeError as exc:
                logger.error("%s", exc)
                time.sleep(settings.poll_interval)
                continue

            if current_count != previous_count:
                logger.info("Property count changed: %s", current_count)
                state_store.set_property_count(current_count)

                listing_urls: list[str] = []
                newly_added_urls: list[str] = []
                try:
                    listing_urls = fetch_listing_urls(payload, count=current_count)
                except RuntimeError as exc:
                    logger.error("Failed to fetch listing URLs: %s", exc)
                else:
                    newly_added_urls = tracker.record(listing_urls)
                    logger.debug(
                        "Recorded %s listings (%s new)",
                        len(listing_urls),
                        len(newly_added_urls),
                    )

                if current_count > previous_count:
                    message_lines = [
                        (
                            f"New property added in {settings.location_name}. "
                            f"Count: {current_count}"
                        )
                    ]

                    if newly_added_urls:
                        max_display = 10
                        display_urls = newly_added_urls[:max_display]
                        message_lines.append("New listings:")
                        message_lines.extend(display_urls)
                        remaining = len(newly_added_urls) - len(display_urls)
                        if remaining > 0:
                            message_lines.append(f"...and {remaining} more")

                    message = "\n".join(message_lines)
                    try:
                        send_notification(settings, message)
                        logger.info(
                            "Notification sent via %s", settings.notification_method
                        )
                    except Exception as e:
                        logger.error("Failed to send notification: %s", e)

                previous_count = current_count
            else:
                logger.debug("No change in property count: %s", current_count)

            if settings.run_once:
                break

            time.sleep(settings.poll_interval)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")


def main() -> None:
    try:
        settings = MonitorSettings()
    except ValidationError as exc:
        print("Configuration error:", file=sys.stderr)
        for error in exc.errors():
            location = " -> ".join(str(part) for part in error.get("loc", ()))
            message = error.get("msg", "Invalid value")
            print(f" - {location or 'settings'}: {message}", file=sys.stderr)
        raise SystemExit(1) from exc

    configure_logging(settings.log_level)

    try:
        payload = load_search_payload(settings.payload_file)
    except RuntimeError as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from exc

    monitor_property_count(settings, payload)


if __name__ == "__main__":
    main()
