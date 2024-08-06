from fastapi import APIRouter, status
from handlers.observer_handlers import initialize_observer, start_observer
from utils.load_env import get_env_variable

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
    folder_to_track = get_env_variable("FOLDER_TO_TRACK")
    file_tracker = get_env_variable("FILE_TRACKER")

    observer = initialize_observer(folder_to_track, file_tracker)
    return start_observer(observer)
