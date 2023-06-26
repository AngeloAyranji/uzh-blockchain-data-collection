# Configuration

The configuration variables for the data collection process are present in two files (`.env` and `cfg.json`).

> ⚠️ Some of the configuration values need to be updated in **both** configuration files, such as the full `node_url` or full `db_dsn`. Please check if updating one file doesn't require the update of some values in the other file before you start the process.

## .env
To create an `.env` file you can copy the provided [`.env.default`](../.env.default) and edit the values as needed.

### Available environment variables
| ENV_VAR | Description | Default value |
|---|---|---|
| `PROJECT_NAME` | Prefix for container names and docker network name | "bdc" |
| `DATA_DIR` | Persistent data destination directory (PostgreSQL) | "./data" |
| `KAFKA_DATA_DIR` | Persistent data destination directory (Kafka, Zookeeper) | "./data" |
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
The configuration json files are used for selecting the data collection mode.

A *sample configuration file* for the Ethereum blockchain with partial collection mode to collect USDT Transfers within blocks 13000000 and 13000020:
```
{
    "node_url": "http://host.docker.internal:8547",
    "db_dsn": "postgres://user:postgres@db_pool:6432/db",
    "redis_url": "redis://redis",
    "kafka_url": "kafka:9092",
    "kafka_topic": "eth",
    "data_collection": [
        {
            "mode": "partial",
            "start_block": 13000000,
            "end_block": 13000020,
            "contracts": [
                {
                    "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    "symbol": "USDT",
                    "category": "erc20",
                    "events": [
                        "TransferFungibleEvent"
                    ]
                }
            ]
        }
    ]
}
```

### Data collection mode

1. `"partial"` = the default mode, only store the web3 data of contracts and events defined in config.json
    * required fields: `start_block`, `end_block`, `contracts`
    ```
    "data_collection": [
        {
            "mode": "partial",
            "start_block": 16804500,
            "end_block": 17100000,
            "contracts": [...]
        }
    ]
    ```
    * transaction, internal transactions and logs are stored if:
        * `to_address` of the transaction is one of the contracts addresses
        * `address` of any log in a transaction is one of the contracts addresses
        * `contractAddress` of the transaction receipt is one of the contract addresess
2. `"full"` = store all web3 data (all transactions) within some block range (including internal transactions and logs)
    * required fields: `start_block`, `end_block`
    ```
    "data_collection": [
        {
            "mode": "full",
            "start_block": 16804500,
            "end_block": 17100000
        }
    ]
    ```
3. `"get_logs"` = producers send transactions received from the `eth_getLogs` RPC method to the consumers
    * required fields: `params` (same [spec](https://www.quicknode.com/docs/ethereum/eth_getLogs) as for `eth_getLogs`)
    ```
    "data_collection": [
        {
            "mode": "get_logs",
            "params": {
                "fromBlock": 123,
                "toBlock": 456,
                "topics": [...],
                "address": "0x..."
            }
        }
    ]
    ```
4. `"log_filter"` = (not/partially implemented) `get_all_entries` method on web3.filter doesn't work with erigon

#### `contracts` field
The contracts field is an array of objects that describe a contract and the events that should be collected.

Example contract object for USDT for which three events are collected:
```
{
    "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "symbol": "USDT",
    "category": "erc20",
    "events": [
        "TransferFungibleEvent",
        "MintFungibleEvent",
        "BurnFungibleEvent"
    ]
}
```

| Field | Type | Description | Required |
|---|---|---|
| `address` | string | the address of a contract | Yes |
| `symbol` | string | symbol of the contract (only used for convenience in the config file) | No |
| `category` | string | category of a contract, has to be matching one of the keys defined in `contract_abi.json` | Yes |
| `events` | array of string | exhaustive list of all events that will result in data being saved in the db | Yes |

#### `params` field
The params field is an object which will be directly passed to the web3 `eth_getLogs` [RPC method call](https://www.quicknode.com/docs/ethereum/eth_getLogs).

Example params object:
```
{
    "fromBlock": 123,
    "toBlock": 456,
    "topics": [...],
    "address": "0x..."
}
```
