#!/bin/bash
set -e

echo "Waiting for postgres..."

# Wait for PostgreSQL to be ready using Python script
python /app/wait-for-db.py

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting server..."
exec "$@"
