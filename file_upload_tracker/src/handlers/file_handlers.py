from watchdog.events import FileSystemEventHandler
from threading import Timer
from src.handlers.log_handlers import ensure_csv_exists, log_event
from watchdog.events import FileSystemEvent
from src.config import settings
from email_handler import send_email

CSV_FILE_EXTENSION = ".csv"

# Load environment variables
smtp_server = settings.smtp_server
smtp_port = settings.smtp_port
smtp_user = settings.smtp_user
smtp_password = settings.smtp_password
sender_email = settings.sender_email
receiver_email = settings.receiver_email


class DebouncedEventHandler(
    FileSystemEventHandler,
):
    """
    A handler class to manage file system events with debouncing.

    Args:
        csv_file_path (str): The path to the CSV file for logging events.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(
        self,
        csv_file_path,
        *args,
        **kwargs,
    ):
        """
        Initialize the DebouncedEventHandler.

        Args:
            csv_file_path (str): The path to the CSV file for logging events.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.event_timers = {}
        self.csv_file_path = csv_file_path
        ensure_csv_exists(self.csv_file_path)

    def _debounce(self, event_type: str, event: FileSystemEvent):
        """
        Debounce the file system events to avoid handling the same
        event multiple times.

        Args:
            event_type (str): The type of the file system event.
            event (FileSystemEvent): The file system event object.

        Returns:
            None
        """
        if event.src_path in self.event_timers:
            self.event_timers[event.src_path].cancel()

        def handle_event():
            """
            Handle the debounced event by logging it and sending an email.

            Returns:
                None
            """
            if event.src_path.endswith(CSV_FILE_EXTENSION):
                log_event(self.csv_file_path, event_type, event.src_path)
                send_email(
                    event_type,
                    event.src_path,
                    settings.smtp_server,
                    settings.smtp_port,
                    settings.smtp_user,
                    settings.smtp_password,
                    settings.sender_email,
                    settings.receiver_email,
                )

            del self.event_timers[event.src_path]

        timer = Timer(0.5, handle_event)
        self.event_timers[event.src_path] = timer
        timer.start()

    def on_modified(self, event):
        """
        Handle the modified file system event.

        This method is called when a file or directory is modified.
        It debounces the event to avoid handling the same event multiple times.

        Args:
            event (FileSystemEvent): The file system event object.

        Returns:
            None
        """
        self._debounce("modified", event)

    def on_created(self, event):
        """
        Handle the created file system event.

        This method is called when a file or directory is created. It debounces
        the event to avoid handling the same event multiple times.

        Args:
            event (FileSystemEvent): The file system event object.

        Returns:
            None
        """
        self._debounce("created", event)

    def on_deleted(self, event):
        """
        Handle the deleted file system event.

        This method is called when a file or directory is deleted. It debounces
        the event to avoid handling the same event multiple times.

        Args:
            event (FileSystemEvent): The file system event object.

        Returns:
            None
        """
        self._debounce("deleted", event)
