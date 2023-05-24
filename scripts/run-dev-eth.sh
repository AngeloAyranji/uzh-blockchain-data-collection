#!/bin/bash

set -e

source scripts/util/prepare-env.sh

# Add dev prefix
export PROJECT_NAME="$PROJECT_NAME-dev"
export DATA_DIR="$DATA_DIR/dev"

# Don't use Sentry for dev env
unset SENTRY_DSN

source scripts/util/prepare-data-dir.sh $DATA_DIR $KAFKA_N_PARTITIONS
source scripts/util/compose-cleanup.sh

echo "Building containers..."

# Start the containers in detached mode and
# attach the logs only to the data producers and consumers
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    --profile eth up \
    --force-recreate \
    --build \
    --remove-orphans \
    -d

echo "Data collection starting..."

echo "Adding containers to network '${PROJECT_NAME}_default'"
docker network connect ${PROJECT_NAME}_default ${PROJECT_NAME}-data_producer_eth-1

# Connect producer and each consumer (currently on the default 'bridge' network) to the compose network
docker ps --format '{{.Names}}' \
    | grep "consumer" \
    | while read c ; do {(docker network connect ${PROJECT_NAME}_default $c) &}; done
echo "Done; following container logs..."

# attach the logs only to the data producers and consumers
docker compose \
    -p $PROJECT_NAME \
    logs \
    -f data_producer_eth data_consumer_eth
