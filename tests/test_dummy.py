import pytest


def test_dummy_truth():
    """A second dummy test to confirm pytest discovery works."""
    assert pytest.__name__ == "pytest"
