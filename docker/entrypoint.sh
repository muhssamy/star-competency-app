#!/bin/bash
# docker/entrypoint.sh
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=password psql -h db -U user -d star_competency -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "✅ PostgreSQL started"

# Ensure upload directory exists
mkdir -p /app/data/uploads
chmod -R 777 /app/data/uploads

# Start the application
if [ "$DEBUG" = "True" ]; then
  echo "Starting in debug mode..."
  exec flask --app star_competency_app.interfaces.web.app run --host=0.0.0.0 --port=5000 --debug
else
  echo "Starting in production mode..."
  exec gunicorn -b 0.0.0.0:5000 star_competency_app.interfaces.web.app:app --workers 4 --timeout 120
fi
