import time
from handlers.file_handlers import DebouncedEventHandler
from watchdog.observers import Observer


def initialize_observer(folder_to_track, file_tracker):
    event_handler = DebouncedEventHandler(file_tracker)
    observer = Observer()
    observer.schedule(event_handler, folder_to_track, recursive=True)
    return observer


def start_observer(observer):
    observer.start()
    try:
        while True:
            time.sleep(1)
            return {"message": "File Upload Tracker is running."}
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
