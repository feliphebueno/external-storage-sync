set -e

echo "Application: ${1}"

case "$1" in
    django)
        if [ "$(grep -c "USE_ENV_PROD=1" .env)" -eq 1 ]; then
            echo "Collecting Django Admin static files for NGINX..."
            if [ -z "$(ls -A ./app/staticfiles/)" ]; then
                ./manage.py collectstatic
            fi;

            echo "Running with production environment..."
            ./bin/external_storage_sync.sh
        fi

        echo "Waiting for RabbitMQ..."
        ./bin/wait-for -t 3 rabbitmq-external-storage-sync:5672 -- echo "RabbitMQ is ready" || true

        exec ./manage.py runserver 0.0.0.0:8000
        ;;
    dramatiq)
        echo "Waiting for RabbitMQ..."
        ./bin/wait-for -t 3 rabbitmq-external-storage-sync:5672 -- echo "RabbitMQ is ready" || true
        dramatiq_extra=""
        if [ "$(grep -c "USE_ENV_PROD=1" .env)" -eq 1 ]; then
            dramatiq_extra="--processes 3 --threads 3 --use-gevent -v 1"
        fi
        exec ./manage.py rundramatiq ${dramatiq_extra}
        ;;
    *)
        exec "$@"
        ;;
esac
