from typing import Any, Dict

import streamlit as st
from streamlit import session_state as cache

from internal.webui.utils import chat, get_history, get_llms, get_sessions, new_session

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
        page_title="Alice AI WebUI",
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
        "llm": "",
        "temperature": 0.7,
        "session_id": "-1",
        "history": [],
    }

    for var, def_val in vars.items():
        if not hasattr(cache, var):
            setattr(cache, var, def_val)


def sidebar():
    st.sidebar.title("Alice AI")
    cache.api_key = st.sidebar.text_input("Alice Api Key", max_chars=100, type="password")

    st.sidebar.header("Sessions")
    sessions = get_sessions(cache.api_key)
    cache.session_id = st.sidebar.selectbox("Select session", options=sessions)

    new_session_onclick = st.sidebar.button("New Chat", key="new_chat")
    if new_session_onclick:
        cache.session_id = new_session(cache.api_key)
        st.success(f"New session created: {cache.session_id}")
        st.rerun()

    st.sidebar.header("LLMs")
    llms = get_llms(cache.api_key)
    cache.llm = st.sidebar.selectbox("Select llm", options=llms)

    st.sidebar.header("Temperature")
    cache.temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.05)


def body():
    cache.history = get_history(cache.api_key, cache.session_id)
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
            for token in chat(
                api_key=cache.api_key,
                session_id=cache.session_id,
                llm_name=cache.llm,
                message=prompt,
                temperature=cache.temperature,
            ):
                resp += token
                place_holder.markdown(resp)


def main():
    init_webui()
    sidebar()
    body()


if __name__ == "__main__":
    main()
