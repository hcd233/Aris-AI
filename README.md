# Alice-AI

## 介绍

这是一个提供**私有化大语言模型服务**的项目，目的是为了快速接入通用大模型(GPT3.5、GPT4)和私有模型(Qwen1.5、ChatGLM3、LLama2、Baichuan2等)服务，提供统一的API接口。依托langchain框架提供多轮对话（Chat）和检索增强生成（RAG）服务，项目名来源于Blue Archive中的角色Alice，如下图

<>

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
- FAISS

### API后端

- Fastapi
- Sqlalchemy
- JWT
- Mysql
- Redis

### Web界面

- Streamlit

### 项目部署

- Docker

## 功能实现

### API相关

1. 用户注册、登录、权限管理
2. 对话管理、历史记录管理
3. 模型(LLM、Embedding)管理、预设(System)提示词管理
4. 向量数据库管理、向量数据库插入、支持文件: Pdf、Markdown、HTML和TXT格式的文件和Arxiv文章链接、链接递归插入

### 模型服务相关

1. Chat: 支持多轮对话
2. Retriever QA: 支持(RAG)检索增强生成的问答

### Web界面

1. 提供上传知识库的界面
2. 提供对话界面

## 项目结构

```text
├─ alice_api.py: 启动API服务器
├─ alice_webui.py: 启动WebUI
├─ confs: 配置文件
│   ├─ deployment: 用于正式环境
│   └─ local: 用于本地环境
├─ envs: 环境变量
│   ├─ deployment: 用于正式环境
│   └─ local: 用于本地环境
├─ docker: 容器部署文件
│   ├─ deployment: 用于正式环境部署
│   └─ local: 用于本地环境调试（只启动Mysql和Redis）
├─ pages: streamlit页面
│   ├─ chat.py: 对话界面
│   └─ vector_db.py: 向量数据库操作界面
├─ src: 内部模块
│   ├─ deployment: 用于正式环境
│   └─ local: 用于本地环境
│   ├─ config: 读取环境变量和配置文件
│   ├─ logger: 日志模块
│   ├─ api: API后端模块
│   │   ├─ auth: 鉴权模块  
│   │   ├─ model: API请求&响应模型
│   │   └─ router: API路由
│   │   │   ├─ v1: v1版本
│   │   │   │   ├─ user: 用户路由
│   │   │   │   ├─ key: 密钥路由
│   │   │   │   ├─ session: 对话路由
│   │   │   │   ├─ vector_db: 向量数据库路由
│   │   │   │   └─ model: 模型路由
│   │   │   │         ├─ llm: 大语言模型路由
│   │   │   │         └─ embedding: 词嵌入模路由
│   │   │   └─ root: 根路由（健康检查用）
│   ├─ langchain: Langchain组件
│   │   ├─ callback.py: 回调（实现SSE）
│   │   ├─ chain.py: 链（实现Chat & RAG）
│   │   ├─ memory.py: 上下文记忆（实现sql backend和windows memory）
│   │   ├─ prompt.py: 提示词（实现chat & RAG rompt template）
│   │   ├─ embedding.py: 词嵌入模型
│   │   ├─ llm.py: 大语言模型
│   │   ├─ retriever: 向量数据库检索
│   │   └─ text_splitter: 文档分块
│   └─ webui: WebUI模块
├─ poetry.lock: 项目依赖
└─ pyproject.toml: 项目配置
```

## 本地部署

### 克隆仓库

```bash
git clone https://github.com/hcd233/Alice-AI
cd Alice-AI
```

### 创建虚拟环境（可选）

可以不创建，但是需要确保python环境为3.11

```bash
conda create -n alice python=3.11.0
conda activate alice
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
python alice_api.py
```

### 启动WebUI

注意在IDE里指定local/webui.env为环境变量

```bash
streamlit run alice_webui.py
```

### 访问SwaggerUI和WebUI

- SwaggerUI: <http://localhost:${API_PORT}/docs>
- WebUI: <http://localhost:8501>

## Docker部署

### 配置conf和env（略）

见template文件

### 构建镜像

```bash
docker build -f docker/Dockerfile -t alice-ai:latest .
```

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
2. 调用私有模型服务，请先把模型部署成类OpenAI接口的API服务（例如llama.cpp-python），然后按照第一条的操作即可

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
