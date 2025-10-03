"""Prometheus metrics for the Property24 bot."""

from __future__ import annotations

import time

from prometheus_client import Counter, Gauge, Histogram

# Metrics for monitoring the property monitoring loop
property_count_gauge = Gauge(
    "property24_current_count",
    "Current number of properties being tracked",
    ["location"],
)

property_count_changes = Counter(
    "property24_count_changes_total",
    "Total number of times the property count has changed",
    ["location", "change_type"],
)

listings_new_total = Counter(
    "property24_listings_new_total",
    "Total number of new listings discovered",
    ["location"],
)

fetch_errors_total = Counter(
    "property24_fetch_errors_total",
    "Total number of errors fetching property data",
    ["error_type"],
)

notifications_sent_total = Counter(
    "property24_notifications_sent_total",
    "Total number of notifications sent",
    ["method", "status"],
)

poll_duration_seconds = Histogram(
    "property24_poll_duration_seconds",
    "Duration of property polling operations",
    ["location"],
)

# Application info and uptime
app_info = Gauge(
    "property24_app_info",
    "Application information",
    ["version", "notification_method"],
)

app_start_time_seconds = Gauge(
    "property24_app_start_time_seconds",
    "Unix timestamp when the application started",
)

# Initialize app start time
app_start_time_seconds.set(time.time())
