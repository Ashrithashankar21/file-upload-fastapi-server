import csv
import os
import time

CSV_FILE_EXTENSION = ".csv"


def ensure_csv_exists(csv_file_path: str) -> None:
    """
    Create the CSV file with headers if it does not exist.

    Args:
        csv_file_path (str): The path to the CSV file.

    Returns:
        None
    """
    if not os.path.isfile(csv_file_path):
        with open(csv_file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Event Type", "File Path", "Timestamp"])


def log_event(csv_file_path: str, event_type: str, file_path: str):
    """
    Append the event details to the CSV file.

    Args:
        csv_file_path (str): The path to the CSV file.
        event_type (str): The type of the file system event.
        file_path (str): The path to the file that triggered the event.

    Returns:
        None
    """
    with open(csv_file_path, "a", newline="") as file:
        writer = csv.writer(file)
        time_stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([event_type, file_path, time_stamp])
