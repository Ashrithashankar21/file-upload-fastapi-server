import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY
import os
import tempfile
from main import app
from handlers.file_handlers import DebouncedEventHandler
from handlers.log_handlers import log_event
from handlers.mail_handlers import send_mail

client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def set_env_variables(monkeypatch):
    """
    Pytest fixture to set environment variables for the duration of a test
    function.

    Args:
        monkeypatch: A pytest fixture that allows you to safely set
        and restore attributes, dictionaries, environment variables, etc.

    This fixture sets the following environment variables:
        - SMTP_SERVER: The SMTP server address.
        - SMTP_PORT: The SMTP server port.
        - SMTP_USER: The SMTP server username.
        - SMTP_PASSWORD: The SMTP server password.
        - SENDER_EMAIL: The sender's email address.
        - RECEIVER_EMAIL: The receiver's email address.

    The fixture is automatically used for each test function due to
    the `autouse=True` parameter.
    """
    monkeypatch.setenv("SMTP_SERVER", "smtp.office365.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "ashritha.shankar@solitontech.com")
    monkeypatch.setenv("SMTP_PASSWORD", "abc")
    monkeypatch.setenv("SENDER_EMAIL", "ashritha.shankar@solitontech.com")
    monkeypatch.setenv("RECEIVER_EMAIL", "ashritha.shankar@solitontech.com")


@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_csv_file(temp_directory):
    temp_csv_path = os.path.join(temp_directory, "test.csv")
    with open(temp_csv_path, "w") as f:
        f.write("Event Type,File Path,Timestamp\n")
    return temp_csv_path


def test_log_event(temp_csv_file):
    DebouncedEventHandler(csv_file_path=temp_csv_file)
    test_event_type = "modified"
    test_file_path = "test.csv"
    log_event(temp_csv_file, test_event_type, test_file_path)

    with open(temp_csv_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 2
    assert test_event_type in lines[1]
    assert test_file_path in lines[1]


def test_ensure_csv_exists(temp_directory):
    temp_csv_path = os.path.join(temp_directory, "test.csv")
    DebouncedEventHandler(csv_file_path=temp_csv_path)

    assert os.path.isfile(temp_csv_path)


def test_track_folder_changes():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "File Upload Tracker is running."}


@patch("handlers.mail_handlers.smtplib.SMTP")
@patch("handlers.mail_handlers.get_env_variable")
def test_send_mail(mock_get_env_variable, mock_smtp):

    # Create a mock SMTP instance
    mock_smtp_instance = MagicMock()
    mock_smtp.return_value = mock_smtp_instance

    # Create a mock email message
    mock_msg = MagicMock()
    mock_msg.as_string.return_value = "mock email string"

    # Call the send_mail function
    send_mail(mock_smtp_instance, mock_msg)

    # Assert the correct setup of the SMTP instance
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with(
        "ashritha.shankar@solitontech.com", ANY
    )
    mock_smtp_instance.sendmail.assert_called_once_with(
        "ashritha.shankar@solitontech.com",
        "ashritha.shankar@solitontech.com",
        "mock email string",
    )


if __name__ == "__main__":
    pytest.main()
