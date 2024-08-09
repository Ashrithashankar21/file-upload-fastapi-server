from fastapi import (
    APIRouter,
    status,
    HTTPException,
    UploadFile,
    File,
    Request,
)
from src.handlers.observer_handlers import initialize_observer, start_observer
from src.config import settings
import msal
import httpx
import webbrowser
from src.handlers.one_drive_file_handler import (
    upload_file_to_one_drive,
    track_file_changes,
)
import asyncio

router = APIRouter()

tasks = {}
task_running = False
global_state = {"access_token": None, "delta_link": None}

redirect_url = "http://localhost:8000/callback"
base_url = f"https://login.microsoftonline.com/{settings.tenant_id}"
token_url = f"{base_url}/oauth2/v2.0/token"
scopes = "User.Read Files.Read Files.ReadWrite"
scope = ["User.Read", "Files.Read", "Files.ReadWrite"]

msal_app = msal.PublicClientApplication(
    settings.client_id,
    authority=base_url,
)


@router.on_event("shutdown")
async def shutdown_event():
    """
    Event handler for server shutdown. Stops all ongoing tasks and clears
    the task list.
    """
    global tasks
    print("Shutting down server. Stopping all tasks...")
    for task_id in list(tasks.keys()):
        tasks[task_id] = False
    await asyncio.sleep(1)
    tasks.clear()
    print("All tasks stopped.")


@router.get("/authorize", tags=["Authorize"])
async def authorize():
    """
    Initiates the OAuth2 authorization flow by redirecting the user
    to the Microsoft login page.

    Returns:
        dict: A message indicating that authorization is in progress.
    """
    authentication_url = msal_app.get_authorization_request_url(
        scopes=scope, redirect_uri=redirect_url
    )
    webbrowser.open(authentication_url)
    return {"message": "Authorizing please wait..."}


@router.get("/callback", include_in_schema=False)
async def callback(request: Request):
    """
    Handles the OAuth2 callback. Exchanges the authorization code for
    an access token.

    Args:
        request (Request): The incoming request containing the
        authorization code.

    Returns:
        dict: A message indicating that authorization was successful.

    Raises:
        HTTPException: If the authorization code is missing or the
        token request fails.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code missing",
        )

    response = httpx.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_url,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret_id,
            "scope": scopes,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    global_state["access_token"] = response.json()["access_token"]
    return {"message": "Authorization successful"}


@router.post("/upload-file", tags=["Upload File"])
async def upload_file(file: UploadFile = File(...)):
    """
    Uploads a file to OneDrive.

    Args:
        file (UploadFile): The file to be uploaded.

    Returns:
        dict: A message indicating whether the file upload was
        successful or not.
    """
    return await upload_file_to_one_drive(global_state, file)


@router.get(
    "/track-local-file-changes",
    status_code=status.HTTP_200_OK,
    tags=["Track file changes"],
)
def track_local_file_changes():
    """
    Initializes and starts an observer to track local file changes.

    Returns:
        dict: A message indicating that local file changes tracking
        has started.
    """
    folder_to_track = settings.folder_to_track
    file_tracker = settings.file_tracker

    observer = initialize_observer(folder_to_track, file_tracker)
    return start_observer(observer)


@router.get(
    "/track-changes-in-one-drive",
    tags=["Track file changes"],
)
async def track_changes_in_one_drive():
    """
    Tracks changes in OneDrive by fetching the delta data
    and updating the local record.

    Returns:
        dict: A message indicating that OneDrive changes
        tracking has started.
    """
    return await track_file_changes(global_state, tasks)
