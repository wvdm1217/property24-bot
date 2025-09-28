#!/bin/bash

echo "Starting: Post Create Command"

# UV Sync
uv sync --dev
source .venv/bin/activate

# Install pre-commit hooks
pre-commit install

echo "Finishing: Post Create Command"