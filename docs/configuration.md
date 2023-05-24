# Configuration

The configuration variables for the data collection process are present in two files (`.env` and `cfg.json`).

> Some of the configuration values need to be updated in **both** configuration files, such as the full `node_url` or full `db_dsn`. Please check if updating one file doesn't require the update of some values in the other file before you start the process.

## .env
To create an `.env` file you can copy the provided [`.env.default`](../.env.default) and edit the values as needed.

### Available environment variables
| ENV_VAR | Description | Default value |
|---|---|---|
| `PROJECT_NAME` | Prefix for container names and docker network name | "bdc" |
| `DATA_DIR` | Persistent data destination directory (PostgreSQL, Kafka, Zookeeper) | "./data" |
| `LOG_LEVEL` | logging level of consumers and producers | "INFO" |
| `DATA_UID` | Data directory owner ID (can be left blank) | `id -u` |
| `DATA_GID` | Data directory owner group ID (can be left blank) | `getent group bdlt \| cut -d: -f3` |
| `N_CONSUMERS` | Number of consumers to use for each topic (blockchain) | 2 |
| `N_CONSUMER_INSTANCES` | Number of DataConsumer instances per consumer container | 2 |
| `KAFKA_N_PARTITIONS` | The number of partitions per topic | `2 * N_CONSUMERS * N_CONSUMER_INSTANCES` |
| `SENTRY_DSN` | DSN for error monitoring via [Sentry](https://sentry.io/welcome/) (optional) | None |
| `POSTGRES_PORT` | Published host port for PostgreSQL | 13338 |
| `POSTGRES_USER` | Username for connecting to PostgreSQL service | "username" |
| `POSTGRES_PASSWORD` | Password for connecting to PostgreSQL service | "postgres" |
| `POSTGRES_DB` | PostgreSQL default database name | "db" |
| `ERIGON_PORT` | Port of the erigon node | 8547 |
| `ERIGON_HOST` | Host of the erigon node | "host.docker.internal" |
| `WEB3_REQUESTS_TIMEOUT` | Timeout for every web3 request (in seconds) | 30 |
| `WEB3_REQUESTS_RETRY_LIMIT` | Amount of retries for each failed web3 request | 10 |
| `WEB3_REQUESTS_RETRY_DELAY` | Time delay between retries (in seconds) | 5 |
| `KAFKA_EVENT_RETRIEVAL_TIMEOUT` | Timeout before exiting consumers after not receiving any event (in seconds) | 600 |


## cfg.json
The configuration json files are used for selecting which contracts, events or block ranges should the web3 data be extracted from. There are two main data collection modes to choose from:

1. `"partial"` = the default mode, only store the web3 data of contracts and events defined in config.json
2. `"full"` = store all web3 data (all transactions) within some block range (including internal transactions and logs)
3. `"log_filter"` = (not implemented yet) `get_all_entries` method on web3.filter doesn't work with erigon
