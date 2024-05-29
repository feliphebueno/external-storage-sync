#!/bin/bash
set -e
# Wait for the last dependency before running commands
./bin/wait-for -t 5 rabbitmq-external-storage-sync:5672 -- echo "RabbitMQ is ready" || true

# Apply DB schema migrations
./manage.py migrate

# Organizes Django admin static files e.g: CSS/JS/images
rm -rf ./app/staticfiles/
./manage.py collectstatic

# Creates a default superuser account:
./manage.py shell < ./bin/setup_admin_user.py
