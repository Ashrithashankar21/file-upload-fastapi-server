from fastapi import UploadFile, HTTPException, status
from src.config import settings
import httpx
from src.utils.auth_util import get_access_token
from log_events import ensure_csv_exists
import aiohttp
import asyncio
from src.utils.file_util import save_local_record, periodic_task
from typing import Dict, Any

graph_api_base_url = "https://graph.microsoft.com/v1.0"
folder_path = f"{settings.one_drive_folder_to_track}"
graph_url = f"{graph_api_base_url}/me/drive/root:/{folder_path}:/delta"


async def upload_file_to_one_drive(
    global_state: Dict[str, None], file: UploadFile
) -> Dict[str, str]:
    """
    Uploads a file to OneDrive.

    Args:
        global_state (dict[str, None]): A dictionary containing global state,
        including access token.
        file (UploadFile): The file to be uploaded.

    Returns:
        dict[str, str]: A dictionary with a success message.

    Raises:
        HTTPException: If there is an issue with uploading the file or
        unauthorized access.
    """
    access_token = get_access_token(global_state)
    file_content = await file.read()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }
    user_id = settings.one_drive_folder_user_id
    upload_url = (
        f"{graph_api_base_url}/users/{user_id}/drive/root:"
        f"/{folder_path}/{file.filename}:/content"
    )

    async with httpx.AsyncClient() as client:
        response = await client.put(
            upload_url,
            headers=headers,
            content=file_content,
        )

    if response.status_code == status.HTTP_201_CREATED:
        return {"message": "File uploaded successfully"}
    elif response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.text,
        )


async def fetch_delta_data(
    graph_url: str,
    access_token: str,
) -> Dict[str, Any]:
    """
    Fetches delta data from the specified OneDrive API endpoint using the
    provided access token.

    Args:
        graph_url (str): The URL to the OneDrive API endpoint for fetching
        delta changes.
        access_token (str): The access token for authenticating the request.

    Returns:
        Dict[str, Any]: The JSON response from the OneDrive API as a
        dictionary.

    Raises:
        HTTPException: If the request fails with a 401 Unauthorized
        status, indicating an authentication error.

    Notes:
        - The function uses an `Authorization` header with the Bearer
        token for authentication.
        - If the response status is 401, an `HTTPException` is raised
        to handle unauthorized access.
        - The function will return the JSON response parsed into a
        dictionary for further processing.
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(graph_url, headers=headers) as response:
            if response.status == status.HTTP_401_UNAUTHORIZED:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized",
                )
            return await response.json()


async def track_file_changes(
    global_state: Dict[str, None],
    tasks: Dict[str, bool],
) -> Dict[str, str]:
    """
    Tracks file changes in OneDrive by fetching delta data and updating
    the local record.

    Args:
        global_state (Dict[str, None]): A dictionary containing global state
        information, including access tokens and delta links.
        tasks (Dict[str, bool]): A dictionary tracking active tasks. The value
        is True if the task is active.

    Returns:
        Dict[str, str]: A dictionary with a message indicating that OneDrive
        changes are being tracked.

    Raises:
        HTTPException: If an error occurs while fetching delta data or if the
        access token is invalid.

    Process:
        1. Retrieves the access token from the global state.
        2. Fetches delta data from the OneDrive API using the access token.
        3. Updates the global state with the new delta link.
        4. Processes the list of changes:
            - Ignores deleted items.
            - Updates the local record with the names of created or modified
            items.
        5. Ensures the local CSV file for tracking is created.
        6. Saves the updated local record to the file.
        7. Checks if a periodic task is already running; if not, starts a new
        periodic task.
        8. Returns a message indicating that tracking has started.

    Notes:
        - This function manages file tracking by creating or updating a
        periodic task that continuously polls for changes.
        - The global variable `task_running` is used to ensure that only one
        periodic task is running at a time.
        - `fetch_delta_data` should handle HTTP errors and parsing issues,
        ensuring robust error management.
    """
    access_token = get_access_token(global_state)

    delta_data = await fetch_delta_data(graph_url, access_token)

    global_state["delta_link"] = delta_data["@odata.deltaLink"]
    changes = delta_data.get("value", [])
    local_record = {}
    for change in changes:
        if change.get("changeType") != "deleted":
            local_record[change.get("id")] = change.get("name")

    ensure_csv_exists(settings.one_drive_file_tracker)
    save_local_record(local_record, settings.one_drive_record_file)
    global task_running
    task_id = "unique_task_id"

    if task_id not in tasks:
        task_running = True
        tasks[task_id] = True
        asyncio.create_task(periodic_task(task_id, tasks, global_state))

    return {"message": "Tracking changes in OneDrive"}
