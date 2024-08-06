from watchdog.events import FileSystemEventHandler
from threading import Timer
from handlers.log_handlers import ensure_csv_exists, log_event
from handlers.mail_handlers import send_email

CSV_FILE_EXTENSION = ".csv"


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
                send_email(event_type, event.src_path)

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
