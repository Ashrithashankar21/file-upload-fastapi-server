import time
import os
from fastapi import APIRouter, status
from handlers import handlers
from watchdog.observers import Observer


router = APIRouter(tags=["Track File Changes"])


@router.get("/", status_code=status.HTTP_200_OK)
def track_file_changes():

    folder_to_track = os.getenv("FOLDER_TO_TRACK")
    file_tracker = os.getenv("FILE_TRACKER")

    if not folder_to_track:
        raise ValueError(
            "Environment variable FOLDER_TO_TRACK\
 is not set or is empty."
        )

    if not file_tracker:
        raise ValueError(
            "Environment variable FILE_TRACKER\
 is not set or is empty."
        )

    path = folder_to_track
    event_handler = handlers.DebouncedEventHandler(file_tracker)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            return {"message": "File Upload Tracker is running."}
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
