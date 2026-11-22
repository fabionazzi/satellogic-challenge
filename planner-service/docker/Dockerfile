FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main

COPY ./src ./src
COPY alembic/ ./alembic/
COPY alembic.ini ./

FROM base AS test

COPY tests/ ./tests/

CMD ["pytest", "-v", "-p", "no:cacheprovider"]

FROM base AS runtime

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
