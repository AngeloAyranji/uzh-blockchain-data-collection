# Scripts

The following directory contains various scripts for running and testing the stack.

| Script | Description | Environment |
|---|---|---|
| run-db.sh | Starts the `db` container (PostgreSQL) |
| run-dev-eth.sh | Starts the entire data collection stack on the **dev** environment |
| run-prod-eth.sh | Starts the entire data collection stack on the **prod** environment |
| stop-prod-eth.sh | Stops the **prod** environment containers |
| view-logs-prod-eth.sh | Shows and follows the **prod** environment containers |

## Differences between Prod and Dev environments

1. Script exit
  * Production run script (`run-prod-eth.sh`) doesn't stop the containers on exit. For that you need to use `stop-prod-eth.sh`. After that, the containers remained in the stopped status, to remove them, run `docker compose -p <project_name> down --remove-orphans`.
  * Dev run script (`run-dev-eth.sh`) stops (cleans up) all containers on `KeyboardInterrupt` or any other exit signal.
2. Environment Variables
  * Production run script uses the environment variables defined in `.env` at the root of the repository.
  * Dev run script uses the same values but:
    * adds a 'dev' suffix to the `PROJECT_NAME`
    * adds a '/dev' path suffix to `DATA_DIR`
    * removes `SENTRY_DSN` env var, so that Sentry is never used for the development environment

## Supporting more EVM blockchains with existing scripts

The [run-dev-eth.sh](scripts/run-dev-eth.sh) can be **easily adapted** for other blockchains by simply changing:
1. the compose profile
2. logs targets.

E.g. to create a `scripts/run-dev-bsc.sh` one would need to edit:
```
    # Line 20 in run-dev-eth.sh
    --profile eth up \
    # to
    --profile bsc up \

    # Line 26 in run-dev-eth.sh
    -f data_producer_eth data_consumer_eth
    # to
    -f data_producer_bsc data_consumer_bsc
```
