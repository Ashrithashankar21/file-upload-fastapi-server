import time
from watchdog.events import FileSystemEventHandler
from threading import Timer
from handlers.log_handler import ensure_csv_exists, log_event
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.load_env import get_env_variable

CSV_FILE_EXTENSION = ".csv"

smtp_server = get_env_variable("SMTP_SERVER")
smtp_port = get_env_variable("SMTP_PORT")
smtp_user = get_env_variable("SMTP_USER")
smtp_password = get_env_variable("SMTP_PASSWORD")
sender_email = get_env_variable("SENDER_EMAIL")
receiver_email = get_env_variable("RECEIVER_EMAIL")


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
        ensure_csv_exists(self.csv_file_path)

    def _debounce(self, event_type, event):
        if event.src_path in self.event_timers:
            self.event_timers[event.src_path].cancel()

        def handle_event():
            if event.src_path.endswith(CSV_FILE_EXTENSION):
                log_event(self.csv_file_path, event_type, event.src_path)
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
