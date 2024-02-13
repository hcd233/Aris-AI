import time
from typing import Any, Dict

import streamlit as st
from streamlit import session_state as cache

from internal.webui.utils import get_embedding_info, get_embeddings, get_vector_db_info, get_vector_dbs, new_vector_db, upload_files

ABOUT = """\
### Alice AI是由lvlvko研发的大语言模型，提供api和webui服务
#### 技术栈
##### 模型微调:
- Transformers
- PEFT
- Pytorch
- Deepspeed
##### 模型部署:
- VLLM
- llama.cpp
##### 模型服务:
- Langchain
- Milvus
##### 后台API：
- Fastapi
- Sqlalchemy
- Mysql
- Redis
##### WebUI:
- Streamlit
##### 项目部署:
- Docker
- Kubernetes
- Traefik
"""


def init_webui():
    # init streamlit config
    st.set_page_config(
        page_title="Alice AI Knowledge Base",
        page_icon="🍃",
        layout="wide",  # "centered",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/hcd233",
            "Report a bug": "https://github.com/hcd233",
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

    st.subheader("Upload data to knowledge base")
    with st.form("upload_files"):
        files = st.file_uploader("Upload data", type=["txt", "md", "pdf", "html"], accept_multiple_files=True)
        embedding_id = cache.embedding_name_id_map.get(cache.embedding_name)
        info = get_embedding_info(cache.api_key, embedding_id)

        chunk_size, chunk_overlap = st.columns(2)
        chunk_size = chunk_size.number_input("Chunk Size", min_value=64, max_value=info.get("chunk_size") * 2, step=64)
        chunk_overlap = chunk_overlap.number_input("Chunk Overlap", min_value=0, max_value=info.get("chunk_size"), step=16)

        submit_onclick = st.form_submit_button("Submit")

    if submit_onclick:
        if chunk_size // 2 < chunk_overlap:
            st.error("Chunk Overlap should be less than half of Chunk Size")
            return
        if not files:
            st.error("No files uploaded")
            return
        upload_files(cache.api_key, cache.vector_db_id, files, chunk_size, chunk_overlap)
        st.success("Upload files success")


def main():
    init_webui()
    sidebar()
    body()


if __name__ == "__main__":
    main()
