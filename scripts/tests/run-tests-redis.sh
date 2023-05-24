#!/bin/bash

# Run database tests
docker compose \
    -f docker-compose.tests.yml \
    up test_redis \
    --build \
    --abort-on-container-exit
