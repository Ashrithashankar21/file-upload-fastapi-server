import time
from watchdog.events import FileSystemEventHandler
from threading import Timer
import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv


CSV_FILE_EXTENSION = ".csv"

load_dotenv()

smtp_server = os.getenv("SMTP_SERVER")
smtp_port = os.getenv("SMTP_PORT")
smtp_user = os.getenv("SMTP_USER")
smtp_password = os.getenv("SMTP_PASSWORD")
sender_email = os.getenv("SENDER_EMAIL")
receiver_email = os.getenv("RECEIVER_EMAIL")


if (
    not smtp_server
    or not smtp_port
    or not smtp_user
    or not smtp_password
    or not sender_email
    or not receiver_email
):
    raise ValueError(
        "Email configuration is not set properly in\
 the environment variables."
    )


class DebouncedEventHandler(
    FileSystemEventHandler,
):
    def __init__(
        self,
        csv_file_path,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.event_timers = {}
        self.csv_file_path = csv_file_path
        self.ensure_csv_exists()

    def _debounce(self, event_type, event):
        if event.src_path in self.event_timers:
            self.event_timers[event.src_path].cancel()

        def handle_event():
            if event.src_path.endswith(CSV_FILE_EXTENSION):
                self.log_event(event_type, event.src_path)
                self.send_email(event_type, event.src_path)

            del self.event_timers[event.src_path]

        timer = Timer(0.5, handle_event)
        self.event_timers[event.src_path] = timer
        timer.start()

    def on_modified(self, event):
        self._debounce("modified", event)

    def on_created(self, event):
        self._debounce("created", event)

    def on_deleted(self, event):
        self._debounce("deleted", event)

    def ensure_csv_exists(self):
        """Create the CSV file with headers if it does not exist."""
        if not os.path.isfile(self.csv_file_path):
            with open(self.csv_file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Event Type", "File Path", "Timestamp"])

    def log_event(self, event_type, file_path):
        """Append the event details to the CSV file."""
        with open(self.csv_file_path, "a", newline="") as file:
            writer = csv.writer(file)
            time_stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([event_type, file_path, time_stamp])

    def send_email(self, event_type, file_path):
        """Send an email notification."""
        subject = f"File System Event: {event_type}"
        time_stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        body = f"Event Type: {event_type}\nFile Path: {file_path}\nTime\
 stamp: {time_stamp}"

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                self.send_mail(server, msg)

        except Exception as e:
            print(f"Failed to send email: {e}")

    def send_mail(self, server, msg):
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)