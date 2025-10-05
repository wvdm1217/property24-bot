# Build stage
FROM ghcr.io/astral-sh/uv:bookworm-slim AS builder

# Enable bytecode compilation and copy mode for mounted volumes
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure Python directory to be consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.13

# Install build dependencies for DuckDB
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential cmake && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Clean up unnecessary files to reduce image size
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type f -name "*.py[co]" -delete && \
    find /app/.venv -type d -name "tests" -o -name "test" | xargs rm -rf 2>/dev/null || true && \
    find /app/.venv -type f -name "*.so" -exec strip --strip-unneeded {} \; 2>/dev/null || true && \
    find /app/.venv -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -type d -name "locale" -exec rm -rf {} + 2>/dev/null || true

# Runtime stage - minimal distroless image
FROM gcr.io/distroless/cc-debian12

# Copy the Python version from builder
COPY --from=builder /python /python

WORKDIR /app

# Copy the application from builder
COPY --from=builder /app/.venv /app/.venv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main"]