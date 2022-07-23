#!/bin/sh

# remove-orphans removes db container if needed
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --force-recreate --remove-orphans