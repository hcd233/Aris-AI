FROM python:3.11

WORKDIR /app

COPY . .

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# docker build -f docker/Dockerfile -t alice-ai:latest .