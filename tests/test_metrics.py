"""Tests for the metrics endpoint."""

from __future__ import annotations

import time
from http.client import HTTPConnection
from typing import TYPE_CHECKING

import pytest

from app.metrics import (
    app_info,
    fetch_errors_total,
    listings_new_total,
    notifications_sent_total,
    property_count_gauge,
)
from app.server import start_metrics_server

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def metrics_server() -> Generator[int, None, None]:
    """Start a metrics server on a test port."""
    port = 18000  # Use a different port for testing
    start_metrics_server(port=port)
    # Give the server a moment to start
    time.sleep(0.2)
    yield port
    # Server runs in daemon thread and will be cleaned up automatically


def test_metrics_endpoint_is_accessible(metrics_server: int) -> None:
    """Test that the /metrics endpoint is accessible."""
    conn = HTTPConnection("localhost", metrics_server)
    try:
        conn.request("GET", "/metrics")
        response = conn.getresponse()
        assert response.status == 200
        assert "text/plain" in response.getheader("Content-Type", "")

        body = response.read().decode("utf-8")
        assert len(body) > 0
        # Check for some expected metrics
        assert "property24_" in body
    finally:
        conn.close()


def test_health_endpoint(metrics_server: int) -> None:
    """Test that the /health endpoint is accessible."""
    conn = HTTPConnection("localhost", metrics_server)
    try:
        conn.request("GET", "/health")
        response = conn.getresponse()
        assert response.status == 200

        body = response.read().decode("utf-8")
        assert body == "OK"
    finally:
        conn.close()


def test_root_endpoint_redirects_to_health(metrics_server: int) -> None:
    """Test that the root endpoint serves health check."""
    conn = HTTPConnection("localhost", metrics_server)
    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        assert response.status == 200

        body = response.read().decode("utf-8")
        assert body == "OK"
    finally:
        conn.close()


def test_not_found_endpoint(metrics_server: int) -> None:
    """Test that unknown endpoints return 404."""
    conn = HTTPConnection("localhost", metrics_server)
    try:
        conn.request("GET", "/unknown")
        response = conn.getresponse()
        assert response.status == 404
    finally:
        conn.close()


def test_metrics_contain_expected_metrics(metrics_server: int) -> None:
    """Test that metrics endpoint exposes expected Prometheus metrics."""
    # Set some test values
    property_count_gauge.labels(location="TestLocation").set(42)
    listings_new_total.labels(location="TestLocation").inc(5)
    fetch_errors_total.labels(error_type="test_error").inc(2)
    notifications_sent_total.labels(method="ntfy", status="success").inc(3)
    app_info.labels(version="0.1.0", notification_method="ntfy").set(1)

    conn = HTTPConnection("localhost", metrics_server)
    try:
        conn.request("GET", "/metrics")
        response = conn.getresponse()
        body = response.read().decode("utf-8")

        # Check for our custom metrics
        assert "property24_current_count" in body
        assert "property24_listings_new_total" in body
        assert "property24_fetch_errors_total" in body
        assert "property24_notifications_sent_total" in body
        assert "property24_app_info" in body
        assert "property24_app_start_time_seconds" in body

        # Check for process metrics (added by prometheus_client by default)
        assert "process_" in body or "python_" in body
    finally:
        conn.close()


def test_metrics_labels_work_correctly(metrics_server: int) -> None:
    """Test that metric labels are properly included."""
    # Set labeled metrics
    property_count_gauge.labels(location="Stellenbosch").set(100)
    property_count_gauge.labels(location="CapeTown").set(200)

    conn = HTTPConnection("localhost", metrics_server)
    try:
        conn.request("GET", "/metrics")
        response = conn.getresponse()
        body = response.read().decode("utf-8")

        # Check that both labels appear
        assert 'location="Stellenbosch"' in body
        assert 'location="CapeTown"' in body
    finally:
        conn.close()
