# Property 24 Notification Bot

The bot needs to scan Property 24 and notify me whenever a new property has been added using ntfy or Telegram.

## Setup

### Notification Methods

The bot supports two notification methods:
- **ntfy** (default): A simple HTTP-based pub-sub notification service
- **Telegram**: Bot-based messaging through the Telegram Bot API

Choose your preferred method by setting `P24_NOTIFICATION_METHOD` in your `.env` file.

#### Using ntfy (Default)

[ntfy](https://ntfy.sh) is a simple notification service that doesn't require registration.

1. Choose a unique topic name (e.g., `property24-yourname-12345`)
2. Subscribe to your topic using the ntfy app or web interface at https://ntfy.sh
3. Set the environment variables:
```bash
P24_NOTIFICATION_METHOD=ntfy  # Optional, this is the default
NTFY_TOPIC=your-unique-topic-name
NTFY_SERVER=https://ntfy.sh  # Optional, this is the default
```

#### Using Telegram

You will need to create a Telegram bot and find the chat ID of the chat between yourself. 

#### Chat ID

1. Ping the bot with a message.
2. Add the `TELEGRAM_TOKEN` to your `.env` and run,
```bash
uv run app/util/chat_id.py
```
3. From the response of the output set the `TELEGRAM_CHAT_ID`,
```bash
$ uv run app/util/chat_id.py
Discovered chat IDs:

 - id=1234567890, type=private, name=Werner van der Merwe
```

4. Set the environment variables:
```bash
P24_NOTIFICATION_METHOD=telegram
TELEGRAM_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```


### Environment settings
Copy `.env.example` to `.env` and fill in your credentials. The application now uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load configuration, so values can come from the environment or the `.env` file.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `P24_NOTIFICATION_METHOD` | ❌ | `ntfy` | Notification method to use: `ntfy` or `telegram`. |
| `NTFY_SERVER` | ❌ | `https://ntfy.sh` | ntfy server URL (only needed for ntfy method). |
| `NTFY_TOPIC` | ✅ (for ntfy) | – | ntfy topic name (required when using ntfy method). |
| `TELEGRAM_TOKEN` | ✅ (for telegram) | – | Bot token obtained from [BotFather](https://core.telegram.org/bots#botfather) (required when using telegram method). |
| `TELEGRAM_CHAT_ID` | ✅ (for telegram) | – | Numeric chat ID that should receive notifications (required when using telegram method). |
| `P24_COUNT_FILE` | ❌ | `count.txt` | File used to persist the previous listing count. |
| `P24_POLL_INTERVAL` | ❌ | `60` | Polling interval in seconds (clamped to a minimum of 10). |
| `P24_LOCATION_NAME` | ❌ | `Stellenbosch` | Location label included in alert messages. |
| `P24_RUN_ONCE` | ❌ | `false` | When `true`, execute a single poll then exit (useful for smoke tests). |
| `P24_LOG_LEVEL` | ❌ | `INFO` | Logging verbosity (`DEBUG`, `INFO`, etc.). |

## Build

```bash
docker build -t property24 .
```

## Running

```bash
uv run python -m app.main
```

or 

```bash
docker run --env-file .env -v "$(pwd)/data/payload.json:/app/data/payload.json:ro" property24
```