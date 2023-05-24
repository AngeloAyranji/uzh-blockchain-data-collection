#!/bin/bash
# Export necessary environment variables with default values

set -e

source .env

# Prefix for the containers and network
export PROJECT_NAME="${PROJECT_NAME:=bdc}"

# Used for correct permissions (e.g. in PostgreSQL)
# use the value in .env or get a default value with a command
export DATA_UID="${DATA_UID:=$(id -u)}"
export DATA_GID="${DATA_GID:=$(getent group bdlt | cut -d: -f3)}"
