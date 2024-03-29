#!/bin/bash

set -e

source scripts/util/prepare-env.sh

export PROJECT_NAME="$PROJECT_NAME-dev"
export DATA_DIR="$DATA_DIR-dev"
export KAFKA_DATA_DIR="$KAFKA_DATA_DIR-dev"
export KAFKA_N_PARTITIONS=4

source scripts/util/prepare-data-dir.sh $DATA_DIR $KAFKA_DATA_DIR $KAFKA_N_PARTITIONS
source scripts/util/compose-cleanup.sh

# Start the db
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    up --build db
