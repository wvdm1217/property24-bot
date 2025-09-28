from pathlib import Path

import pytest

from app.property24 import ListingTracker, fetch_listing_urls


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:  # noqa: D401 - simple stub
        """Pretend the response is successful."""


class DummySession:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.called_urls: list[str] = []

    def get(self, url: str, timeout: int) -> DummyResponse:
        self.called_urls.append(url)
        return DummyResponse(self.response_text)


@pytest.fixture()
def sample_payload() -> dict[str, object]:
    return {
        "autoCompleteItems": [
            {
                "normalizedName": "Stellenbosch",
                "parentName": "Western Cape",
                "id": 459,
            }
        ],
        "propertyTypes": [4, 5, 6],
    }


def test_fetch_listing_urls_extracts_unique_links(
    sample_payload: dict[str, object],
) -> None:
    html = """
    <div data-listing-number="12345"></div>
    <a href="/to-rent/stellenbosch/western-cape/459/12345">Listing 12345</a>
    <div data-listing-number="67890"></div>
    <a href="/to-rent/stellenbosch/western-cape/459/67890">Listing 67890</a>
    <a href="/to-rent/stellenbosch/western-cape/459/67890">Duplicate 67890</a>
    """
    session = DummySession(response_text=html)

    urls = fetch_listing_urls(sample_payload, count=2, session=session)  # type: ignore[arg-type]

    expected_url = (
        "https://www.property24.com/to-rent/stellenbosch/western-cape/459"
        "/p1?PropertyCategory=House%2CApartmentOrFlat%2CTownhouse"
    )
    assert session.called_urls == [expected_url]
    assert urls == [
        "https://www.property24.com/to-rent/stellenbosch/western-cape/459/12345",
        "https://www.property24.com/to-rent/stellenbosch/western-cape/459/67890",
    ]


def test_listing_tracker_records_new_urls(tmp_path: Path) -> None:
    listing_file = tmp_path / "listing.txt"
    previous_file = tmp_path / "old.txt"
    new_file = tmp_path / "new.txt"

    tracker = ListingTracker(
        listing_file=listing_file,
        previous_file=previous_file,
        new_file=new_file,
    )

    first_urls = ["https://example.com/1", "https://example.com/2"]
    recorded_first = tracker.record(first_urls)

    assert recorded_first == first_urls
    assert listing_file.read_text(encoding="utf-8").strip().splitlines() == first_urls
    assert new_file.read_text(encoding="utf-8").strip().splitlines() == first_urls
    assert not previous_file.exists()

    second_urls = ["https://example.com/2", "https://example.com/3"]
    recorded_second = tracker.record(second_urls)

    assert recorded_second == ["https://example.com/3"]
    assert listing_file.read_text(encoding="utf-8").strip().splitlines() == second_urls
    assert new_file.read_text(encoding="utf-8").strip().splitlines() == [
        "https://example.com/3"
    ]
    assert previous_file.read_text(encoding="utf-8").strip().splitlines() == first_urls
