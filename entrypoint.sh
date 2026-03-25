#!/bin/bash
set -e

cd /app

echo "Waiting for postgres..."
python /usr/local/bin/wait-for-db.py

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting server..."
exec "$@"
