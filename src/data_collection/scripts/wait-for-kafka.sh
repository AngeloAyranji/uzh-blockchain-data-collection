#!/bin/bash

RETRIES=0
MAX_RETRIES=100

echo "Waiting for Kafka container to start...";

# Wait for Kafka to start
while ! curl --connect-timeout 5 http://kafka:9092/ 2>&1 | grep '52' >/dev/null;
do
  sleep 2;

  # Respect maximum amount of retries
  (( RETRIES++ ))
  if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo "Maximum retries ($RETRIES) reached. Kafka container failed to start in time."
    exit 1;
  fi
done

echo "Kafka container alive. Waiting 15s for Kafka startup script to finish..."
sleep 15;
