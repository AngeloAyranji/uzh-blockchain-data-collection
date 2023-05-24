#!/bin/bash

set -e
source scripts/util/prepare-env.sh

# view the logs for the data producers and consumers
docker compose \
    -p $PROJECT_NAME \
    logs \
    -f data_producer_eth data_consumer_eth
