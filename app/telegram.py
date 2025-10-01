import json
import logging

import requests

logger = logging.getLogger(__name__)


def send_message(token: str, chat_id: str, text: str) -> None:
    """Send a message via the Telegram Bot API."""

    logger.info("Sending message to chat_id %s: %s", chat_id, text)
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    logger.debug("Response: %s %s", response.status_code, response.text)


if __name__ == "__main__":
    from app.config import MonitorSettings
    from app.logger import configure_logging

    configure_logging("INFO")
    settings = MonitorSettings()

    send_message(
        token=settings.token,
        chat_id=settings.chat_id,
        text="Hello, World!",
    )
