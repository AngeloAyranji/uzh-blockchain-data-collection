#!/bin/bash

source .env

KAFKA_CONTAINER="${PROJECT_NAME}-kafka-1"

# Print the status of partitions for topic eth (events received, events left to consume, etc.)
docker exec -it $KAFKA_CONTAINER /bin/bash -c '${KAFKA_HOME}/bin/kafka-consumer-groups.sh --describe --bootstrap-server kafka:9092 --group eth'
