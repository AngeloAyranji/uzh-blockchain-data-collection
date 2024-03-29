#!/bin/bash

set -e

source scripts/util/prepare-env.sh

export PROJECT_NAME="$PROJECT_NAME-dev"
export DATA_DIR="$DATA_DIR-dev"
export KAFKA_DATA_DIR="$KAFKA_DATA_DIR-dev"

source scripts/util/compose-cleanup.sh

# Prepare the data directory for db only
mkdir -p \
    $DATA_DIR/postgresql-data
chown -R $DATA_UID:$DATA_GID $DATA_DIR

# Start the db
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    up --build db
