import json

import requests


def send_message(token: str, chat_id: str, text: str) -> bool:
    """Send a message via the Telegram Bot API."""

    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    data = json.dumps(payload).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, data=data, headers={"Content-Type": "application/json"})

    print(f"Sending message to chat_id {chat_id}: {text}")
    print(response.status_code, response.text)

if __name__ == "__main__":

    from app.config import MonitorSettings
    settings = MonitorSettings()

    send_message(
        token=settings.token,
        chat_id=settings.chat_id,
        text="Hello, World!",
    )