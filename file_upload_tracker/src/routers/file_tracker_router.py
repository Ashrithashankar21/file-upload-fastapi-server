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
from fastapi.responses import RedirectResponse
import msal
import httpx
import webbrowser
import aiohttp
from typing import List, Dict
import json
from pathlib import Path
from log_events import ensure_csv_exists, log_event
from email_handler import send_email

router = APIRouter(tags=["Track File Changes"])


REDIRECT_URL = "http://localhost:8000/callback"
SCOPES = "User.Read Files.Read Files.ReadWrite"
AUTHORIZATION_BASE_URL = (
    f"https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/authorize"
)
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

authority = f"https://login.microsoftonline.com/{settings.tenant_id}"
scope = ["User.Read", "Files.Read", "Files.ReadWrite"]

msal_app = msal.PublicClientApplication(settings.client_id, authority=authority)

FOLDER_NAME = "one-drive-tracker"


@router.get("/authorize")
async def authorize():
    auth_url = msal_app.get_authorization_request_url(
        scopes=scope, redirect_uri=REDIRECT_URL
    )
    webbrowser.open(auth_url)  # Open in browser
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing")
    token_url = (
        f"https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/token"
    )
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
    return response.json()["access_token"]


@router.post(
    "/upload-file",
)
async def upload_file(access_token: str, file: UploadFile = File(...)):
    file_content = await file.read()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }

    user_id = "ashritha.shankar@solitontech.in"
    upload_url = f"{GRAPH_API_URL}/users/{user_id}/drive/root:/one-drive-tracker/{file.filename}:/content"

    async with httpx.AsyncClient() as client:
        response = await client.put(upload_url, headers=headers, content=file_content)

    if response.status_code == 201:
        return {"message": "File uploaded successfully"}
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


@router.get("/track-local-file-changes", status_code=status.HTTP_200_OK)
def track_local_file_changes():
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


LOCAL_RECORD_FILE = "C:/Users/ashritha.shankar/Documents/onedrive-data.csv"


def load_local_record() -> Dict[str, str]:
    """Load the local record of file names and IDs."""
    if Path(LOCAL_RECORD_FILE).exists():
        with open(LOCAL_RECORD_FILE, "r") as file:
            return json.load(file)
    return {}


def save_local_record(record: Dict[str, str]):
    """Save the local record of file names and IDs."""
    with open(LOCAL_RECORD_FILE, "w") as file:
        json.dump(record, file)


def save_changes_to_csv(changes: List[Dict[str, str]]):
    """Save changes to a CSV file."""
    local_record = load_local_record()

    for change in changes:
        item_id = change.get("id", "unknown")
        change_type = change.get("deleted", {}).get("state") or change.get(
            "changeType", "updated" if item_id in local_record else "created"
        )
        item_name = change.get("name", "Unknown")

        if item_name.startswith(FOLDER_NAME):
            continue

        if change_type == "deleted":
            item_name = local_record.pop(item_id, "Unknown")
        else:
            local_record[item_id] = item_name
        print(f"{change_type}: {item_name}")
        log_event(settings.one_drive_file_tracker, change_type, item_name)
        send_email(
            change_type,
            item_name,
            settings.smtp_server,
            settings.smtp_port,
            settings.smtp_user,
            settings.smtp_password,
            settings.sender_email,
            settings.receiver_email,
        )

    save_local_record(local_record)


@router.get("/track-changes-in-one-drive")
async def track_changes_in_one_drive(request: Request, access_token: str):

    graph_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{FOLDER_NAME}:/delta"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(graph_url, headers=headers) as response:
            delta_data = await response.json()

    request.session["delta_link"] = delta_data["@odata.deltaLink"]
    changes = delta_data.get("value", [])
    local_record = {}
    for change in changes:
        if change.get("changeType") != "deleted":
            local_record[change.get("id")] = change.get("name")

    ensure_csv_exists(settings.one_drive_file_tracker)
    save_local_record(local_record)
    return {"changes": changes}


async def poll_changes(request: Request, access_token: str):
    delta_link = request.session.get("delta_link")
    if not delta_link:
        return {"message": "No delta link found. Start with /track-changes."}

    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(delta_link, headers=headers) as response:
            delta_data = await response.json()

    request.session["delta_link"] = delta_data["@odata.deltaLink"]
    changes = delta_data.get("value", [])
    return {"changes": changes}


@router.get("/save-changes")
async def save_changes(request: Request, access_token: str):
    changes = await poll_changes(request, access_token)
    save_changes_to_csv(changes.get("changes", []))
    return {"message": "Changes saved to CSV"}
