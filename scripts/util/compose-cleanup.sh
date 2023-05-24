#!/bin/bash

# Cleanup on exit or interrupt
function cleanup {
    exit_status=$?
    echo "Starting cleanup; removing containers..."
    docker compose -p $PROJECT_NAME down --remove-orphans
    echo "Cleanup successful."
    exit $exit_status
}
trap cleanup EXIT
