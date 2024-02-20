from json import loads
from typing import Any, Dict, Iterator, List, Literal, Tuple
from urllib.parse import urljoin

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.config import API_HOST, API_PORT

API_URL = f"{API_HOST}:{API_PORT}"


def parse_response(response: requests.Response, action: str) -> Dict[str, Any]:
    action = action.title()

    if response.status_code != 200:
        st.error(f"{action} Error: ({response.status_code}){response.text}")
        st.stop()

    resp: Dict[str, Any] = response.json()

    if resp.get("status") != "success":
        st.error(f"{action} Status Error {resp.get('message')}")
        st.stop()

    data = resp.get("data")
    return data


def get_llms(api_key: str) -> List[str]:
    url = urljoin(API_URL, "v1/model/llm/llms")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, "get llms")

    llms = data.get("llm_list")
    llms = [llm.get("llm_name") for llm in llms]

    return llms


def get_embeddings(api_key: str) -> Dict[str, int]:
    url = urljoin(API_URL, "v1/model/embedding/embeddings")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, "get embeddings")

    embeddings = data.get("embedding_list")
    embeddings = {embedding.get("embedding_name"): embedding.get("embedding_id") for embedding in embeddings}

    return embeddings


def get_vector_dbs(api_key: str) -> Dict[str, int]:
    url = urljoin(API_URL, "v1/vector-db/vector-dbs")
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, "get vector dbs")

    llms = data.get("vector_db_list")
    llms = {llm.get("vector_db_name"): llm.get("vector_db_id") for llm in llms}
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


def get_history(api_key: str, session_id: int) -> Tuple[int, List[Dict[Literal["role", "content"], str]]]:
    url = urljoin(API_URL, f"v1/session/{session_id}")
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, f"get session {session_id}'s history")

    bind_llm, messages = data.get("bind_llm"), data.get("messages")
    messages = [{field: message["message"][field] for field in ("role", "content")} for message in messages]

    return bind_llm, messages


def get_vector_db_info(api_key: str, vector_db_id: int) -> Dict[str, Any]:
    url = urljoin(API_URL, f"v1/vector-db/{vector_db_id}")
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, f"get vector db {vector_db_id}'s info")

    for k, v in data.items():
        if isinstance(v, str):
            continue
        data[k] = str(v)
    return data


def get_embedding_info(api_key: str, embedding_id: int) -> Dict[str, Any]:
    url = urljoin(API_URL, f"v1/model/embedding/{embedding_id}")
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(
        url=url,
        headers=headers,
    )

    data = parse_response(response, f"get embedding {embedding_id}'s info")

    return data


def new_session(api_key: str) -> int:
    url = urljoin(API_URL, "v1/session")
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.post(
        url=url,
        headers=headers,
    )

    data = parse_response(response, "create chat session")

    return data.get("session_id")


def new_vector_db(api_key: str, vector_db_name: str, embedding_name: str, vector_db_description: str) -> int:
    url = urljoin(API_URL, "v1/vector-db")
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "vector_db_name": vector_db_name,
        "embedding_name": embedding_name,
        "vector_db_description": vector_db_description,
    }

    response = requests.post(
        url=url,
        headers=headers,
        json=data,
    )

    data = parse_response(response, "create vector db")

    return data.get("vector_db_id")


def upload_files(api_key: str, vector_db_id: int, files: List[UploadedFile], chunk_size: int, chunk_overlap: int) -> Dict[str, Any]:
    url = urljoin(API_URL, f"v1/vector-db/{vector_db_id}/files")
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }

    response = requests.put(
        url=url,
        headers=headers,
        params=params,
        files=[("files", (file.name, file.getvalue(), file.type)) for file in files],
    )

    data = parse_response(response, "upload files")
    return data


def upload_urls(api_key: str, vector_db_id: int, urls: str, chunk_size: int, chunk_overlap: int, url_type: str) -> Dict[str, Any]:
    url = urljoin(API_URL, f"v1/vector-db/{vector_db_id}/urls")
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "url_type": url_type,
    }

    response = requests.put(
        url=url,
        headers=headers,
        params=params,
        json=urls.split("\n"),
    )

    data = parse_response(response, "upload urls")
    return data


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


def retriever_qa(api_key: str, session_id: int, message: str, llm_name: str, temperature: float, vector_db_id: int):
    url = urljoin(API_URL, f"v1/session/{session_id}/retriever-qa")
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "message": message,
        "llm_name": llm_name,
        "temperature": temperature,
        "vector_db_id": vector_db_id,
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
