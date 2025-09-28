import pytest


def test_dummy_truth() -> None:
    """A second dummy test to confirm pytest discovery works."""
    assert pytest.__name__ == "pytest"
