FROM python:3.11

WORKDIR /app

COPY ./src /app/src
COPY ./pyproject.toml /app/pyproject.toml
COPY ./poetry.lock /app/poetry.lock
COPY ./*.py /app/

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root
RUN playwright install

CMD [ "echo 'Welcome to Aris AI!'" ]

# docker build -f docker/Dockerfile -t aris-ai:latest .