#!/bin/bash

# Run unit tests
docker compose \
    -f docker-compose.tests.yml \
    up test_unit \
    --build \
    --abort-on-container-exit
