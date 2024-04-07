# Aris-AI

[ English | [简体中文](README_zh.md) ]

## Introduction

This is a project that provides **private large language model services**, aiming to quickly access general large models (GPT3.5, GPT4) and private models (Qwen1.5, ChatGLM3, LLama2, Baichuan2, etc.) services, providing a unified API interface. Relying on the langchain framework to provide multi-turn dialogue (Chat) and retrieval augmented generation (RAG) services, the project name comes from the character Aris in Blue Archive, as shown in the figure below

<div style="text-align: center;">
  <img src="assets/110531412.jpg" style="width: 50%;" />
</div>

## Tech Stack

### Fine-tuning

- Transformers
- PEFT
- Pytorch
- Deepspeed

### Private Model Deployment

- llama.cpp
- llama-cpp-python

### Large Language Model Service

- Langchain
- FAISS

### API Backend

- Fastapi
- Sqlalchemy
- JWT
- Mysql
- Redis

### Web UI

- Streamlit

### Project Deployment

- Docker

## Function Implementation

### API Related

1. User registration, login, permission management
2. Dialogue management, history management
3. Model (LLM, Embedding) management, preset (System) prompt management
4. Vector database management, vector database insertion, support:

- Files: Pdf, Markdown, HTML, Jupyter, TXT, Python, C++, Java and other code files
- Links: Arxiv, Git, unauthenticated url (supports recursive crawling, automated tool crawling)

### Model Service Related

1. Chat: Supports multi-round dialogue
2. Retriever QA: Supports question answering with (RAG) retrieval enhanced generation

### Web Interface

1. Provide an interface to upload knowledge bases
2. Provide a dialogue interface

## Project Structure

```text
├─ aris_api.py: Start the API server
├─ aris_webui.py: Start the WebUI
├─ confs: Configuration files
│   ├─ deployment: For production environment
│   └─ local: For local environment
├─ envs: Environment variables
│   ├─ deployment: For production environment
│   └─ local: For local environment
├─ docker: Container deployment files
│   ├─ deployment: For production environment deployment
│   └─ local: For local environment debugging (only start Mysql and Redis)
├─ pages: streamlit pages
│   ├─ chat.py: Dialogue interface
│   └─ vector_db.py: Vector database operation interface
├─ src: Internal modules
│   ├─ deployment: For production environment
│   └─ local: For local environment
│   ├─ config: Read environment variables and configuration files
│   ├─ logger: Log module
│   ├─ api: API backend module  
│   │   ├─ auth: Authentication module  
│   │   ├─ model: API request & response model
│   │   └─ router: API router
│   │   │   ├─ v1: v1 version
│   │   │   │   ├─ user: User router
│   │   │   │   ├─ key: Key router
│   │   │   │   ├─ session: Dialogue router
│   │   │   │   ├─ vector_db: Vector database router
│   │   │   │   └─ model: Model router
│   │   │   │         ├─ llm: Large language model router
│   │   │   │         └─ embedding: Word embedding model router
│   │   │   └─ root: Root router (for health check)
│   ├─ langchain: Langchain component
│   │   ├─ callback.py: Callback (implement SSE)
│   │   ├─ chain.py: Chain (implement Chat & RAG)
│   │   ├─ memory.py: Context memory (implement sql backend and windows memory)
│   │   ├─ prompt.py: Prompt (implement chat & RAG rompt template)
│   │   ├─ embedding.py: Word embedding model
│   │   ├─ llm.py: Large language model
│   │   ├─ retriever: Vector database retrieval
│   │   ├─ url_loader: Component for importing links
│   │   ├─ file_loader: Component for importing files
│   │   └─ text_splitter: Document chunking
│   └─ webui: WebUI module
├─ poetry.lock: Project dependencies
└─ pyproject.toml: Project configuration
```

## Local Deployment

### Clone the Repository

```bash
git clone https://github.com/hcd233/Aris-AI
cd Aris-AI
```

### Create a Virtual Environment (Optional)

You can skip this step, but you need to make sure that the python environment is 3.11

```bash
conda create -n aris python=3.11.0
conda activate aris
```

### Install Dependencies

```bash
pip install poetry
poetry install
```

### Configure conf and env (Omitted)

See the template file

### Start Mysql and Redis

```bash
docker-compose -f docker/local/docker-compose.yml up -d
```

### Start the API Server

Note that you need to specify local/api.env as the environment variable in the IDE

```bash
python aris_api.py
```

### Start the WebUI

Note that you need to specify local/webui.env as the environment variable in the IDE

```bash
streamlit run aris_webui.py
```

### Access SwaggerUI and WebUI

- SwaggerUI: <http://localhost:${API_PORT}/docs>
- WebUI: <http://localhost:8501>

## Docker Deployment

### Configure conf and env (As above)

See the template file

### Start the Container

```bash
docker-compose -f docker/deployment/docker-compose.yml up -d --no-build
```

### Operation Instructions

#### User Operation

1. For login operations, I only did simple username and password verification, and did not provide a registration function in the WebUI. Please call the API interface yourself, and set the administrator status (is_admin=1) in the database operation to access private models
2. After login, you need to carry a jwt token to operate the secret key, which is used to call the private model service

#### Model Operation

1. Call the general large model service, which currently only supports the OpenAI series models (or agents with OpenAI-like interfaces). You can access it directly in the API. You need to store information such as base, key, max_tokens in the database, and you can customize the System prompt
2. Call the private model service, please deploy the model as an API service with an OpenAI-like API (such as [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)), and then follow the first The operation of the article can be done

## Project Outlook

### Goals

1. Support access to more models (AzureOpenAI, Gemini, HuggingFaceEndpoint, Llama.cpp)
2. More RAG strategies (RAG fusion, rearrangement, multi-path recall, etc.)
3. Support multi-modal Chat & RAG
4. Support maintaining a Key pool for the same model to achieve load balancing
5. Support Agent and tool calls
6. Release fine-tuned private models

### Author Status

Due to my busy work schedule, the project progress may be relatively slow, and I will update it occasionally. PRs and Issues are welcome
