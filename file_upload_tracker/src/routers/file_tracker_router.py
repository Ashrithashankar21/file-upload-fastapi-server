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

REDIRECT_URL = "http://localhost:8000/callback"
SCOPES = "User.Read Files.Read Files.ReadWrite"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

authority = f"https://login.microsoftonline.com/{settings.tenant_id}"
token_url = f"https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/token"
scope = ["User.Read", "Files.Read", "Files.ReadWrite"]

msal_app = msal.PublicClientApplication(settings.client_id, authority=authority)


@router.on_event("shutdown")
async def shutdown_event():
    global tasks
    print("Shutting down server. Stopping all tasks...")
    for task_id in list(tasks.keys()):
        tasks[task_id] = False
    await asyncio.sleep(1)
    tasks.clear()
    print("All tasks stopped.")


@router.get("/authorize", tags=["Authorize"])
async def authorize():
    auth_url = msal_app.get_authorization_request_url(
        scopes=scope, redirect_uri=REDIRECT_URL
    )
    webbrowser.open(auth_url)
    return {"message": "Authorizing please wait..."}


@router.get("/callback", include_in_schema=False)
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")

    response = httpx.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URL,
            "client_id": settings.client_id,
            "client_secret": settings.client_secret_id,
            "scope": SCOPES,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    global_state["access_token"] = response.json()["access_token"]
    return {"message": "Authorization successful"}


@router.post("/upload-file", tags=["Upload File"])
async def upload_file(file: UploadFile = File(...)):
    return await upload_file_to_one_drive(global_state, file)


@router.get(
    "/track-local-file-changes",
    status_code=status.HTTP_200_OK,
    tags=["Track file changes"],
)
def track_local_file_changes():
    folder_to_track = settings.folder_to_track
    file_tracker = settings.file_tracker

    observer = initialize_observer(folder_to_track, file_tracker)
    return start_observer(observer)


@router.get(
    "/track-changes-in-one-drive",
    tags=["Track file changes"],
)
async def track_changes_in_one_drive():
    return await track_file_changes(global_state, tasks)
