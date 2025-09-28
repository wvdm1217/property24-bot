#!/bin/bash

echo "Starting: Post Create Command"

# UV Sync
uv sync --all-groups
source .venv/bin/activate

# Install pre-commit hooks
pre-commit install

# Install Playwright browsers
playwright install chromium --with-deps

echo "Finishing: Post Create Command"