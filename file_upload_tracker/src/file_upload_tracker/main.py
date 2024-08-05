import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
import os
from dotenv import load_dotenv

CSV_FILE_EXTENSION = ".csv"

load_dotenv()

folder_to_track = os.getenv("FOLDER_TO_TRACK")

if not folder_to_track:
    raise ValueError("Environment variable MY_FILE_PATH is not set or is empty.")


class DebouncedEventHandler(FileSystemEventHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_timers = {}

    def _debounce(self, event_type, event):
        if event.src_path in self.event_timers:
            self.event_timers[event.src_path].cancel()

        def handle_event():
            if event.src_path.endswith(CSV_FILE_EXTENSION):
                print(f"File {event_type}: {event.src_path}")
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


if __name__ == "__main__":
    path = folder_to_track
    event_handler = DebouncedEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
