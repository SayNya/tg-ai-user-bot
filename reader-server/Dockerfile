FROM python:3.13-slim

ENV POETRY_VERSION=2.1
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false \
  && poetry install --only main

COPY . /app/

COPY .env /app/.env

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

CMD ["python", "src/main.py"]
