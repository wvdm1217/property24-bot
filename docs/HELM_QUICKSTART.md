# Quick Start Guide - Property24 Bot Helm Chart

## Overview

You now have a minimal, production-ready Helm chart for your Property24 bot! 🎉

## What Was Created

```
charts/property24-bot/
├── Chart.yaml                      # Chart metadata
├── values.yaml                     # Default configuration
├── values-ntfy-example.yaml        # Example: ntfy notifications
├── values-telegram-example.yaml    # Example: Telegram notifications
├── README.md                       # Full documentation
└── templates/
    ├── deployment.yaml             # Bot deployment
    ├── serviceaccount.yaml         # Service account
    ├── configmap.yaml              # Optional ConfigMap for payload
    ├── pvc.yaml                    # Optional persistent storage
    ├── _helpers.tpl                # Template helpers
    └── NOTES.txt                   # Post-install notes
```

## Next Steps

### 1. Build and Tag Your Docker Image

```bash
# Build the image
docker build -t property24-bot:0.1.0 .

# If using a registry, tag and push:
docker tag property24-bot:0.1.0 your-registry/property24-bot:0.1.0
docker push your-registry/property24-bot:0.1.0
```

### 2. Choose Your Notification Method

#### Option A: Using ntfy (Simpler)

```bash
helm install property24-bot ./charts/property24-bot \
  --set ntfy.topic=your-unique-topic-name
```

#### Option B: Using Telegram

First, create a Kubernetes secret:

```bash
kubectl create secret generic telegram-secret \
  --from-literal=token=YOUR_TELEGRAM_BOT_TOKEN
```

Then install:

```bash
helm install property24-bot ./charts/property24-bot \
  --set notificationMethod=telegram \
  --set telegram.tokenSecret=telegram-secret \
  --set telegram.chatId=YOUR_CHAT_ID
```

### 3. Customize Using a Values File (Recommended)

Copy an example file and customize it:

```bash
# For ntfy
cp charts/property24-bot/values-ntfy-example.yaml my-values.yaml

# For Telegram
cp charts/property24-bot/values-telegram-example.yaml my-values.yaml

# Edit the file with your settings
nano my-values.yaml

# Install with your custom values
helm install property24-bot ./charts/property24-bot -f my-values.yaml
```

### 4. Verify the Deployment

```bash
# Check the deployment status
kubectl get deployments

# Check pod status
kubectl get pods -l "app.kubernetes.io/name=property24-bot"

# View logs
kubectl logs -l "app.kubernetes.io/name=property24-bot" -f
```

## Common Configurations

### Enable Persistent Storage (Recommended)

Edit your values file to enable persistence:

```yaml
persistence:
  enabled: true
  size: 1Gi
```

### Set Resource Limits

```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Adjust Polling Interval

```yaml
app:
  pollInterval: 120  # Check every 2 minutes instead of 1
```

## Managing Your Deployment

### Upgrade

```bash
helm upgrade property24-bot ./charts/property24-bot -f my-values.yaml
```

### Rollback

```bash
helm rollback property24-bot
```

### Uninstall

```bash
helm uninstall property24-bot
```

### Check Status

```bash
helm status property24-bot
```

## Troubleshooting

### View Pod Events

```bash
kubectl describe pod -l "app.kubernetes.io/name=property24-bot"
```

### Check Configuration

```bash
helm get values property24-bot
```

### Test Template Rendering

```bash
helm template property24-bot ./charts/property24-bot -f my-values.yaml
```

## Notes

- The chart uses a ServiceAccount for better security
- State database can be persisted using PersistentVolumeClaim
- Secrets (like Telegram tokens) are properly referenced from Kubernetes secrets
- The deployment restarts automatically if the ConfigMap changes
- No service/ingress is created (bot doesn't need HTTP exposure)

## Need Help?

Check the full documentation in `charts/property24-bot/README.md`
