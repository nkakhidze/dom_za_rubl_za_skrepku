#!/bin/sh
set -e

echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."

python - <<'PY'
import os
import time

import psycopg

host = os.environ["POSTGRES_HOST"]
port = int(os.environ.get("POSTGRES_PORT", "5432"))
dbname = os.environ["POSTGRES_DB"]
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]

for attempt in range(60):
    try:
        with psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=2,
        ):
            print("PostgreSQL is ready")
            break
    except Exception as error:
        if attempt == 59:
            raise
        print(f"PostgreSQL is not ready yet: {error}")
        time.sleep(1)
PY

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting backend..."
exec "$@"
