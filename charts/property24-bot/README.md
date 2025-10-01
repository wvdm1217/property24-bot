# Property24 Bot Helm Chart

A Helm chart for deploying the Property24 webscraping bot on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+

## Installing the Chart

### Using ntfy (default)

```bash
helm install my-property24-bot ./property24-bot \
  --set ntfy.topic=your-unique-topic-name
```

### Using Telegram

First, create a secret with your Telegram bot token:

```bash
kubectl create secret generic telegram-secret \
  --from-literal=token=YOUR_TELEGRAM_BOT_TOKEN
```

Then install the chart:

```bash
helm install my-property24-bot ./property24-bot \
  --set notificationMethod=telegram \
  --set telegram.tokenSecret=telegram-secret \
  --set telegram.chatId=YOUR_CHAT_ID
```

## Configuration

The following table lists the configurable parameters of the Property24 Bot chart and their default values.

### Basic Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `property24-bot` |
| `image.tag` | Image tag (defaults to Chart appVersion) | `""` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |

### Notification Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `notificationMethod` | Notification method: `ntfy` or `telegram` | `ntfy` |
| `ntfy.server` | Ntfy server URL | `https://ntfy.sh` |
| `ntfy.topic` | Ntfy topic name (required for ntfy) | `""` |
| `telegram.tokenSecret` | Name of secret containing TELEGRAM_TOKEN | `""` |
| `telegram.chatId` | Telegram chat ID | `""` |

### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `app.pollInterval` | Polling interval in seconds | `60` |
| `app.locationName` | Location name for notifications | `Stellenbosch` |
| `app.runOnce` | Run once then exit | `false` |
| `app.logLevel` | Log level (DEBUG, INFO, etc.) | `INFO` |
| `app.payloadFile` | Path to payload file | `data/payload.json` |
| `app.stateFile` | Path to state database file | `data/state.duckdb` |

### Storage Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `persistence.enabled` | Enable persistent storage for state | `false` |
| `persistence.size` | Storage size | `1Gi` |
| `persistence.accessMode` | Access mode | `ReadWriteOnce` |
| `persistence.storageClass` | Storage class | `""` |
| `payload.useConfigMap` | Use ConfigMap for payload.json | `false` |
| `payload.configMapName` | ConfigMap name for payload | `""` |

### Resource Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources` | CPU/Memory resource requests/limits | `{}` |
| `nodeSelector` | Node labels for pod assignment | `{}` |
| `tolerations` | Tolerations for pod assignment | `[]` |
| `affinity` | Affinity rules for pod assignment | `{}` |

## Examples

### Enable persistent storage

```bash
helm install my-property24-bot ./property24-bot \
  --set ntfy.topic=my-topic \
  --set persistence.enabled=true \
  --set persistence.size=2Gi
```

### Set resource limits

```bash
helm install my-property24-bot ./property24-bot \
  --set ntfy.topic=my-topic \
  --set resources.limits.cpu=200m \
  --set resources.limits.memory=256Mi \
  --set resources.requests.cpu=100m \
  --set resources.requests.memory=128Mi
```

### Use a custom values file

Create a `my-values.yaml` file:

```yaml
notificationMethod: ntfy
ntfy:
  topic: my-unique-topic

app:
  pollInterval: 120
  locationName: "Cape Town"
  logLevel: "DEBUG"

persistence:
  enabled: true
  size: 2Gi

resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

Then install:

```bash
helm install my-property24-bot ./property24-bot -f my-values.yaml
```

## Uninstalling the Chart

```bash
helm uninstall my-property24-bot
```

## Viewing Logs

```bash
kubectl logs -l "app.kubernetes.io/name=property24-bot" -f
```

## Troubleshooting

### Check pod status

```bash
kubectl get pods -l "app.kubernetes.io/name=property24-bot"
```

### Describe pod for issues

```bash
kubectl describe pod -l "app.kubernetes.io/name=property24-bot"
```

### Check configuration

```bash
helm get values my-property24-bot
```
