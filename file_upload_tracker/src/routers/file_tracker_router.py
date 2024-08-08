import requests
from fastapi import APIRouter, status, HTTPException, UploadFile, File, Depends, Request
from src.handlers.observer_handlers import initialize_observer, start_observer
from src.config import settings
from datetime import datetime
import csv
from fastapi.responses import RedirectResponse
import msal
import httpx
import webbrowser

router = APIRouter(tags=["Track File Changes"])


folder_path = "personal/ashritha_shankar_solitontech_in/Documents/one-drive-tracker"
REDIRECT_URL = "http://localhost:8000/callback"
SCOPES = "User.Read Files.Read Files.ReadWrite"
AUTHORIZATION_BASE_URL = (
    f"https://login.microsoftonline.com/{settings.tenant_id}/oauth2/v2.0/authorize"
)
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

authority = f"https://login.microsoftonline.com/{settings.tenant_id}"
scope = ["User.Read", "Files.Read", "Files.ReadWrite"]

msal_app = msal.PublicClientApplication(settings.client_id, authority=authority)


@router.get("/authorize/")
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
    "/upload/",
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
