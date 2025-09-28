"""Logging utilities for the Property24 bot."""

from __future__ import annotations

import logging
from typing import Optional

_LOGGER_NAME = "property24"
_CONFIGURED = False


def configure_logging(level: str = "INFO") -> logging.Logger:
	"""Configure and return the application logger."""

	global _CONFIGURED

	if not _CONFIGURED:
		logging.basicConfig(
			level=level,
			format="%(asctime)s %(levelname)s %(message)s",
		)
		_CONFIGURED = True

	logger = logging.getLogger(_LOGGER_NAME)
	logger.setLevel(level)
	return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
	"""Retrieve a logger instance, defaulting to the application logger."""

	if name is None:
		return logging.getLogger(_LOGGER_NAME)
	return logging.getLogger(name)

