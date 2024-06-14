# Aris-AI

[ [English](README.md) | 简体中文 ]

## 介绍

这是一个提供**私有化大语言模型服务**的项目，目的是为了快速接入通用大模型(GPT3.5、GPT4)和私有模型(Qwen1.5、ChatGLM3、LLama2、Baichuan2等)服务，提供统一的API接口。依托langchain框架提供多轮对话（Chat）和检索增强生成（RAG）服务，项目名来源于Blue Archive中的角色Aris，如下图

<div style="text-align: center;">
  <img src="assets/110531412.jpg" style="width: 50%;" />
</div>

## 更新日志

- [2024-06-15] 使用Neo4j作为存储知识库的数据库

## 技术栈

### 微调

- Transformers
- PEFT
- Pytorch
- Deepspeed

### 私有模型部署

- llama.cpp
- llama-cpp-python

### 大模型服务

- Langchain

### API后端

- Fastapi
- Sqlalchemy
- JWT
- Mysql
- Redis
- Neo4j

### Web界面

- Streamlit

### 项目部署

- Docker

## 功能实现

### API相关

1. 用户注册、登录、权限管理
2. 对话管理、历史记录管理
3. 模型(LLM、Embedding)管理、预设(System)提示词管理
4. 向量数据库管理、向量数据库插入、支持:

- 文件: Pdf、Markdown、HTML、Jupyter、TXT、Python、C++、Java等多种代码文件
- 链接: Arxiv、Git、无鉴权url(支持递归爬取、自动化工具爬取)

### 模型服务相关

1. Chat: 支持多轮对话
2. Retriever QA: 支持(RAG)检索增强生成的问答

### Web界面相关

1. 提供上传知识库的界面
2. 提供对话界面

## 项目结构

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

## 本地部署

### 克隆仓库

```bash
git clone https://github.com/hcd233/Aris-AI
cd Aris-AI
```

### 创建虚拟环境（可选）

可以不创建，但是需要确保python环境为3.11

```bash
conda create -n aris python=3.11.0
conda activate aris
```

### 安装依赖

```bash
pip install poetry
poetry install
```

### 配置conf和env（略）

见template文件

### 启动Mysql和Redis

```bash
docker-compose -f docker/local/docker-compose.yml up -d
```

### 启动API服务器

注意在IDE里指定local/api.env为环境变量

```bash
python aris_api.py
```

### 启动WebUI

注意在IDE里指定local/webui.env为环境变量

```bash
streamlit run aris_webui.py
```

### 访问SwaggerUI和WebUI

- SwaggerUI: <http://localhost:${API_PORT}/docs>
- WebUI: <http://localhost:8501>

## Docker部署

### 配置conf和env（同上）

见template文件

### 启动容器

```bash
docker-compose -f docker/deployment/docker-compose.yml up -d --no-build
```

### 操作说明

#### 用户操作

1. 对于登录操作，我只做了简单的用户名密码验证，并且没有在WebUI中提供注册功能，请自行调用API接口，并且操作数据库设置管理员身份（is_admin=1），以便接入私有模型
2. 登录后需要携带jwt token才能操作secret key，secret key用于调用私有模型服务

#### 模型操作

1. 调用通用大模型服务，目前仅支持OpenAI系列模型（或类OpenAI接口的代理），直接在API中接入即可，需要在数据库中储存base、key、max_tokens等信息，同时可以自定义System prompt
2. 调用私有模型服务，请先把模型部署成类OpenAI接口的API服务（例如[llama-cpp-python](https://github.com/abetlen/llama-cpp-python)），然后按照第一条的操作即可

## 项目展望

### 目标

1. 支持接入更多模型（AzureOpenAI、Gemini、HuggingFaceEndpoint、Llama.cpp）
2. 更多RAG策略（RAG fusion、重排、多路召回等）
3. 支持多模态Chat & RAG
4. 支持对同模型维护Key池实现负载均衡
5. 支持Agent和工具调用
6. 发布微调的私有模型

### 作者状态

因为工作繁忙，项目进度可能会比较慢，随缘更新一下，欢迎PR和Issue
