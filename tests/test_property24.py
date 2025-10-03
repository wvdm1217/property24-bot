from urllib.parse import urlencode

import pytest

from app.property24 import BASE_URL, ListingTracker, fetch_listing_urls
from app.state import DuckDBStateStore


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


class DummySessionWithVariableResponses:
    """Session that returns different responses for each call."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.call_count = 0
        self.called_urls: list[str] = []

    def get(self, url: str, timeout: int) -> DummyResponse:
        self.called_urls.append(url)
        response_text = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return DummyResponse(response_text)


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
    # Expect two requests per page to filter out dummy listings
    assert session.called_urls == [expected_url, expected_url]
    assert urls == [
        "https://www.property24.com/to-rent/stellenbosch/western-cape/459/12345",
        "https://www.property24.com/to-rent/stellenbosch/western-cape/459/67890",
    ]


def test_fetch_listing_urls_uses_advanced_search_for_multiple_locations() -> None:
    payload = {
        "autoCompleteItems": [
            {"id": 9136},
            {"id": 9163},
        ],
        "propertyTypes": [4, 5, 6],
        "priceTo": {"value": 20000},
    }

    html = """
    <div data-listing-number="55555"></div>
    <a href="/to-rent/bo-kaap/cape-town/9136/55555">Listing 55555</a>
    """
    session = DummySession(response_text=html)

    urls = fetch_listing_urls(payload, count=1, session=session)  # type: ignore[arg-type]

    expected_query = urlencode(
        [
            ("sp", "s=9136,9163&pt=20000"),
            ("PropertyCategory", "House,ApartmentOrFlat,Townhouse"),
        ]
    )
    expected_url = f"{BASE_URL}/to-rent/advanced-search/results?{expected_query}"

    # Expect two requests per page to filter out dummy listings
    assert session.called_urls == [expected_url, expected_url]
    assert urls == [
        f"{BASE_URL}/to-rent/bo-kaap/cape-town/9136/55555",
    ]


def test_listing_tracker_records_new_urls(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    state_path = tmp_path_factory.mktemp("state") / "state.duckdb"
    state_store = DuckDBStateStore(path=state_path)
    tracker = ListingTracker(state_store=state_store)

    first_urls = ["https://example.com/1", "https://example.com/2"]
    recorded_first = tracker.record(first_urls)

    assert recorded_first == first_urls
    assert state_store.get_current_listings() == first_urls
    assert state_store.get_new_listings() == first_urls
    assert state_store.get_previous_listings() == []

    second_urls = ["https://example.com/2", "https://example.com/3"]
    recorded_second = tracker.record(second_urls)

    assert recorded_second == ["https://example.com/3"]
    assert state_store.get_current_listings() == second_urls
    assert state_store.get_new_listings() == ["https://example.com/3"]
    assert state_store.get_previous_listings() == first_urls


def test_fetch_listing_urls_filters_out_dummy_listings(
    sample_payload: dict[str, object],
) -> None:
    """Test that only listings appearing in both requests are included."""
    # First request includes dummy listing 99999
    first_response = """
    <div data-listing-number="12345"></div>
    <a href="/to-rent/stellenbosch/western-cape/459/12345">Listing 12345</a>
    <div data-listing-number="99999"></div>
    <a href="/to-rent/stellenbosch/western-cape/459/99999">Dummy 99999</a>
    """

    # Second request has real listing 12345 but different dummy 88888
    second_response = """
    <div data-listing-number="12345"></div>
    <a href="/to-rent/stellenbosch/western-cape/459/12345">Listing 12345</a>
    <div data-listing-number="88888"></div>
    <a href="/to-rent/stellenbosch/western-cape/459/88888">Dummy 88888</a>
    """

    session = DummySessionWithVariableResponses(
        responses=[first_response, second_response]
    )

    urls = fetch_listing_urls(sample_payload, count=2, session=session)  # type: ignore[arg-type]

    # Should only include the listing that appeared in both responses
    assert urls == [
        "https://www.property24.com/to-rent/stellenbosch/western-cape/459/12345",
    ]
