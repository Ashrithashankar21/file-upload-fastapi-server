from fastapi import HTTPException, status
from typing import Dict


def get_access_token(global_state: Dict[str, str]) -> str:
    """
    Retrieves the access token from the global state.

    Args:
        global_state (Dict[str, str]): A dictionary containing the global state.

    Returns:
        str: The access token if present.

    Raises:
        HTTPException: If the access token is not found in the global state.
    """
    access_token = global_state.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is missing"
        )
    return access_token
