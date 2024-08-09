from fastapi import UploadFile, HTTPException
from src.config import settings
import httpx
from src.utils.auth_util import get_access_token
from log_events import ensure_csv_exists
import aiohttp
import asyncio
from src.utils.file_util import save_local_record, periodic_task

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


async def upload_file_to_one_drive(global_state: dict[str, None], file: UploadFile):
    access_token = get_access_token(global_state)
    file_content = await file.read()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/octet-stream",
    }

    user_id = "ashritha.shankar@solitontech.in"
    upload_url = f"{GRAPH_API_URL}/users/{user_id}/drive/root:/{settings.one_drive_folder_to_track}/{file.filename}:/content"

    async with httpx.AsyncClient() as client:
        response = await client.put(upload_url, headers=headers, content=file_content)

    if response.status_code == 201:
        return {"message": "File uploaded successfully"}
    elif response.status_code == 401:
        raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


async def track_file_changes(global_state: dict[str, None], tasks: dict):
    access_token = get_access_token(global_state)

    graph_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{settings.one_drive_folder_to_track}:/delta"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(graph_url, headers=headers) as response:
            if response.status == 401:
                raise HTTPException(status_code=401, detail="Unauthorized")
            delta_data = await response.json()

    global_state["delta_link"] = delta_data["@odata.deltaLink"]
    changes = delta_data.get("value", [])
    local_record = {}
    for change in changes:
        if change.get("changeType") != "deleted":
            local_record[change.get("id")] = change.get("name")

    ensure_csv_exists(settings.one_drive_file_tracker)
    save_local_record(local_record)
    global task_running
    task_id = "unique_task_id_for_this_endpoint"

    if task_id not in tasks:
        task_running = True
        tasks[task_id] = True
        asyncio.create_task(periodic_task(task_id, tasks, global_state))

    return {"message": "Tracking changes in OneDrive"}
