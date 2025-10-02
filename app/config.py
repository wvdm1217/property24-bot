"""Application settings powered by Pydantic."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_PAYLOAD_FILE = "data/payload.json"
DEFAULT_POLL_INTERVAL = 60
MIN_POLL_INTERVAL = 10
DEFAULT_STATE_FILE = "data/state.duckdb"

logger = logging.getLogger(__name__)


def _coerce_path_value(value: Path | str | None, default: str) -> Path:
    if value is None:
        return Path(default)
    if isinstance(value, Path):
        return value
    value = value.strip()
    return Path(value or default)


class NtfySettings(BaseSettings):
    """Minimal settings required for ntfy service access."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    server: str = Field(
        default="https://ntfy.sh",
        validation_alias=AliasChoices("NTFY_SERVER"),
    )
    topic: str = Field(validation_alias=AliasChoices("NTFY_TOPIC"))


class TelegramSettings(BaseSettings):
    """Minimal settings required for Telegram API access."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    token: str = Field(validation_alias=AliasChoices("TELEGRAM_TOKEN"))


class MonitorSettings(BaseSettings):
    """Runtime configuration derived from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    # Notification method: 'ntfy' or 'telegram'
    notification_method: str = Field(
        default="ntfy",
        validation_alias=AliasChoices("P24_NOTIFICATION_METHOD"),
    )

    # Ntfy settings
    ntfy_server: str = Field(
        default="https://ntfy.sh",
        validation_alias=AliasChoices("NTFY_SERVER"),
    )
    ntfy_topic: str | None = Field(
        default=None,
        validation_alias=AliasChoices("NTFY_TOPIC"),
    )

    # Telegram settings (optional)
    telegram_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_TOKEN"),
    )
    telegram_chat_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("TELEGRAM_CHAT_ID"),
    )

    payload_file: Path = Field(
        default=Path(DEFAULT_PAYLOAD_FILE),
        validation_alias=AliasChoices("P24_PAYLOAD_FILE"),
    )
    poll_interval: int = Field(
        default=DEFAULT_POLL_INTERVAL,
        validation_alias=AliasChoices("P24_POLL_INTERVAL"),
    )
    location_name: str = Field(
        default="Stellenbosch",
        validation_alias=AliasChoices("P24_LOCATION_NAME"),
    )
    run_once: bool = Field(
        default=False,
        validation_alias=AliasChoices("P24_RUN_ONCE"),
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("P24_LOG_LEVEL"),
    )
    state_file: Path = Field(
        default=Path(DEFAULT_STATE_FILE),
        validation_alias=AliasChoices("P24_STATE_FILE"),
    )

    # Metrics server settings
    metrics_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("P24_METRICS_ENABLED"),
    )
    metrics_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("P24_METRICS_PORT"),
    )

    @field_validator("payload_file", mode="before")
    @classmethod
    def _coerce_payload_file(cls, value: Path | str | None) -> Path:
        return _coerce_path_value(value, DEFAULT_PAYLOAD_FILE)

    @field_validator("poll_interval", mode="after")
    @classmethod
    def _enforce_poll_interval(cls, value: int) -> int:
        if value < MIN_POLL_INTERVAL:
            logger.warning(
                "P24_POLL_INTERVAL=%s is too low. Using %s seconds instead.",
                value,
                MIN_POLL_INTERVAL,
            )
            return MIN_POLL_INTERVAL
        return value

    @field_validator("log_level", mode="after")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("state_file", mode="before")
    @classmethod
    def _coerce_state_file(cls, value: Path | str | None) -> Path:
        return _coerce_path_value(value, DEFAULT_STATE_FILE)

    @model_validator(mode="after")
    def _validate_notification_settings(self) -> "MonitorSettings":
        """Validate that required fields are present based on notification method."""
        method = self.notification_method.lower()

        if method == "ntfy":
            if not self.ntfy_topic:
                raise ValueError(
                    "NTFY_TOPIC is required when using ntfy notification method"
                )
        elif method == "telegram":
            if not self.telegram_token:
                raise ValueError(
                    "TELEGRAM_TOKEN is required when using telegram notification method"
                )
            if not self.telegram_chat_id:
                raise ValueError(
                    "TELEGRAM_CHAT_ID is required when using telegram "
                    "notification method"
                )
        else:
            raise ValueError(
                f"Invalid notification method: {method}. Must be 'ntfy' or 'telegram'"
            )

        return self
