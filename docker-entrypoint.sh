#!/bin/sh
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (ignore failures)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

# Default port
PORT=${PORT:-8000}

# Start gunicorn
echo "Starting gunicorn on port $PORT"
exec gunicorn --bind 0.0.0.0:${PORT} --workers 4 --worker-class sync --max-requests 1000 --max-requests-jitter 100 --timeout 60 expenses_app.wsgi:application
