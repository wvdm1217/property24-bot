"""Property24 monitoring bot implemented in Python."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import IO, Mapping, Optional, Protocol, cast
from urllib import error, request

from pydantic import ValidationError

from app.config import MonitorSettings
from app.logger import configure_logging, get_logger

PROPERTY_COUNTER_URL = "https://www.property24.com/search/counter"
TELEGRAM_SEND_MESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"


logger = get_logger(__name__)


class UrlOpener(Protocol):
    """Protocol describing the signature of urllib opener functions."""

    def __call__(
        self, request: request.Request, timeout: Optional[float] = None
    ) -> IO[bytes]:
        ...


DEFAULT_OPENER = cast(UrlOpener, request.urlopen)


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


def read_previous_count(count_file: Path) -> int:
    """Load the previous count from disk, initialising the file if needed."""

    try:
        content = count_file.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError("empty content")
        return int(content)
    except FileNotFoundError:
        logger.info(
            "Count file %s not found. Initialising with 0.",
            count_file,
        )
    except ValueError:
        logger.warning(
            "Count file %s contained invalid data. Resetting to 0.", count_file
        )

    count_file.write_text("0\n", encoding="utf-8")
    return 0


def write_count(count_file: Path, value: int) -> None:
    """Persist the latest count to disk."""

    count_file.write_text(f"{value}\n", encoding="utf-8")


def fetch_property_count(
    payload: Mapping[str, object],
    opener: UrlOpener = DEFAULT_OPENER,
) -> int:
    """Call the Property24 counter endpoint and return the current listing count."""

    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        PROPERTY_COUNTER_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with opener(req, timeout=20) as response:
            data = json.load(response)
    except error.URLError as exc:
        raise RuntimeError("Failed to fetch property count") from exc

    try:
        return int(data["count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("Property count missing in response") from exc


def send_message(
    token: str,
    chat_id: str,
    text: str,
    *,
    opener: UrlOpener = DEFAULT_OPENER,
) -> bool:
    """Send a Telegram message with the provided bot credentials."""

    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    url = TELEGRAM_SEND_MESSAGE_URL.format(token=token)
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with opener(req, timeout=10) as response:
            response.read()  # Ensure request completes
        return True
    except error.URLError as exc:
        logger.error("Failed to send Telegram message: %s", exc)
        return False


def monitor_property_count(
    settings: MonitorSettings,
    payload: Mapping[str, object],
    opener: UrlOpener = DEFAULT_OPENER,
) -> None:
    """Monitor the property count and notify when new listings appear."""

    previous_count = read_previous_count(settings.count_file)
    logger.info(
        "Starting monitor for %s (previous count: %s)",
        settings.location_name,
        previous_count,
    )

    try:
        while True:
            try:
                current_count = fetch_property_count(payload, opener=opener)
            except RuntimeError as exc:
                logger.error("%s", exc)
                time.sleep(settings.poll_interval)
                continue

            if current_count != previous_count:
                logger.info("Property count changed: %s", current_count)
                write_count(settings.count_file, current_count)

                if current_count > previous_count:
                    message = (
                        f"New property added in {settings.location_name}. "
                        f"Count: {current_count}"
                    )
                    if send_message(
                        settings.token,
                        settings.chat_id,
                        message,
                        opener=opener,
                    ):
                        logger.info("Telegram notification sent")
                else:
                    logger.info(
                        "Property removed in %s. Count: %s",
                        settings.location_name,
                        current_count,
                    )

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
    logger.setLevel(settings.log_level)

    try:
        payload = load_search_payload(settings.payload_file)
    except RuntimeError as exc:
        logger.error("%s", exc)
        raise SystemExit(1) from exc

    monitor_property_count(settings, payload)


if __name__ == "__main__":
    main()
