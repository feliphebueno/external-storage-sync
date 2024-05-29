#!/bin/sh
set -e

NAME="external_storage_sync"
APP_PATH=/var/www/external_storage_sync
SOCKFILE=${APP_PATH}/${NAME}.sock
WORKER_CLASS="gevent"
NUM_WORKERS=4
THREADS=8
DJANGO_SETTINGS_MODULE=config.settings
DJANGO_WSGI_MODULE=config.wsgi

MAX_REQUEST=300
TIMEOUT=30
GRACEFUL_TIMEOUT=30
LOG_FILE="/var/www/gunicorn.log"
LOG_LEVEL="warning"

echo "Starting $NAME as `whoami`"

cd ${APP_PATH} || exit

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
export PYTHONPATH=${APP_PATH}:${PYTHONPATH}


# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name ${NAME} \
  --bind=0.0.0.0:8000 \
  --worker-class ${WORKER_CLASS} \
  --workers ${NUM_WORKERS} \
  --threads ${THREADS} \
  --max-requests=${MAX_REQUEST} \
  --timeout=${TIMEOUT} \
  --graceful-timeout=${GRACEFUL_TIMEOUT} \
  --chdir=${APP_PATH} \
  --pid=/tmp/${NAME}.pid \
  --log-level=${LOG_LEVEL} \
  --log-file=${LOG_FILE}
