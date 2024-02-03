from json import loads
from typing import Any, Dict, Iterator, List, Literal
from urllib.parse import urljoin

import requests
import streamlit as st

from internal.config import API_HOST, API_PORT

API_URL = f"{API_HOST}:{API_PORT}"


def parse_response(response: requests.Response, action: str) -> Dict[str, Any]:
    action = action.title()

    if response.status_code != 200:
        st.error(f"{action} Error: ({response.status_code}){response.text}")
        st.stop()

    resp: Dict[str, Any] = response.json()

    if resp.get("status") != "success":
        st.error(f"{action} Status Error {response.get('message')}")
        st.stop

    data = resp.get("data")
    return data


def get_llms(api_key: str) -> List[str]:
    url = urljoin(API_URL, "v1/model/llms")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, "get llms")

    llms = data.get("llm_list")
    llms = [llm.get("llm_name") for llm in llms]

    return llms


def get_sessions(
    api_key: str,
    page_id: int = 0,
    per_page_num: int = 20,
) -> List[str]:
    url = urljoin(API_URL, "v1/session/sessions")
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"page_id": page_id, "per_page_num": per_page_num}
    response = requests.get(
        url=url,
        headers=headers,
        params=params,
    )

    data = parse_response(response, "get sessions")

    sessions = data.get("session_list")
    sessions = [session.get("session_id") for session in sessions]

    return sessions


def get_history(api_key: str, session_id: int) -> List[Dict[Literal["role", "content"], str]]:
    url = urljoin(API_URL, f"v1/session/{session_id}")
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, f"get session {session_id}'s history")

    messages = data.get("messages")
    messages = [{field: message["message"][field] for field in ("role", "content")} for message in messages]

    return messages


def chat(api_key: str, session_id: int, message: str, llm_name: str, temperature: float) -> Iterator[str]:
    url = urljoin(API_URL, f"v1/session/{session_id}/chat")
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "message": message,
        "llm_name": llm_name,
        "temperature": temperature,
    }

    response = requests.post(
        url=url,
        headers=headers,
        json=data,
        stream=True,
    )

    for chunk in response.iter_lines():
        if not chunk:
            continue
        chunk = loads(chunk.decode("utf-8"))
        yield chunk.get("delta", "")
