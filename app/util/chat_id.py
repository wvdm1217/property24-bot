"""Fetch and display Telegram chat IDs from getUpdates."""

from __future__ import annotations

import json
import sys
from collections import OrderedDict
from typing import Any, Iterable, Mapping
from urllib import error, request

from pydantic import ValidationError

from app.config import TelegramSettings

API_URL = "https://api.telegram.org/bot{token}/getUpdates"


def _extract_chat_records(updates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Collect chat metadata from Telegram updates.

    Telegram sends various update types. We check common containers that expose a
    ``chat`` payload and deduplicate the results while preserving order.
    """

    chats: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
    for update in updates:
        for key in ("message", "edited_message", "channel_post", "my_chat_member"):
            payload = update.get(key)
            if isinstance(payload, Mapping):
                chat = payload.get("chat")
                if isinstance(chat, Mapping):
                    chat_id = chat.get("id")
                    if chat_id is not None and chat_id not in chats:
                        chats[chat_id] = {
                            "id": chat_id,
                            "type": chat.get("type"),
                            "title": chat.get("title"),
                            "username": chat.get("username"),
                            "first_name": chat.get("first_name"),
                            "last_name": chat.get("last_name"),
                        }
        # Handle inline query style updates
        if isinstance(update.get("callback_query"), Mapping):
            chat = update["callback_query"].get("message", {}).get("chat", {})
            chat_id = chat.get("id")
            if chat_id is not None and chat_id not in chats:
                chats[chat_id] = {
                    "id": chat_id,
                    "type": chat.get("type"),
                    "title": chat.get("title"),
                    "username": chat.get("username"),
                    "first_name": chat.get("first_name"),
                    "last_name": chat.get("last_name"),
                }
    return list(chats.values())


def main() -> int:
    try:
        settings = TelegramSettings()
    except ValidationError as exc:
        print("Configuration error:", file=sys.stderr)
        for error_details in exc.errors():
            location = " -> ".join(str(part) for part in error_details.get("loc", ()))
            message = error_details.get("msg", "Invalid value")
            print(f" - {location or 'settings'}: {message}", file=sys.stderr)
        return 1

    url = API_URL.format(token=settings.token)
    try:
        with request.urlopen(url, timeout=10) as response:
            data = json.load(response)
    except error.URLError as exc:
        print(f"Failed to reach Telegram API: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, Mapping) or not data.get("ok"):
        print("Unexpected response from Telegram API:", file=sys.stderr)
        print(json.dumps(data, indent=2), file=sys.stderr)
        return 1

    updates = data.get("result", [])
    if not updates:
        print("No updates found. Send a message to your bot and rerun this script.")
        return 0

    chats = _extract_chat_records(updates)
    if not chats:
        print("No chat information found in updates. Try sending a new message.")
        return 0

    print("Discovered chat IDs:\n")
    for chat in chats:
        label_parts = [
            f"id={chat['id']}",
            f"type={chat.get('type') or 'unknown'}",
        ]
        display_name = chat.get("title") or chat.get("username")
        if not display_name:
            names = [
                name
                for name in (chat.get("first_name"), chat.get("last_name"))
                if name
            ]
            if names:
                display_name = " ".join(names)
        if display_name:
            label_parts.append(f"name={display_name}")

        print(" - " + ", ".join(label_parts))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
