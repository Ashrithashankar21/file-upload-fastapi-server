import time
from handlers.file_handlers import DebouncedEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver


def initialize_observer(
    folder_to_track: str,
    file_tracker: str,
) -> BaseObserver:
    """
    Initialize a file observer to monitor changes in a specified folder.

    Args:
        folder_to_track (str): The path to the folder to be monitored.
        file_tracker (str): The file tracker to be used for handling events.

    Returns:
        BaseObserver: An initialized observer object ready to start monitoring.
    """
    event_handler = DebouncedEventHandler(file_tracker)
    observer = Observer()
    observer.schedule(event_handler, folder_to_track, recursive=True)
    return observer


def start_observer(observer: BaseObserver) -> dict:
    """
    Start the file observer and keep it running.

    Args:
        observer (BaseObserver): The observer object to be started.

    Returns:
        dict: A dictionary containing the status message of the observer.
    """
    observer.start()
    try:
        while True:
            time.sleep(1)
            return {"message": "File Upload Tracker is running."}
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
