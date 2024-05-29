echo "Building docker containers..."
docker-compose build --no-cache

# Start Django and Postgres containers for the initial setup
docker-compose up --detach django-external-storage-sync postgres-external-storage-sync

echo "Container setup..."
docker-compose exec django-external-storage-sync ./bin/container_setup.sh

# Starts the whole env
docker-compose up --detach

echo "Done!"
