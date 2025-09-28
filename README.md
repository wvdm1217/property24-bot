# Property 24 Notification Bot

The bot needs to scan Property 24 and notify me whenever a new property has been added using Telegram.

## Setup


### Telegram Bot

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


### Environment settings
Copy `.env.example` to `.env` and fill in your credentials. The application now uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load configuration, so values can come from the environment or the `.env` file.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `TELEGRAM_TOKEN` | ✅ | – | Bot token obtained from [BotFather](https://core.telegram.org/bots#botfather). |
| `TELEGRAM_CHAT_ID` | ✅ | – | Numeric chat ID that should receive notifications. |
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
docker run --env-file .env property24
```