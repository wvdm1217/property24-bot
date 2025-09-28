"""Application settings powered by Pydantic."""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.logger import get_logger

DEFAULT_COUNT_FILE = "count.txt"
DEFAULT_PAYLOAD_FILE = "data/payload.json"
DEFAULT_POLL_INTERVAL = 60
MIN_POLL_INTERVAL = 10

logger = get_logger(__name__)

def _coerce_path_value(value: Path | str | None, default: str) -> Path:
    if value is None:
        return Path(default)
    if isinstance(value, Path):
        return value
    value = value.strip()
    return Path(value or default)


class MonitorSettings(BaseSettings):
    """Runtime configuration derived from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    token: str = Field(validation_alias=AliasChoices("TELEGRAM_TOKEN"))
    chat_id: str = Field(validation_alias=AliasChoices("TELEGRAM_CHAT_ID"))
    count_file: Path = Field(
        default=Path(DEFAULT_COUNT_FILE),
        validation_alias=AliasChoices("P24_COUNT_FILE"),
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

    @field_validator("count_file", mode="before")
    @classmethod
    def _coerce_count_file(cls, value: Path | str | None) -> Path:
        return _coerce_path_value(value, DEFAULT_COUNT_FILE)

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

