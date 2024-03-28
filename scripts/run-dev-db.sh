#!/bin/bash

set -e

export PROJECT_NAME="$PROJECT_NAME-dev"

source scripts/util/prepare-env.sh
source scripts/util/prepare-data-dir.sh $DATA_DIR $KAFKA_DATA_DIR $KAFKA_N_PARTITIONS
source scripts/util/compose-cleanup.sh

# Start the db
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    up --build db
