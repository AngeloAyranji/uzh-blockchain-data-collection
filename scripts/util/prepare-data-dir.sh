#!/bin/bash

KAFKA_DIR=$1/kafka-data/kafka-logs/

if [ -d $1 ]
then
    echo "Using existing data directory ($1)"
else
    echo "Preparing data directory structure ($1)"
    # Linux workaround for docker container user/group permissions
    mkdir -p \
        $DATA_DIR/zookeeper-data/data \
        $DATA_DIR/zookeeper-data/datalog \
        $DATA_DIR/kafka-data \
        $DATA_DIR/postgresql-data
    chown -R $DATA_UID:$DATA_GID $DATA_DIR
    # Created a new directory for data so we can exit this script as no further integrity checks are necessary.
    return
fi

# Save the current number of partitions
N_EXISTING_PARTITIONS=`ls -l $KAFKA_DIR | grep -E "^d.*eth-[0-9]+$" | wc -l`

# Checks whether the current configuration of env variables is compatible with the existing data in $DATA_DIR
if [ $N_EXISTING_PARTITIONS != $2 ]
then
    echo "Warning: The number of existing kafka partitions ($N_EXISTING_PARTITIONS) in $KAFKA_DIR conflicts with the current environment variable configuration ($2). Please change the KAFKA_N_PARTITIONS variable ($2) to match the existing number of partitions ($N_EXISTING_PARTITIONS) or remove the existing kafka directory ($KAFKA_DIR)"
    echo "Exiting..."
    exit 1
fi
