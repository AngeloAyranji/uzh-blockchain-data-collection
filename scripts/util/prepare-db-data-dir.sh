#!/bin/bash

mkdir -p \
    $1/postgresql-data
chown -R $DATA_UID:$DATA_GID $1