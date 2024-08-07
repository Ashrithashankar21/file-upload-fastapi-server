from fastapi import APIRouter, status
from src.handlers.observer_handlers import initialize_observer, start_observer
from src.config import settings

router = APIRouter(tags=["Track File Changes"])


@router.get("/", status_code=status.HTTP_200_OK)
def track_file_changes():
    """
     Endpoint to track file changes in a specified folder.

    This endpoint initializes a file observer to monitor changes in the folder
    specified by the environment variable "FOLDER_TO_TRACK" and uses the file
    tracker specified by the environment variable "FILE_TRACKER".

    Returns:
        dict: A dictionary containing the status of the observer.
    """
    folder_to_track = settings.FOLDER_TO_TRACK
    file_tracker = settings.FILE_TRACKER

    observer = initialize_observer(folder_to_track, file_tracker)
    return start_observer(observer)
