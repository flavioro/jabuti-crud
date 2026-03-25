#!/usr/bin/env sh
set -eu

echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
