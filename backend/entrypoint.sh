#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head || echo "Migrations skipped (DB may not be ready)"

echo "Starting Social Media Platform API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
