import requests
from fastapi import APIRouter, status, HTTPException, UploadFile, File
from src.handlers.observer_handlers import initialize_observer, start_observer
from src.config import settings
from datetime import datetime
import csv


router = APIRouter(tags=["Track File Changes"])
folder_path = "personal/ashritha_shankar_solitontech_com/Documents/onedrive\
-tracker"
one_drive_api_url = "https://graph.microsoft.com/v1.0"


# Helper function to get an access token
async def get_access_token():
    client_id = settings.client_id
    client_secret = settings.client_secret_id
    auth_url = settings.auth_url

    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }
    response = requests.post(auth_url, data=body, timeout=10)
    response.raise_for_status()
    return response.json()["access_token"]


# Endpoint to upload files to OneDrive
@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):

    access_token = await get_access_token()

    # Read the file
    contents = await file.read()

    # Prepare to upload
    upload_url = (
        f"{one_drive_api_url}/me/drive/root:/uplo\
ads/"
        f"{file.filename}:/content"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": file.content_type,
    }

    # Upload the file
    response = requests.put(
        upload_url,
        headers=headers,
        data=contents,
        timeout=10,
    )
    if response.status_code == 201:
        return {"message": "File uploaded successfully"}
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json(),
        )


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


def get_changes(access_token, folder_id):
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/delta"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def write_changes_to_csv(changes):
    one_drive_file_tracker = settings.one_drive_file_tracker

    with open(one_drive_file_tracker, "a", newline="") as file:
        writer = csv.writer(file)
        for change in changes.get("value", []):
            writer.writerow(
                [
                    datetime.now(),
                    change.get("id"),
                    change.get("name"),
                    change.get("deleted", False),
                ]
            )


def get_folder_id_by_path(access_token, folder_path):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{folder_path}"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()["id"]


@router.get("/track-for-one-drive/")
async def track_one_drive_changes():
    access_token = await get_access_token()
    folder_id = await get_folder_id_by_path(access_token, folder_path)
    changes = get_changes(access_token, folder_id)
    write_changes_to_csv(changes)
