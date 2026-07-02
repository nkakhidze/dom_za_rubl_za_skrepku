FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-bot.txt requirements-dev.txt requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements-bot.txt

COPY alembic ./alembic
COPY app ./app
COPY bot ./bot
COPY scripts ./scripts
COPY alembic.ini ./

RUN chmod +x /app/scripts/backend-entrypoint.sh

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
