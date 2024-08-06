import csv
import os
import time

CSV_FILE_EXTENSION = ".csv"


def ensure_csv_exists(csv_file_path) -> None:
    """Create the CSV file if it does not exist."""
    if not os.path.isfile(csv_file_path):
        with open(csv_file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Event Type", "File Path", "Timestamp"])


def log_event(csv_file_path, event_type, file_path):
    """Append the event details to the CSV file."""
    with open(csv_file_path, "a", newline="") as file:
        writer = csv.writer(file)
        time_stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([event_type, file_path, time_stamp])
