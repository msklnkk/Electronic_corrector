#!/bin/sh
set -e

until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-app_db}"; do
  echo "PostgreSQL не готов — ждём..."
  sleep 1
done

alembic upgrade head

exec uvicorn main:app --host 0.0.0.0 --port 8000