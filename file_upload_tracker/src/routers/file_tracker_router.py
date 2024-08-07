from fastapi import APIRouter, status
from src.handlers.observer_handlers import initialize_observer, start_observer
from src.config import settings

router = APIRouter(tags=["Track File Changes"])


@router.get("/", status_code=status.HTTP_200_OK)
def track_file_changes():
    """
     Endpoint to track file changes in a specified folder.

    This endpoint initializes a file observer to monitor changes in the folder
    specified by the environment variable "folder_to_track" and uses the file
    tracker specified by the environment variable "file_tracker".

    Returns:
        dict: A dictionary containing the status of the observer.
    """
    folder_to_track = settings.folder_to_track
    file_tracker = settings.file_tracker

    observer = initialize_observer(folder_to_track, file_tracker)
    return start_observer(observer)
