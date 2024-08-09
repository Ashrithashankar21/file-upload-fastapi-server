import json
from pathlib import Path
from typing import List, Dict
from src.config import settings
from log_events import log_event
from email_handler import send_email
import aiohttp
import asyncio
from src.utils.auth_util import get_access_token


def load_local_record() -> Dict[str, str]:
    if Path(settings.one_drive_record_file).exists():
        with open(settings.one_drive_record_file, "r") as file:
            return json.load(file)
    return {}


def save_local_record(record: Dict[str, str]):
    with open(settings.one_drive_record_file, "w") as file:
        json.dump(record, file)


def save_changes_to_csv(changes: List[Dict[str, str]]):
    local_record = load_local_record()

    for change in changes:
        item_id = change.get("id", "unknown")
        change_type = change.get("deleted", {}).get("state") or change.get(
            "changeType", "updated" if item_id in local_record else "created"
        )
        item_name = change.get("name", "Unknown")

        if item_name.startswith(settings.one_drive_folder_to_track):
            continue

        if change_type == "deleted":
            item_name = local_record.pop(item_id, "Unknown")
        else:
            local_record[item_id] = item_name
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


async def poll_changes(global_state: dict[str, None]):
    delta_link = global_state.get("delta_link")
    access_token = get_access_token(global_state)
    if not delta_link:
        return {
            "message": "No delta link found. Start with /track-changes-in-one-drive."
        }

    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(delta_link, headers=headers) as response:
            delta_data = await response.json()

    global_state["delta_link"] = delta_data["@odata.deltaLink"]
    changes = delta_data.get("value", [])
    return {"changes": changes}


async def save_changes(global_state: dict[str, None]):

    changes = await poll_changes(global_state)
    save_changes_to_csv(changes.get("changes", []))
    return {"message": "Changes saved to CSV"}


async def periodic_task(task_id: str, tasks: dict, global_state: dict[str, None]):
    while tasks.get(task_id):
        await save_changes(global_state)
        await asyncio.sleep(1)
