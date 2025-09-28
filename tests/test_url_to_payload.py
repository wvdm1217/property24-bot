"""Tests for the Playwright-backed Property24 payload extractor."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace, TracebackType
from typing import Any, Callable, Literal

import pytest

from app.util import url_to_payload


class DummyRequest:
    def __init__(self, url: str, method: str, payload: dict[str, Any]) -> None:
        self.url = url
        self.method = method
        self.post_data = json.dumps(payload)


class DummyExpectation:
    def __init__(
        self,
        request: DummyRequest,
        predicate: Callable[[Any], bool],
    ) -> None:
        if not predicate(request):
            raise AssertionError("Predicate did not match request")
        self.value = request

    def __enter__(self) -> "DummyExpectation":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        return False


class DummyPage:
    def __init__(self, request: DummyRequest) -> None:
        self.request = request
        self.goto_calls: list[tuple[str, str]] = []

    def expect_request(
        self,
        predicate: Callable[[Any], bool],
        timeout: float,
    ) -> DummyExpectation:
        return DummyExpectation(self.request, predicate)

    def goto(self, url: str, wait_until: str) -> None:
        self.goto_calls.append((url, wait_until))


class DummyContext:
    def __init__(self, page: DummyPage) -> None:
        self.page = page
        self.default_timeout: float | None = None

    def new_page(self) -> DummyPage:
        return self.page

    def new_context(self) -> "DummyContext":
        return self

    def set_default_timeout(self, value: float) -> None:
        self.default_timeout = value


class DummyBrowser:
    def __init__(self, context: DummyContext) -> None:
        self.context = context

    def new_context(self) -> DummyContext:
        return self.context


class DummyChromium:
    def __init__(self, browser: DummyBrowser) -> None:
        self.browser = browser

    def launch(self, *, headless: bool) -> DummyBrowser:
        assert headless is True
        return self.browser


class DummyPlaywright:
    def __init__(self, chromium: DummyChromium) -> None:
        self.chromium = chromium


class DummySyncPlaywright:
    def __init__(self, playwright: DummyPlaywright) -> None:
        self.playwright = playwright

    def __enter__(self) -> DummyPlaywright:
        return self.playwright

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        return False


@pytest.fixture()
def fake_sync_playwright(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"foo": "bar"}
    request = DummyRequest(
        url="https://www.property24.com/search/counter",
        method="POST",
        payload=payload,
    )
    page = DummyPage(request)
    context = DummyContext(page)
    browser = DummyBrowser(context)
    chromium = DummyChromium(browser)
    playwright = DummyPlaywright(chromium)
    dummy_sync = DummySyncPlaywright(playwright)

    monkeypatch.setattr(url_to_payload, "sync_playwright", lambda: dummy_sync)

    # provide access to the fabricated objects for assertions
    monkeypatch.setattr(url_to_payload, "_TEST_PAGE", page, raising=False)
    monkeypatch.setattr(url_to_payload, "_TEST_REQUEST", request, raising=False)


def test_match_counter_request() -> None:
    request = SimpleNamespace(url="https://x.com/search/counter", method="POST")
    assert url_to_payload._match_counter_request(request) is True  # type: ignore[arg-type]

    request_get = SimpleNamespace(url="https://x.com/search/counter", method="GET")
    assert url_to_payload._match_counter_request(request_get) is False  # type: ignore[arg-type]

    request_other = SimpleNamespace(url="https://x.com/other", method="POST")
    assert url_to_payload._match_counter_request(request_other) is False  # type: ignore[arg-type]


def test_extract_payload(
    monkeypatch: pytest.MonkeyPatch,
    fake_sync_playwright: None,
) -> None:
    result = url_to_payload._extract_payload("https://example.com", timeout=5)

    assert result == json.loads(url_to_payload._TEST_REQUEST.post_data)  # type: ignore[attr-defined]


def test_main_prints_payload(
    monkeypatch: pytest.MonkeyPatch,
    fake_sync_playwright: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(url_to_payload, "_extract_payload", lambda u, t: {"foo": "bar"})

    url_to_payload.main(["https://example.com", "--pretty"])

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"foo": "bar"}
    assert captured.err == ""


def test_main_writes_to_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fake_sync_playwright: None,
) -> None:
    monkeypatch.setattr(url_to_payload, "_extract_payload", lambda u, t: {"k": 1})

    output_file = tmp_path / "payload.json"
    url_to_payload.main(["https://example.com", "--output", str(output_file)])

    assert json.loads(output_file.read_text(encoding="utf-8")) == {"k": 1}


def test_main_handles_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        url_to_payload,
        "_extract_payload",
        lambda u, t: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    with pytest.raises(SystemExit) as exc_info:
        url_to_payload.main(["https://example.com"])

    assert exc_info.value.code == 1
    assert "boom" in capsys.readouterr().err
