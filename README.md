# Property24 Notification Bot

A Python-based bot that monitors Property24 for new property listings and sends notifications via ntfy or Telegram. The bot uses DuckDB for state persistence and can be deployed on Kubernetes using the included Helm chart.

## Features

- 🏠 **Property Monitoring**: Continuously monitors Property24 for new listings
- 📱 **Multiple Notification Methods**: Support for both ntfy and Telegram notifications
- 💾 **Persistent State**: Uses DuckDB to track seen listings and prevent duplicate notifications
- 🐳 **Docker Support**: Containerized application with optimized build using `uv`
- ☸️ **Kubernetes Ready**: Production-ready Helm chart for easy deployment
- ⚙️ **Configurable**: Flexible configuration via environment variables or Pydantic Settings

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (for local development)
- Docker (for containerized deployment)
- Kubernetes + Helm 3.0+ (for Kubernetes deployment)

## Quick Start

### Local Development

1. Install dependencies using `uv`:
```bash
uv sync
```

2. Create a search payload file (see [Creating the Search Payload](#creating-the-search-payload) section):
```bash
# Install playwright for the utility
uv sync --group web

# Generate payload from a Property24 search URL
uv run app/util/url_to_payload.py "YOUR_PROPERTY24_URL" --output data/payload.json --pretty
```

3. Configure your environment (see [Configuration](#configuration) section below)

4. Run the bot:
```bash
uv run python -m app.main
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t property24-bot:0.1.0 .
```

2. Run the container:
```bash
docker run --env-file .env \
  -v "$(pwd)/data/payload.json:/app/data/payload.json:ro" \
  -v "$(pwd)/data:/app/data" \
  property24-bot:0.1.0
```

### Kubernetes Deployment with Helm

The project includes a production-ready Helm chart for deploying on Kubernetes.

#### Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Docker image pushed to a registry (or available in your cluster)

#### Basic Installation

**Using ntfy (default):**

```bash
helm install property24-bot ./charts/property24-bot \
  --set ntfy.topic=your-unique-topic-name \
  --set image.repository=your-registry/property24-bot \
  --set image.tag=0.1.0
```

**Using Telegram:**

First, create a Kubernetes secret with your Telegram bot token:

```bash
kubectl create secret generic telegram-secret \
  --from-literal=token=YOUR_TELEGRAM_BOT_TOKEN
```

Then install the chart:

```bash
helm install property24-bot ./charts/property24-bot \
  --set notificationMethod=telegram \
  --set telegram.tokenSecret=telegram-secret \
  --set telegram.chatId=YOUR_CHAT_ID \
  --set image.repository=your-registry/property24-bot \
  --set image.tag=0.1.0
```

#### Advanced Helm Configuration

For production deployments, it's recommended to use a custom values file:

```bash
# Copy an example values file
cp charts/property24-bot/values-ntfy-example.yaml my-values.yaml

# Edit with your settings
nano my-values.yaml

# Install with custom values
helm install property24-bot ./charts/property24-bot -f my-values.yaml
```

**Enable persistent storage (recommended):**

```bash
helm install property24-bot ./charts/property24-bot \
  -f my-values.yaml \
  --set persistence.enabled=true \
  --set persistence.size=2Gi
```

#### Verify Deployment

```bash
# Check deployment status
kubectl get deployments -l "app.kubernetes.io/name=property24-bot"

# Check pod status
kubectl get pods -l "app.kubernetes.io/name=property24-bot"

# View logs
kubectl logs -l "app.kubernetes.io/name=property24-bot" -f
```

#### Helm Chart Configuration

See the [Helm Chart README](charts/property24-bot/README.md) for complete configuration options, or check out the [Helm Quick Start Guide](docs/HELM_QUICKSTART.md) for more detailed instructions.

## Configuration

### Notification Methods

The bot supports two notification methods:
- **ntfy** (default): A simple HTTP-based pub-sub notification service
- **Telegram**: Bot-based messaging through the Telegram Bot API

Choose your preferred method by setting `P24_NOTIFICATION_METHOD` in your environment.

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

You will need to create a Telegram bot and find the chat ID.

**Setup Steps:**

1. Create a bot via [BotFather](https://core.telegram.org/bots#botfather) and get the bot token
2. Send a message to your bot
3. Run the utility to discover your chat ID:
```bash
uv run app/util/chat_id.py
```
4. From the output, note your chat ID:
```bash
$ uv run app/util/chat_id.py
Discovered chat IDs:

 - id=1234567890, type=private, name=Werner van der Merwe
```
5. Set the environment variables:
```bash
P24_NOTIFICATION_METHOD=telegram
TELEGRAM_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### Creating the Search Payload

The bot requires a `payload.json` file that defines the Property24 search criteria. This file contains parameters like location, property type, number of bedrooms, price range, etc.

#### Method 1: Using the URL to Payload Utility (Recommended)

The easiest way to create a payload file is to use the included utility script:

1. Go to [Property24](https://www.property24.com/) and configure your search filters (location, price, property type, etc.)
2. Copy the URL from your browser
3. Run the utility to extract the payload:

```bash
# Install the playwright dependency (only needed once)
uv sync --group web

# Generate the payload
uv run app/util/url_to_payload.py "https://www.property24.com/for-sale/..." --output data/payload.json --pretty
```

Example:
```bash
uv run app/util/url_to_payload.py \
  "https://www.property24.com/for-sale/stellenbosch/western-cape/9238" \
  --output data/payload_stellenbosch.json \
  --pretty
```

This will automatically capture the search parameters and save them to a JSON file.

#### Method 2: Manual Creation

You can also manually create or edit the `payload.json` file. Here's a basic example:

```json
{
  "bedrooms": 2,
  "bathrooms": 1,
  "priceFrom": 1000000,
  "priceTo": 2000000,
  "propertyTypes": [4, 5, 6],
  "autoCompleteItems": [
    {
      "id": 9238,
      "name": "Stellenbosch",
      "type": 2
    }
  ]
}
```

### Environment Variables

The application uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) to load configuration from environment variables or a `.env` file.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `P24_NOTIFICATION_METHOD` | ❌ | `ntfy` | Notification method: `ntfy` or `telegram` |
| `NTFY_SERVER` | ❌ | `https://ntfy.sh` | ntfy server URL (only for ntfy method) |
| `NTFY_TOPIC` | ✅ (for ntfy) | – | ntfy topic name (required for ntfy method) |
| `TELEGRAM_TOKEN` | ✅ (for telegram) | – | Bot token from [BotFather](https://core.telegram.org/bots#botfather) |
| `TELEGRAM_CHAT_ID` | ✅ (for telegram) | – | Numeric chat ID for notifications |
| `P24_STATE_FILE` | ❌ | `data/state.duckdb` | DuckDB file for persisting state |
| `P24_PAYLOAD_FILE` | ❌ | `data/payload.json` | Search payload configuration file |
| `P24_POLL_INTERVAL` | ❌ | `60` | Polling interval in seconds (minimum 10) |
| `P24_LOCATION_NAME` | ❌ | `Stellenbosch` | Location label for alert messages |
| `P24_RUN_ONCE` | ❌ | `false` | Run once then exit (useful for testing) |
| `P24_LOG_LEVEL` | ❌ | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Project Structure

```
property24-bot/
├── app/                    # Main application code
│   ├── main.py            # Entry point and main monitoring loop
│   ├── config.py          # Pydantic settings configuration
│   ├── property24.py      # Property24 API interaction
│   ├── state.py           # DuckDB state management
│   ├── telegram.py        # Telegram notification handler
│   ├── ntfy.py            # ntfy notification handler
│   └── util/              # Utility scripts
│       ├── chat_id.py     # Telegram chat ID discovery
│       └── url_to_payload.py  # Convert Property24 URL to payload
├── charts/                 # Helm chart for Kubernetes deployment
│   └── property24-bot/
├── data/                   # Data files (payloads, state)
├── docs/                   # Additional documentation
├── tests/                  # Unit tests
├── Dockerfile             # Container image definition
├── pyproject.toml         # Python project configuration
└── README.md              # This file
```

## Development

### Running Tests

```bash
uv run pytest
```

### Linting and Formatting

The project uses `ruff` for linting and formatting:

```bash
# Run linter
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Type Checking

```bash
uv run mypy app/
```

## Utilities

### Convert Property24 URL to Payload

Convert a Property24 search URL into a payload configuration:

```bash
uv run app/util/url_to_payload.py "https://www.property24.com/for-sale/..."
```

### Discover Telegram Chat ID

Find your Telegram chat ID after messaging your bot:

```bash
uv run app/util/chat_id.py
```

## License

MIT 