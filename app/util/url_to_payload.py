"""Utilities for extracting Property24 counter payloads via Playwright."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, cast

from playwright.sync_api import (
    Error as PlaywrightError,
    Request,
    TimeoutError,
    sync_playwright,
)

COUNTER_URL_SUFFIX = "/search/counter"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Navigate to a Property24 search results page, wait for the counter "
            "API call, and print its payload JSON."
        )
    )
    parser.add_argument("url", help="Property24 search results URL to visit")
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Maximum time in seconds to wait for the counter request (default: 20)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Optional path to write the payload JSON; defaults to stdout",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation",
    )
    return parser.parse_args(argv)


def _match_counter_request(request: Request) -> bool:
    return request.url.endswith(COUNTER_URL_SUFFIX) and request.method == "POST"


def _extract_payload(url: str, timeout: float) -> dict[str, Any]:
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            context.set_default_timeout(timeout * 1000)
            page = context.new_page()

            with page.expect_request(
                lambda request: _match_counter_request(request),
                timeout=timeout * 1000,
            ) as request_info:
                page.goto(url, wait_until="networkidle")

            request = request_info.value
            payload_text = request.post_data
            if payload_text is None:
                raise RuntimeError("Counter request did not include a payload body")

            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive
                raise RuntimeError("Counter payload is not valid JSON") from exc

            if not isinstance(payload, dict):
                raise RuntimeError("Counter payload must be a JSON object")

            return cast("dict[str, Any]", payload)
    except TimeoutError as exc:
        raise RuntimeError(
            "Timed out waiting for the Property24 counter request"
        ) from exc
    except PlaywrightError as exc:
        raise RuntimeError("Playwright encountered an error") from exc


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])

    try:
        payload = _extract_payload(args.url, args.timeout)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    json_kwargs: dict[str, Any]
    if args.pretty:
        json_kwargs = {"indent": 2, "ensure_ascii": False}
    else:
        json_kwargs = {"separators": (",", ":")}

    output_text = json.dumps(payload, **json_kwargs)

    if args.output:
        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(output_text)
            if args.pretty:
                fh.write("\n")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
