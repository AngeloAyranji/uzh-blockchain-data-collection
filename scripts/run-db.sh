#!/bin/bash

set -e
source scripts/util/prepare-env.sh
source scripts/util/prepare-data-dir.sh $DATA_DIR $KAFKA_N_PARTITIONS
source scripts/util/compose-cleanup.sh

# Start the db
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    up --build db
