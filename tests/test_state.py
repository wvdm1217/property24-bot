from pathlib import Path

from app.state import DuckDBStateStore


def test_state_store_persists_counts(tmp_path: Path) -> None:
    state_path = tmp_path / "state.duckdb"
    store = DuckDBStateStore(path=state_path)

    assert store.get_property_count() == 0

    store.set_property_count(5)
    assert store.get_property_count() == 5

    # Re-open to ensure persistence.
    reopened = DuckDBStateStore(path=state_path)
    assert reopened.get_property_count() == 5


def test_state_store_updates_listings(tmp_path: Path) -> None:
    store = DuckDBStateStore(path=tmp_path / "state.duckdb")

    first_urls = ["https://example.com/1", "https://example.com/2"]
    assert store.update_current_listings(first_urls) == first_urls
    assert store.get_current_listings() == first_urls
    assert store.get_previous_listings() == []
    assert store.get_new_listings() == first_urls

    second_urls = ["https://example.com/2", "https://example.com/3"]
    assert store.update_current_listings(second_urls) == ["https://example.com/3"]
    assert store.get_current_listings() == second_urls
    assert store.get_previous_listings() == first_urls
    assert store.get_new_listings() == ["https://example.com/3"]
