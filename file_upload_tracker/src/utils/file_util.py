import json
from pathlib import Path
from typing import List, Dict, Any
from src.config import settings
from log_events import log_event
from email_handler import send_email
import aiohttp
import asyncio
from src.utils.auth_util import get_access_token


def load_local_record(record_file_path: str) -> Dict[str, str]:
    """
    Loads a JSON record from a local file.

    Args:
        record_file_path (str): The path to the JSON file.

    Returns:
        Dict[str, str]: The JSON data as a dictionary if the file exists,
        otherwise an empty dictionary.
    """
    file_path = Path(record_file_path)

    if file_path.exists():
        with file_path.open("r") as file:
            return json.load(file)

    return {}


def save_local_record(record: Dict[str, str], record_file_path: str) -> None:
    """
    Saves a dictionary to a JSON file.

    Args:
        record (Dict[str, str]): The dictionary to save.
        record_file_path (str): The path to the JSON file.

    Returns:
        None
    """
    file_path = Path(record_file_path)

    with file_path.open("w") as file:
        json.dump(record, file, indent=4)


def save_changes_to_csv(
    changes: List[Dict[str, str]],
    record_file_path: str,
) -> None:
    """
    Processes a list of file system changes and updates the local record file.
    It also logs the events and sends email notifications for each change.

    Args:
        changes (List[Dict[str, str]]): A list of dictionaries representing
        changes in the file system. Each dictionary contains details about the
        change, such as:
            - "id" (str): The unique identifier for the item.
            - "changeType" (str): The type of change (e.g., "created",
                "updated", "deleted").
            - "name" (str): The name of the item affected by the change.
            - "deleted" (dict): A dictionary containing details about the
                deletion, if applicable. Contains a "state" key that indicates
                the deletion state.
        record_file_path (str): The path to the local CSV file where the record
                                of changes is stored.

    Returns:
        None: This does not return any value. It modifies the local record
        file and performs side effects such as logging and sending emails.

    Raises:
        FileNotFoundError: If the local record file cannot be found or
        accessed.
        json.JSONDecodeError: If the local record file contains invalid
        JSON data.

    Process:
        1. Loads the current local record from the specified file.
        2. Iterates through the list of changes:
            - Determines the change type (e.g., "created", "updated",
            "deleted").
            - Updates the local record based on the change type.
            - Logs the change event.
            - Sends an email notification about the change.
        3. Saves the updated local record back to the file.
    """
    local_record = load_local_record(record_file_path)

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

    save_local_record(local_record, record_file_path)


async def poll_changes(global_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Polls for changes using the delta link from global state and returns the
    changes.

    Args:
        global_state (Dict[str, Any]): A dictionary containing the global
        state including 'delta_link'.

    Returns:
        Dict[str, Any]: A dictionary with the changes or a message if no
        delta link is found.
    """
    delta_link = global_state.get("delta_link")
    if not delta_link:
        return {"message": "No delta link found. "}
    access_token = get_access_token(global_state)

    headers = {"Authorization": f"Bearer {access_token}"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(delta_link, headers=headers) as response:
                response.raise_for_status()
                delta_data = await response.json()
        except aiohttp.ClientError as e:
            return {"message": f"Request failed: {e}"}
        except ValueError:
            return {"message": "Failed to parse response JSON."}

    global_state["delta_link"] = delta_data["@odata.deltaLink"]
    changes = delta_data.get("value", [])
    return {"changes": changes}


async def save_changes(global_state: Dict[str, Any]) -> Dict[str, str]:
    """
    Polls for changes, saves the changes to a CSV file, and returns a
    success message.

    Args:
        global_state (Dict[str, Any]): A dictionary containing the
        global state, including the delta link and access token.

    Returns:
        Dict[str, str]: A dictionary containing a success message
        indicating that changes have been saved to CSV.

    Raises:
        HTTPException: If there is an issue with polling changes
        or saving to the CSV file.
    """
    try:
        changes = await poll_changes(global_state)
        save_changes_to_csv(
            changes.get("changes", []),
            settings.one_drive_record_file,
        )
        return {"message": "Changes saved to CSV"}
    except Exception as e:
        return {"message": f"Failed to save changes: {str(e)}"}


async def periodic_task(
    task_id: str, tasks: Dict[str, bool], global_state: Dict[str, Any]
) -> None:
    """
    Periodically performs a task while the task ID is active in the tasks
    dictionary.

    Args:
        task_id (str): The unique identifier for the task.
        tasks (Dict[str, bool]): A dictionary tracking the status of
        various tasks. The value is True if the task is active.
        global_state (Dict[str, Any]): A dictionary containing the global
        state needed for performing the task.

    Returns:
        None: This function does not return any value.
    """
    while tasks.get(task_id):
        try:
            await save_changes(global_state)
        except Exception as e:
            print(f"Error during task {task_id}: {e}")

        await asyncio.sleep(1)
