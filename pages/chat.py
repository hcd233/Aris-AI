from typing import Any, Dict

import streamlit as st
from streamlit import session_state as cache

from src.webui.utils import chat, get_history, get_llms, get_sessions, get_vector_dbs, new_session, retriever_qa

ABOUT = """\
### Aris AI is a project of providing private llm api and webui service
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
        page_title="Aris AI Chat",
        page_icon="🍃",
        layout="wide",  # "centered",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/hcd233/Aris-AI/README.md",
            "Report a bug": "https://github.com/hcd233/Aris-AI/issues/new",
            "About": ABOUT,
        },
    )

    # init cache
    vars: Dict[str, Any] = {
        "api_key": "",
        "llm": "",
        "temperature": 0.7,
        "session_id": 0,
        "session_list": [],
        "history": [],
        "bind_llm": None,
        "vector_db_id": 0,
    }

    for var, def_val in vars.items():
        if not hasattr(cache, var):
            setattr(cache, var, def_val)


def sidebar():
    st.sidebar.title("Aris AI")
    cache.api_key = st.sidebar.text_input("Aris Api Key", max_chars=100, type="password", value=cache.api_key)

    with st.sidebar.expander("Menu"):
        st.page_link("pages/chat.py", label="Chat", icon="💬")
        st.page_link("pages/vector_db.py", label="Knowledge Base", icon="📚")

    if not cache.session_list:
        cache.session_list = get_sessions(cache.api_key)
    st.sidebar.header("Sessions")
    cache.session_id = st.sidebar.selectbox("Select session", options=cache.session_list)

    new_session_onclick = st.sidebar.button("New Chat", key="new_chat")
    if new_session_onclick:
        cache.session_id = new_session(cache.api_key)
        st.success(f"New session created: {cache.session_id}")
        cache.session_list = []
        st.rerun()

    if cache.session_id:
        cache.bind_llm, cache.history = get_history(cache.api_key, cache.session_id)

    st.sidebar.header("LLMs")
    llms = get_llms(cache.api_key)
    if cache.bind_llm:
        st.sidebar.info(f"Bind LLM: {cache.bind_llm}")
        llms = [cache.bind_llm]
    cache.llm = st.sidebar.selectbox("Select llm", options=llms, disabled=cache.bind_llm is not None)

    st.sidebar.header("VectorStore")
    vector_stores = get_vector_dbs(cache.api_key)

    vector_db_name = st.sidebar.selectbox("Select vector store", options=list(vector_stores.keys()), index=None, placeholder="Without vector store")
    cache.vector_db_id = vector_stores.get(vector_db_name)

    st.sidebar.header("Temperature")
    cache.temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05)


def body():
    if not cache.session_id:
        st.info("Please create or select a session")
        return
    container = st.container(height=700, border=False)
    for message in cache.history:
        role, content = message.get("role"), message.get("content")
        if role == "human":
            container.chat_message(name=role).write(content)
        elif role == "ai":
            container.chat_message(name=role).markdown(content)
    prompt = st.chat_input(f"Chat with {cache.llm}", max_chars=8192)
    if prompt and prompt.strip():
        container.chat_message("human").write(prompt)

        # NOTE: this is may occur display problem
        # container.chat_message("ai").write_stream(
        #     stream=chat(
        #         api_key=cache.api_key,
        #         session_id=cache.session_id,
        #         llm_name=cache.llm,
        #         message=prompt,
        #         temperature=cache.temperature,
        #     )
        # )

        with container.chat_message("ai"):
            resp = ""
            place_holder = st.empty()
            if not cache.vector_db_id:
                for token in chat(
                    api_key=cache.api_key,
                    session_id=cache.session_id,
                    llm_name=cache.llm,
                    message=prompt,
                    temperature=cache.temperature,
                ):
                    resp += token
                    place_holder.markdown(resp)
            else:
                for token in retriever_qa(
                    api_key=cache.api_key,
                    session_id=cache.session_id,
                    llm_name=cache.llm,
                    message=prompt,
                    temperature=cache.temperature,
                    vector_db_id=cache.vector_db_id,
                ):
                    resp += token
                    place_holder.markdown(resp)


def main():
    init_webui()
    sidebar()
    body()


if __name__ == "__main__":
    main()
