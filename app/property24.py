"""Property24 listing scraping utilities."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlencode

import requests

from app.logger import get_logger

BASE_URL = "https://www.property24.com"
PAGE_SIZE = 20

DEFAULT_LISTING_FILE = Path("listing.txt")
DEFAULT_PREVIOUS_FILE = Path("old.txt")
DEFAULT_NEW_FILE = Path("new.txt")

# Mapping of Property24 property type identifiers to query parameter values.
PROPERTY_CATEGORY_MAP = {
    1: "House",
    2: "ApartmentOrFlat",
    3: "Townhouse",
    4: "House",
    5: "ApartmentOrFlat",
    6: "Townhouse",
    7: "VacantLand",
    8: "CommercialProperty",
    9: "IndustrialProperty",
    10: "Farm",
    11: "GuestHouse",
    12: "FlatShare",
}

LISTING_NUMBER_PATTERN = re.compile(r'data-listing-number="(\d+)"')
LISTING_HREF_PATTERN = re.compile(r'href="(?P<path>/to-rent/[^"?#]+/(?P<number>\d+))"')


logger = get_logger(__name__)


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def _build_property_categories(payload: Mapping[str, object]) -> list[str]:
    property_types = payload.get("propertyTypes")
    if not isinstance(property_types, Sequence):
        return []

    categories: list[str] = []
    for raw_type in property_types:
        try:
            property_type = int(raw_type)
        except (TypeError, ValueError):
            continue
        category = PROPERTY_CATEGORY_MAP.get(property_type)
        if category and category not in categories:
            categories.append(category)
    return categories


def _build_listing_path(payload: Mapping[str, object]) -> str:
    auto_complete_items = payload.get("autoCompleteItems")
    if not isinstance(auto_complete_items, Sequence) or not auto_complete_items:
        raise RuntimeError("Payload missing autoCompleteItems entry")

    first_item = auto_complete_items[0]
    if not isinstance(first_item, Mapping):
        raise RuntimeError("Invalid autoCompleteItems entry")

    normalized_name = first_item.get("normalizedName")
    name = first_item.get("name")
    location_id = first_item.get("id")
    parent_name = first_item.get("parentName")

    if location_id is None:
        raise RuntimeError("Payload missing location identifier")

    if isinstance(normalized_name, str) and normalized_name.strip():
        area_slug = _slugify(normalized_name)
    elif isinstance(name, str):
        area_slug = _slugify(name)
    else:
        raise RuntimeError("Payload missing location name")

    parent_slug = _slugify(parent_name) if isinstance(parent_name, str) else ""

    if parent_slug:
        return f"/to-rent/{area_slug}/{parent_slug}/{location_id}"
    return f"/to-rent/{area_slug}/{location_id}"


def _build_listing_page_url(payload: Mapping[str, object], page: int) -> str:
    base_path = _build_listing_path(payload)
    query_string = ""
    categories = _build_property_categories(payload)
    if categories:
        query_string = urlencode({"PropertyCategory": ",".join(categories)})

    suffix = f"/p{page}"
    if query_string:
        suffix = f"{suffix}?{query_string}"
    return f"{BASE_URL}{base_path}{suffix}"


def _extract_listing_urls(html: str, valid_numbers: Iterable[str]) -> list[str]:
    valid_set = set(valid_numbers)
    urls: list[str] = []

    for match in LISTING_HREF_PATTERN.finditer(html):
        number = match.group("number")
        if valid_set and number not in valid_set:
            continue
        path = match.group("path")
        absolute = f"{BASE_URL}{path}"
        if absolute not in urls:
            urls.append(absolute)
    return urls


def fetch_listing_urls(
    payload: Mapping[str, object],
    *,
    count: int,
    session: requests.Session | None = None,
) -> list[str]:
    """Fetch all listing URLs for the search payload."""

    if count < 0:
        raise ValueError("Count cannot be negative")

    total_pages = max(1, math.ceil(count / PAGE_SIZE)) if count else 1
    local_session: requests.Session | None = None
    if session is None:
        local_session = requests.Session()
        session = local_session

    urls: list[str] = []
    seen_numbers: set[str] = set()

    try:
        for page in range(1, total_pages + 1):
            page_url = _build_listing_page_url(payload, page)
            try:
                response = session.get(page_url, timeout=15)
                response.raise_for_status()
            except requests.RequestException as exc:
                raise RuntimeError(f"Failed to fetch listing page {page}") from exc

            html = response.text
            numbers = set(LISTING_NUMBER_PATTERN.findall(html))
            seen_numbers.update(numbers)
            page_urls = _extract_listing_urls(html, numbers or seen_numbers)
            for url in page_urls:
                if url not in urls:
                    urls.append(url)

        if count and len(urls) < count:
            logger.debug(
                "Extracted %s listing URLs but count is %s (pages=%s)",
                len(urls),
                count,
                total_pages,
            )
    finally:
        if local_session is not None:
            local_session.close()

    return urls


def _read_urls(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return [line.strip() for line in content.splitlines() if line.strip()]


def _write_urls(path: Path, urls: Sequence[str]) -> None:
    if path.parent and path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(urls)
    if text:
        text = f"{text}\n"
    path.write_text(text, encoding="utf-8")


class ListingTracker:
    """Track listing URLs across runs and identify new entries."""

    def __init__(
        self,
        *,
        listing_file: Path = DEFAULT_LISTING_FILE,
        previous_file: Path = DEFAULT_PREVIOUS_FILE,
        new_file: Path = DEFAULT_NEW_FILE,
    ) -> None:
        self.listing_file = listing_file
        self.previous_file = previous_file
        self.new_file = new_file

    def load_previous(self) -> list[str]:
        return _read_urls(self.listing_file)

    def record(self, urls: Sequence[str]) -> list[str]:
        previous_urls = self.load_previous()
        previous_set = set(previous_urls)

        if previous_urls:
            _write_urls(self.previous_file, previous_urls)
        elif self.previous_file.exists():
            self.previous_file.write_text("", encoding="utf-8")

        _write_urls(self.listing_file, urls)

        new_urls = [url for url in urls if url not in previous_set]

        if new_urls:
            _write_urls(self.new_file, new_urls)
        elif self.new_file.exists():
            self.new_file.write_text("", encoding="utf-8")

        return new_urls
