FROM python:3.13

WORKDIR /app

COPY ./src /app/src
COPY pyproject.toml poetry.lock .env README.md /app/

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]
