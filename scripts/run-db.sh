#!/bin/bash

set -e
source scripts/util/prepare-env.sh
source scripts/util/prepare-db-data-dir.sh $DATA_DIR
source scripts/util/compose-cleanup.sh

# Start the db
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.prod.yml \
    up --build db
