#!/bin/bash

# Simple entrypoint without complex health checks
# Let Docker Compose health checks handle service dependencies

echo "Running database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000