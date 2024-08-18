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
from src.handlers.one_drive_file_handlers import (
    upload_file_to_one_drive,
    track_file_changes,
)
import asyncio
import requests
import json
import os
import pandas as pd


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
    for task_id in list(tasks.keys()):
        tasks[task_id] = False
    await asyncio.sleep(1)
    tasks.clear()


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
    print(file)
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


def download_file(file_id, filename, access_token):
    print("Downloading file:", filename)
    headers = {"Authorization": f"Bearer {access_token}"}
    file_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/content"
    file_extension = filename.split(".")[-1].lower()

    # Define the output file path
    local_file_path = os.path.join(
        "C:/Users/ashritha.shankar/Documents/one-drive-files", filename
    )

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

    # Download the file
    response = requests.get(file_url, headers=headers, stream=True)
    response.raise_for_status()

    # Save the file to local path
    with open(local_file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Convert XLSX to CSV if needed
    if file_extension == "xlsx":
        print("Converting XLSX to CSV:", filename)
        # Convert XLSX to temporary CSV
        temp_csv_path = os.path.splitext(local_file_path)[0] + ".csv"
        df = pd.read_excel(local_file_path)
        df.to_csv(temp_csv_path, index=False)

        # Inline check for headers
        expected_headers = [
            "employee_number",
            "employee_name",
            "python",
            "react",
            "angular",
            "c#",
            "labview",
        ]

        with open(temp_csv_path, "r") as f:
            header_row = f.readline().strip()
            print("0", header_row)

        headers = header_row.split(",")

        print("1", headers)
        if headers == expected_headers:
            print("3", expected_headers)
            # If headers are correct, keep the CSV file and remove the XLSX
            os.remove(local_file_path)
        else:
            # If headers are incorrect, remove the temporary CSV file
            print("2", expected_headers)

            os.remove(temp_csv_path)
            print(
                f"Skipped converting {filename} as it does not have the expected headers."
            )
    elif file_extension == "csv":
        # Inline check for headers
        expected_headers = [
            "employee_number",
            "employee_name",
            "python",
            "react",
            "angular",
            "c#",
            "labview",
        ]

        with open(local_file_path, "r") as f:
            header_row = f.readline().strip()

        headers = header_row.split(",")

        if headers != expected_headers:
            # If headers are incorrect, remove the CSV file
            os.remove(local_file_path)


def fetch_onedrive_data(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    graph_api_base_url = "https://graph.microsoft.com/v1.0"
    folder_path = f"{settings.one_drive_folder_to_track}"
    graph_url = f"{graph_api_base_url}/me/drive/root:/{folder_path}:/children"

    response = requests.get(graph_url, headers=headers)
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    data = response.json()
    if "value" in data:
        # Extract file names and IDs
        files_info = {item["id"]: item["name"] for item in data["value"]}

        # Save the data to a JSON file
        with open(settings.one_drive_database, "w") as f:
            json.dump(files_info, f, indent=4)

        return files_info
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No files found or invalid response format.",
        )


@router.get("/download-file")
async def download_files():
    fetch_onedrive_data(global_state["access_token"])
    with open(settings.one_drive_database, "r") as file:
        data = json.load(file)

    file_ids = list(data.keys())
    file_names = list(data.values())

    for file_id, file_name in zip(file_ids, file_names):
        if file_name.endswith(".csv") or file_name.endswith(".xlsx"):
            download_file(file_id, file_name, global_state["access_token"])
