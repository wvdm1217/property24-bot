"""DuckDB-backed persistence for Property24 bot state."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import duckdb

from app.logger import get_logger

DEFAULT_STATE_FILE = Path("data/state.duckdb")

logger = get_logger(__name__)


class DuckDBStateStore:
    """Persist bot state (counts and listing snapshots) in DuckDB."""

    def __init__(self, path: Path = DEFAULT_STATE_FILE) -> None:
        self.path = path
        self._initialise()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        if self.path.parent and self.path.parent != Path(""):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.path))

    def _initialise(self) -> None:
        connection = self._connect()
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS listings (
                    snapshot TEXT,
                    position INTEGER,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (snapshot, position)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS listings_snapshot_position_idx
                ON listings (snapshot, position)
                """
            )
        finally:
            connection.close()

    def get_property_count(self) -> int:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'property_count'"
            ).fetchone()
            if row is None:
                return 0

            raw_value = row[0]
            try:
                return int(raw_value)
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid property count '%s' in state store; resetting to 0.",
                    raw_value,
                )
                connection.execute("DELETE FROM metadata WHERE key = 'property_count'")
                connection.execute(
                    "INSERT INTO metadata (key, value) VALUES (?, ?)",
                    ("property_count", "0"),
                )
                return 0
        finally:
            connection.close()

    def set_property_count(self, value: int) -> None:
        connection = self._connect()
        try:
            connection.execute("DELETE FROM metadata WHERE key = 'property_count'")
            connection.execute(
                "INSERT INTO metadata (key, value) VALUES (?, ?)",
                ("property_count", str(value)),
            )
        finally:
            connection.close()

    def _snapshot_urls(self, snapshot: str) -> list[str]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT url FROM listings WHERE snapshot = ? ORDER BY position",
                (snapshot,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            connection.close()

    def get_current_listings(self) -> list[str]:
        return self._snapshot_urls("current")

    def get_previous_listings(self) -> list[str]:
        return self._snapshot_urls("previous")

    def get_new_listings(self) -> list[str]:
        return self._snapshot_urls("new")

    def update_current_listings(self, urls: Sequence[str]) -> list[str]:
        urls_list = list(urls)
        connection = self._connect()
        try:
            connection.execute("BEGIN")
            existing_rows = connection.execute(
                "SELECT position, url FROM listings WHERE snapshot = 'current' "
                "ORDER BY position"
            ).fetchall()

            connection.execute("DELETE FROM listings WHERE snapshot = 'previous'")
            for index, (_, url) in enumerate(existing_rows):
                connection.execute(
                    "INSERT INTO listings (snapshot, position, url) VALUES (?, ?, ?)",
                    ("previous", index, url),
                )

            connection.execute("DELETE FROM listings WHERE snapshot = 'current'")
            for index, url in enumerate(urls_list):
                connection.execute(
                    "INSERT INTO listings (snapshot, position, url) VALUES (?, ?, ?)",
                    ("current", index, url),
                )

            previous_urls = [row[1] for row in existing_rows]
            previous_set = set(previous_urls)
            new_urls = [url for url in urls_list if url not in previous_set]

            connection.execute("DELETE FROM listings WHERE snapshot = 'new'")
            for index, url in enumerate(new_urls):
                connection.execute(
                    "INSERT INTO listings (snapshot, position, url) VALUES (?, ?, ?)",
                    ("new", index, url),
                )

            connection.execute("COMMIT")
        except Exception:  # pragma: no cover - defensive
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

        return new_urls

    def reset(self) -> None:
        """Clear all stored state."""

        connection = self._connect()
        try:
            connection.execute("DELETE FROM metadata")
            connection.execute("DELETE FROM listings")
        finally:
            connection.close()

    def ensure_file(self) -> None:
        """Ensure the underlying database file exists on disk."""

        # Connecting already creates the file if needed.
        connection = self._connect()
        connection.close()

    def iterate_snapshot(self, snapshot: str) -> Iterable[str]:
        """Yield URLs for a snapshot without loading all in memory."""

        connection = self._connect()
        try:
            result = connection.execute(
                "SELECT url FROM listings WHERE snapshot = ? ORDER BY position",
                (snapshot,),
            )
            for row in result.fetchall():
                yield row[0]
        finally:
            connection.close()
