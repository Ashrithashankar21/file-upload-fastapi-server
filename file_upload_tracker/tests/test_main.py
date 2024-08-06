import pytest

from file_upload_tracker.main import add


def test_add():
    print("Running test_add")
    assert add(1, 2) == 3


if __name__ == "__main__":
    pytest.main()
