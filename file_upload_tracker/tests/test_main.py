import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import tempfile
from watchdog.events import FileSystemEvent
from file_upload_tracker.main import app, DebouncedEventHandler


client = TestClient(app)


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


@patch("file_upload_tracker.main.smtplib.SMTP")
@patch.object(DebouncedEventHandler, "send_mail")
@patch("file_upload_tracker.main.smtp_server", "smtp.office365.com")
@patch("file_upload_tracker.main.smtp_port", 587)
@patch("file_upload_tracker.main.smtp_user", "your_test_email@example.com")
@patch("file_upload_tracker.main.smtp_password", "your_test_password")
def test_send_email(mock_send_mail, temp_csv_file):
    handler = DebouncedEventHandler(csv_file_path=temp_csv_file)

    mock_event = MagicMock(spec=FileSystemEvent)
    mock_event.src_path = "test.csv"

    handler.send_email("created", mock_event.src_path)
    mock_send_mail.assert_called_once()


def test_log_event(temp_csv_file):
    handler = DebouncedEventHandler(csv_file_path=temp_csv_file)

    test_event_type = "modified"
    test_file_path = "test.csv"
    handler.log_event(test_event_type, test_file_path)

    with open(temp_csv_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 2
    assert test_event_type in lines[1]
    assert test_file_path in lines[1]


@patch("file_upload_tracker.main.smtp_user", "your_test_email@example.com")
@patch("file_upload_tracker.main.smtp_password", "your_test_password")
@patch("file_upload_tracker.main.sender_email", "sender@example.com")
@patch("file_upload_tracker.main.receiver_email", "receiver@example.com")
def test_send_mail(temp_csv_file):
    # Create a mock SMTP instance
    mock_smtp_instance = MagicMock()

    # Create an instance of the event handler
    handler = DebouncedEventHandler(csv_file_path=temp_csv_file)

    # Create a mock email message
    msg = MagicMock()

    # Call the send_mail method
    handler.send_mail(mock_smtp_instance, msg)

    # Ensure starttls was called
    mock_smtp_instance.starttls.assert_called_once()

    # Ensure login was called with the correct credentials
    mock_smtp_instance.login.assert_called_once_with(
        "your_test_email@example.com", "your_test_password"
    )

    # Ensure sendmail was called with the correct parameters
    mock_smtp_instance.sendmail.assert_called_once_with(
        "sender@example.com", "receiver@example.com", msg.as_string()
    )


def test_ensure_csv_exists(temp_directory):
    temp_csv_path = os.path.join(temp_directory, "test.csv")
    handler = DebouncedEventHandler(csv_file_path=temp_csv_path)

    assert os.path.isfile(temp_csv_path)


def test_track_folder_changes(temp_directory):
    response = client.get("/track-file-changes")
    assert response.status_code == 200
    assert response.json() == {"message": "File Upload Tracker is running."}


if __name__ == "__main__":
    pytest.main()
