#!/bin/bash

KAFKA_DIR=$2/kafka-data/kafka-logs/

mkdir -p \
    $2/zookeeper-data/data \
    $2/zookeeper-data/datalog \
    $2/kafka-data \
    $1/postgresql-data
chown -R $DATA_UID:$DATA_GID $1

# Save the current number of partitions
N_EXISTING_PARTITIONS=`ls -l $KAFKA_DIR | grep -E "^d.*eth-[0-9]+$" | wc -l`

# Checks whether the current configuration of env variables is compatible with the existing data in $DATA_DIR
if [ $N_EXISTING_PARTITIONS != $3 ] && [ $N_EXISTING_PARTITIONS != 0 ]
then
    echo "Warning: The number of existing kafka partitions ($N_EXISTING_PARTITIONS) in $KAFKA_DIR conflicts with the current environment variable configuration ($3). Please change the KAFKA_N_PARTITIONS variable ($3) to match the existing number of partitions ($N_EXISTING_PARTITIONS) or remove the existing kafka directory ($KAFKA_DIR)"
    echo "Exiting..."
    exit 1
fi
