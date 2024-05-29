#!/bin/bash
set -e
DJANGO_APP_STATUS_URL="http://localhost:8000/status.html"

# When running with production settings, also checks for gunicorn's processes
if pgrep gunicorn &> /dev/null; then
    curl --fail -L ${DJANGO_APP_STATUS_URL} || exit 1
else
    exit 0
fi
