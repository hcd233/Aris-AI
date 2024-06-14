# Aris-AI

[ English | [简体中文](README_zh.md) ]

## Introduction

This is a project that provides **private large language model services**, aiming to quickly access general large models (GPT3.5, GPT4) and private models (Qwen1.5, ChatGLM3, LLama2, Baichuan2, etc.) services, providing a unified API interface. Relying on the langchain framework to provide multi-turn dialogue (Chat) and retrieval augmented generation (RAG) services, the project name comes from the character Aris in Blue Archive, as shown in the figure below

<div style="text-align: center;">
  <img src="assets/110531412.jpg" style="width: 50%;" />
</div>

## Change Log

- [2024-06-15] Use Neo4j as the database for storing knowledge bases

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

### API Backend

- Fastapi
- Sqlalchemy
- JWT
- Mysql
- Redis
- Neo4j

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
.
├── assets
├── confs
│   ├── deployment
│   └── local
├── docker
│   ├── deployment
│   └── local
├── envs
│   ├── deployment
│   └── local
├── kubernetes
├── logs
├── pages
└── src
    ├── api
    │   ├── auth
    │   ├── model
    │   └── router
    │       └── v1
    │           ├── model
    │           └── oauth2
    ├── config
    ├── langchain_aris
    ├── logger
    ├── middleware
    │   ├── jwt
    │   ├── logger
    │   ├── mysql
    │   │   └── models
    │   └── redis
    └── webui
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

### Create Volumes

```bash
docker volume create mysql-data
docker volume create redis-data
docker volume create neo4j-data
```

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
