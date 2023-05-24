#!/bin/bash

source .env

REDIS_CONTAINER="${PROJECT_NAME}-redis-1"

# Show the sorted set in redis that keeps track of events received and consumed per partition in topic eth
docker exec -it $REDIS_CONTAINER bash -c 'echo "ZRANGE eth_n_transactions 0 -1 WITHSCORES" | redis-cli'
