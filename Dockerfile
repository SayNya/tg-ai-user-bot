FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    postgresql-dev

COPY pyproject.toml poetry.lock /app/

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY ./src /app/src
COPY .env README.md /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

CMD ["python", "src/main.py"]
