from fastapi import UploadFile, HTTPException
from src.config import settings
import httpx

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


async def upload_file_to_one_drive(
    access_token: str, file: UploadFile, file_content: bytes
):
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
