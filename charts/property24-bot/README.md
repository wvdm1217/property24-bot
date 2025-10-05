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

### Metrics Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `metrics.enabled` | Enable Prometheus metrics endpoint | `true` |
| `metrics.port` | Port for metrics server | `8000` |
| `metrics.service.type` | Service type for metrics endpoint | `ClusterIP` |
| `metrics.service.port` | Service port for metrics | `8000` |
| `metrics.service.annotations` | Annotations for metrics service | `{}` |
| `metrics.serviceMonitor.enabled` | Enable ServiceMonitor (requires Prometheus Operator) | `false` |
| `metrics.serviceMonitor.interval` | Prometheus scrape interval | `30s` |
| `metrics.serviceMonitor.scrapeTimeout` | Prometheus scrape timeout | `10s` |
| `metrics.serviceMonitor.labels` | Additional labels for ServiceMonitor | `{}` |
| `metrics.grafanaDashboard.enabled` | Enable Grafana dashboard ConfigMap | `false` |
| `metrics.grafanaDashboard.labels` | Additional labels for dashboard ConfigMap (e.g., `grafana_dashboard: "1"`) | `{}` |
| `metrics.grafanaDashboard.annotations` | Annotations for dashboard ConfigMap | `{}` |

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

### Enable Prometheus metrics with ServiceMonitor

For clusters with Prometheus Operator installed:

```bash
helm install my-property24-bot ./property24-bot \
  --set ntfy.topic=my-topic \
  --set metrics.enabled=true \
  --set metrics.serviceMonitor.enabled=true \
  --set metrics.serviceMonitor.labels.prometheus=kube-prometheus
```

Or in a values file:

```yaml
notificationMethod: ntfy
ntfy:
  topic: my-unique-topic

metrics:
  enabled: true
  port: 8000
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
    labels:
      prometheus: kube-prometheus
```

### Enable Grafana dashboard with kube-prometheus-stack

For clusters with kube-prometheus-stack installed:

```bash
helm install my-property24-bot ./property24-bot \
  --set ntfy.topic=my-topic \
  --set metrics.enabled=true \
  --set metrics.serviceMonitor.enabled=true \
  --set metrics.serviceMonitor.labels.prometheus=kube-prometheus \
  --set metrics.grafanaDashboard.enabled=true \
  --set-string metrics.grafanaDashboard.labels.grafana_dashboard="1"
```

Or in a values file:

```yaml
notificationMethod: ntfy
ntfy:
  topic: my-unique-topic

metrics:
  enabled: true
  port: 8000
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
    labels:
      prometheus: kube-prometheus
  grafanaDashboard:
    enabled: true
    labels:
      grafana_dashboard: "1"  # Required for auto-discovery
```

The dashboard will be automatically imported into Grafana if the sidecar is enabled in your kube-prometheus-stack deployment.

### Access metrics endpoint

When metrics are enabled, you can access the metrics endpoint:

```bash
# Port-forward to the metrics port
kubectl port-forward svc/my-property24-bot-metrics 8000:8000

# Access metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
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

## Monitoring

### Prometheus Metrics

The chart exposes Prometheus metrics when `metrics.enabled` is `true` (default). The following metrics are available:

- `property24_current_count` - Current number of properties being tracked
- `property24_count_changes_total` - Total property count changes
- `property24_listings_new_total` - Total new listings discovered
- `property24_fetch_errors_total` - Total API fetch errors
- `property24_notifications_sent_total` - Total notifications sent
- `property24_poll_duration_seconds` - Polling duration histogram
- `property24_app_info` - Application metadata
- `property24_app_start_time_seconds` - Application start timestamp

### Prometheus Operator Integration

If you have Prometheus Operator installed, enable the ServiceMonitor:

```yaml
metrics:
  enabled: true
  serviceMonitor:
    enabled: true
    labels:
      prometheus: kube-prometheus  # Match your Prometheus selector
```

The ServiceMonitor will be automatically discovered by Prometheus Operator and start scraping metrics.

### Grafana Dashboard

The chart includes a pre-built Grafana dashboard that works with kube-prometheus-stack. To enable it:

```yaml
metrics:
  enabled: true
  grafanaDashboard:
    enabled: true
    labels:
      grafana_dashboard: "1"  # Required for kube-prometheus-stack auto-discovery
```

The dashboard includes the following visualizations:

- **Current Property Count** - Real-time count of tracked properties
- **New Listings** - Total new listings discovered
- **Uptime** - Application uptime tracking
- **Notification Success Rate** - Gauge showing notification delivery success rate
- **Property Count Over Time** - Historical trend of property counts
- **New Listings Rate** - Rate of new property discoveries
- **Notifications Sent Rate** - Breakdown of notifications by method and status
- **Fetch Errors Rate** - API error tracking
- **Poll Duration Percentiles** - Performance metrics (p50, p95, p99)
- **Property Count Changes** - Rate of property count increases/decreases

The dashboard includes template variables for:
- **Data Source** - Select your Prometheus data source
- **Namespace** - Filter by Kubernetes namespace
- **Location** - Filter by location (e.g., Stellenbosch)

Once deployed, the dashboard will be automatically discovered by Grafana if you're using kube-prometheus-stack with the sidecar enabled.

### Manual Prometheus Configuration

If not using Prometheus Operator, add the following to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'property24-bot'
    kubernetes_sd_configs:
      - role: service
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_label_app_kubernetes_io_name]
        regex: property24-bot
        action: keep
      - source_labels: [__meta_kubernetes_service_label_app_kubernetes_io_component]
        regex: metrics
        action: keep
```

### Example Grafana Queries

Monitor current property count:
```promql
property24_current_count{location="Stellenbosch"}
```

New listings rate per hour:
```promql
rate(property24_listings_new_total[1h]) * 3600
```

Notification success rate:
```promql
rate(property24_notifications_sent_total{status="success"}[5m])
  / rate(property24_notifications_sent_total[5m])
```

