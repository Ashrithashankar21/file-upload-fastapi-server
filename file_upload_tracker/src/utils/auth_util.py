from fastapi import HTTPException


def get_access_token(global_state: dict) -> str:
    access_token = global_state.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is missing")
    return access_token
