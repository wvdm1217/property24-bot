import logging

import requests

logger = logging.getLogger(__name__)


def send_message(server: str, topic: str, message: str) -> None:
    """Send a message via the ntfy service."""

    url = f"{server}/{topic}"
    logger.info("Sending message to %s: %s", url, message)
    response = requests.post(url, data=message.encode("utf-8"))
    logger.info("Response status code: %s", response.status_code)


def main() -> None:
    from app.config import NtfySettings
    from app.logger import configure_logging

    configure_logging("INFO")
    settings = NtfySettings()

    send_message(settings.server, settings.topic, "Test message from property24-bot")


if __name__ == "__main__":
    main()
