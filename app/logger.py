"""Logging utilities for the Property24 bot."""

from __future__ import annotations

import logging
import sys

_logging_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Configure logging for the entire application.

    Should be called once at application startup, before any loggers are created.
    Configures the root logger to use a consistent format and level.

    Args:
        level: Logging level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    global _logging_configured

    if _logging_configured:
        return

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger - this affects all loggers in the hierarchy
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )

    _logging_configured = True
