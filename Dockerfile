FROM python:3.13-alpine

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock /app/

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY ./src /app/src
COPY .env README.md /app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

CMD ["python", "src/main.py"]