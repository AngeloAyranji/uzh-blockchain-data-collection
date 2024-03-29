#!/bin/bash

set -e

source scripts/util/prepare-env.sh

export PROJECT_NAME="$PROJECT_NAME-dev"
export DATA_DIR="$DATA_DIR-dev"

source scripts/util/prepare-db-data-dir.sh $DATA_DIR
source scripts/util/compose-cleanup.sh

# Start the db
docker compose \
    -p $PROJECT_NAME \
    -f docker-compose.yml \
    -f docker-compose.dev.yml \
    up --build db
