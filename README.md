# Property 24 Notification Bot

The bot needs to scan Property 24 and notify me whenever a new property has been added using Telegram.

## Setup


### Telegram Bot

You will need to create a Telegram bot and find the chat ID of the chat between yourself. 

### Environment settings
Create a `.env` file with the following contents.

```text
TELEGRAM_TOKEN=123456789:ABCDE...
TELEGRAM_CHAT_ID=1234567890
```

## Build

```bash
docker build -t property24 .
```

## Running 



```bash

```