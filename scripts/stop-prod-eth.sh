#!/bin/bash

set -e
source scripts/util/prepare-env.sh

function cleanup {
    echo "Stopping production containters;"
    docker compose -p $PROJECT_NAME stop
    echo "Success."
}

read -p "Are you sure you want to stop the 'prod' containers? This will not remove them. (y/n) " choice
case "$choice" in
  y|Y ) cleanup;;
  n|N ) echo "Ok - skipping...";;
  * ) echo "Invalid value.";;
esac
