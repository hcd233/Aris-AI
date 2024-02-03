FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# docker build -f docker/dockerfile -t alice-ai:latest .