import time
from typing import Any, Dict

import streamlit as st
from streamlit import session_state as cache

from src.webui.utils import get_embedding_info, get_embeddings, get_vector_db_info, get_vector_dbs, new_vector_db, upload_files, upload_urls

ABOUT = """\
### Alice AI is a project of providing private llm api and webui service
#### Author: [hcd233](https://github.com/hcd233)
#### Tech Stack
##### LLM fine-tuning:
- Transformers
- PEFT
- Pytorch
- Deepspeed
##### LLM deployment:
- llama.cpp
- llama-cpp-python
##### LLM service:
- Langchain
- FAISS
##### API backend:
- Fastapi
- Sqlalchemy
- Mysql
- Redis
##### WebUI:
- Streamlit
##### Project deployment:
- Docker
"""


def init_webui():
    # init streamlit config
    st.set_page_config(
        page_title="Alice AI Knowledge Base",
        page_icon="🍃",
        layout="wide",  # "centered",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/hcd233/Alice-AI/README.md",
            "Report a bug": "https://github.com/hcd233/Alice-AI/issues/new",
            "About": ABOUT,
        },
    )

    # init cache
    vars: Dict[str, Any] = {
        "api_key": "",
        "vector_db_id": 0,
        "vector_db_name": "",
        "embedding_id": 0,
        "embedding_name": "",
        "embedding_name_id_map": {},
    }

    for var, def_val in vars.items():
        if not hasattr(cache, var):
            setattr(cache, var, def_val)


def sidebar():
    st.sidebar.title("Alice AI")
    cache.api_key = st.sidebar.text_input("Alice Api Key", max_chars=100, type="password", value=cache.api_key)
    cache.embedding_name_id_map = get_embeddings(cache.api_key)

    with st.sidebar.expander("Menu"):
        st.page_link("pages/chat.py", label="Chat", icon="💬")
        st.page_link("pages/vector_db.py", label="Knowledge Base", icon="📚")

    st.sidebar.header("VectorStore")
    vector_stores = get_vector_dbs(cache.api_key)

    cache.vector_db_name = st.sidebar.selectbox(
        "Select vector store", options=list(vector_stores.keys()), index=None, placeholder="Create vector store"
    )
    cache.vector_db_id = vector_stores.get(cache.vector_db_name)
    if not cache.vector_db_id:
        return
    st.sidebar.subheader(f"{cache.vector_db_name}'s Info")
    info = get_vector_db_info(cache.api_key, cache.vector_db_id)
    cache.embedding_name = info.get("embedding_name")
    st.sidebar.dataframe(info, use_container_width=True)


def body():
    st.header("Knowledge Base")
    if not cache.vector_db_id:
        st.subheader("Create a new knowledge base")
        with st.form("create_vector_db"):
            name_input, bind_embedding = st.columns(2)
            vector_db_name = name_input.text_input("Name", max_chars=25)
            cache.embedding_name = bind_embedding.selectbox("Embedding Model", options=cache.embedding_name_id_map.keys())

            vector_db_description = st.text_area("Description", max_chars=500)
            submit_onclick = st.form_submit_button("Submit")

        if submit_onclick:
            cache.vector_db_id = new_vector_db(cache.api_key, vector_db_name, cache.embedding_name, vector_db_description)
            st.success(f"Create vector store {vector_db_name} success, vector store id: {cache.vector_db_id}")
            time.sleep(1)
            st.rerun()
        return

    upload_header, upload_type = st.columns(2)
    upload_header.subheader("Upload data to knowledge base")
    upload_type = upload_type.selectbox("Upload Type", options=["file", "url"])
    if upload_type == "file":
        with st.form("upload_files"):
            files = st.file_uploader("Upload files", type=["txt", "md", "pdf", "html"], accept_multiple_files=True)
            embedding_id = cache.embedding_name_id_map.get(cache.embedding_name)
            info = get_embedding_info(cache.api_key, embedding_id)

            chunk_size, chunk_overlap = st.columns(2)
            chunk_size = chunk_size.number_input("Chunk Size", min_value=64, max_value=info.get("chunk_size") * 2, step=64)
            chunk_overlap = chunk_overlap.number_input("Chunk Overlap", min_value=0, max_value=info.get("chunk_size"), step=16)

            upload_func = upload_files
            upload_args = dict(
                api_key=cache.api_key,
                vector_db_id=cache.vector_db_id,
                files=files,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            submit_onclick = st.form_submit_button("Submit")

    elif upload_type == "url":
        with st.form("upload_urls"):
            urls = st.text_area("Urls", max_chars=1000, help="One url per line")
            embedding_id = cache.embedding_name_id_map.get(cache.embedding_name)
            info = get_embedding_info(cache.api_key, embedding_id)

            chunk_size, chunk_overlap, url_type = st.columns(3)
            chunk_size = chunk_size.number_input("Chunk Size", min_value=64, max_value=info.get("chunk_size") * 2, step=64)
            chunk_overlap = chunk_overlap.number_input("Chunk Overlap", min_value=0, max_value=info.get("chunk_size"), step=16)
            url_type = url_type.selectbox("Url Type", options=["arxiv", "single", "recursive"])

            upload_func = upload_urls
            upload_args = dict(
                api_key=cache.api_key,
                vector_db_id=cache.vector_db_id,
                urls=urls,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                url_type=url_type,
            )

            submit_onclick = st.form_submit_button("Submit")

    else:
        st.error("Invalid upload type")
        return

    if submit_onclick:
        if chunk_size // 2 < chunk_overlap:
            st.error("Chunk Overlap should be less than half of Chunk Size")
            return

        if upload_type == "file" and not files:
            st.error(f"No {upload_type} uploaded")
            return

        if upload_type == "url" and not urls:
            st.error(f"No {upload_type} input")
            return

        data = upload_func(**upload_args)
        st.success(f"Upload {upload_type} success\n\nInfo: {data}")
        time.sleep(1)


def main():
    init_webui()
    sidebar()
    body()


if __name__ == "__main__":
    main()
