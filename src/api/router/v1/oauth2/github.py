from urllib.parse import urlencode

import requests
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from src.api.model.response import StandardResponse
from src.config.env import OAUTH2_GITHUB_CLIENT_ID, OAUTH2_GITHUB_CLIENT_SECRET
from src.config.gbl import OAUTH2_GITHUB_AUTH_URL, OAUTH2_GITHUB_REDIRECT_URL, OAUTH2_GITHUB_TOKEN_URL, OAUTH2_GITHUB_USER_API

from .common import login

github_router = APIRouter(prefix="/github", tags=["oauth2"])


@github_router.get("/login")
async def github_login() -> StandardResponse:
    query = {
        "client_id": OAUTH2_GITHUB_CLIENT_ID,
        "redirect_uri": OAUTH2_GITHUB_REDIRECT_URL,
        "scope": "user",
    }
    return StandardResponse(
        code=1,
        status="success",
        data={"url": f"{OAUTH2_GITHUB_AUTH_URL}?{urlencode(query)}"},
    )


@github_router.get("/callback")
async def github_callback(code: str) -> JSONResponse:
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")

    query = {
        "client_id": OAUTH2_GITHUB_CLIENT_ID,
        "client_secret": OAUTH2_GITHUB_CLIENT_SECRET,
        "code": code,
    }
    headers = {"Accept": "application/json"}
    response = requests.post(OAUTH2_GITHUB_TOKEN_URL, data=query, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to retrieve access token")

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Access token is missing in response")

    # Use the access token to get user info
    user_response = requests.get(OAUTH2_GITHUB_USER_API, headers={"Authorization": f"Bearer {access_token}"})

    if user_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to retrieve user information")

    user_data = user_response.json()
    token = login(user_data["login"], user_data["id"], user_data["avatar_url"], "github")
    return StandardResponse(
        code=1,
        status="success",
        data={"token": token},
    )
