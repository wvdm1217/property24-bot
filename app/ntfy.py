import requests

from app.config import NtfySettings


def send_message(server: str, topic: str, message: str) -> None:
    """Send a message via the ntfy service."""

    url = f"{server}/{topic}"
    response = requests.post(url, data=message.encode("utf-8"))

    print(f"Sending message to topic {topic}: {message}")
    print(response.status_code, response.text)


if __name__ == "__main__":
    settings = NtfySettings()
    send_message(settings.server, settings.topic, "Test message from property24-bot")
