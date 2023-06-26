# Example

This document shows a very simple few step example of configuration, orchestration and the output of running the application stack in both environments.

This example will:
* start 1 producer that will insert all transactions into Kafka in the block range 13000000-13000020
* start 2 consumers that will consume all transactions from Kafka and only save data for those that are related to USDT and contain a Transfer event in the logs
* stop all containers after 10 minutes of no events received from Kafka in all consumers.

## Configuration
Use the same configuration as shown in [docs/configuration.md](/docs/configuration.md#cfgjson). You may only need to adjust the `node_url`.

Copy this configuration into [src/data_collection/etc/cfg/dev/eth.json](/src/data_collection/etc/cfg/dev/eth.json) and [src/data_collection/etc/cfg/prod/eth.json](/src/data_collection/etc/cfg/prod/eth.json).

Make sure to also have an `.env` file in the root of the repository (`cp .env.default .env`)

## Running in development mode
Running in development mode only requires to start the `run-dev-eth.sh` script like so:

```
$ ./scripts/run-dev-eth.sh
ls: cannot access './data-dev/kafka-data/kafka-logs/': No such file or directory
Building containers...
[+] Building 0.9s (50/50) FINISHED
...
<a lot of docker build logs in here>
...
Data collection starting...
Adding containers to network 'bdc-dev_default'
Done; following container logs...
bdc-dev-data_producer_eth-1  | Waiting for Kafka container to start...
bdc-dev-data_consumer_eth-2  | Waiting for Kafka container to start...
bdc-dev-data_consumer_eth-1  | Waiting for Kafka container to start...
bdc-dev-data_producer_eth-1  | Kafka container alive. Waiting 15s for Kafka startup script to finish...
bdc-dev-data_consumer_eth-2  | Kafka container alive. Waiting 15s for Kafka startup script to finish...
bdc-dev-data_consumer_eth-1  | Kafka container alive. Waiting 15s for Kafka startup script to finish...
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:53.188 __main__ INFO     Starting producer-eth
bdc-dev-data_consumer_eth-2  | 2023-06-26 12:55:53.336 __main__ INFO     Starting consumer-eth
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:53.342 app.producer INFO     Using config: {'node_url': AnyUrl('http://host.docker.internal:8547', scheme='http', host='host.docker.internal', tld='internal', host_type='domain', port='8547'), 'db_dsn': PostgresDsn('postgres://user:postgres@db_pool:6432/db', ), 'sentry_dsn': '', 'redis_url': RedisDsn('redis://redis:6379/0', ), 'kafka_url': 'kafka:9092', 'kafka_topic': 'eth', 'number_of_consumer_tasks': 2, 'web3_requests_timeout': 30, 'web3_requests_retry_limit': 10, 'web3_requests_retry_delay': 5, 'kafka_event_retrieval_timeout': 600}
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:53.342 app.producer INFO     Creating data collection producer task ({'mode': <DataCollectionMode.PARTIAL: 'partial'>, 'start_block': 13000000, 'end_block': 13000020, 'topics': None, 'params': None, 'contracts': ['USDT']})
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:53.342 app.producer INFO     Found 4 partition(s) on topic 'eth'
bdc-dev-data_consumer_eth-1  | 2023-06-26 12:55:53.386 __main__ INFO     Starting consumer-eth
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:53.484 app.producer INFO     Starting from block #13000000, expecting to finish at block #13000020
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:54.001 app.producer INFO     Finished at block #13000020 | total produced transactions: 4066
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:54.001 app.producer INFO     Finished producing data from all data collection tasks.
bdc-dev-data_producer_eth-1  | 2023-06-26 12:55:54.001 __main__ INFO     Exiting producer-eth with code 0
bdc-dev-data_producer_eth-1 exited with code 0
bdc-dev-data_consumer_eth-1  | 2023-06-26 12:56:03.800 app.kafka.manager INFO     Consuming events in topic 'eth' for partitions: [3, 1]
bdc-dev-data_consumer_eth-2  | 2023-06-26 12:56:03.802 app.kafka.manager INFO     Consuming events in topic 'eth' for partitions: [2, 0]
bdc-dev-data_consumer_eth-2  | 2023-06-26 13:06:57.463 app.kafka.manager INFO     No event received for 600 seconds from any partition - timed out
bdc-dev-data_consumer_eth-2  | 2023-06-26 13:06:57.478 app.consumer INFO     Finished processing topic 'eth'.
bdc-dev-data_consumer_eth-2  | 2023-06-26 13:06:57.478 app.consumer INFO     number of consumed transactions: 1736 | number of processed transactions: 124
bdc-dev-data_consumer_eth-2  | 2023-06-26 13:06:57.479 __main__ INFO     Exiting consumer-eth with code 0
bdc-dev-data_consumer_eth-2 exited with code 0
bdc-dev-data_consumer_eth-1  | 2023-06-26 13:07:34.552 app.kafka.manager INFO     No event received for 600 seconds from any partition - timed out
bdc-dev-data_consumer_eth-1  | 2023-06-26 13:07:34.559 app.consumer INFO     Finished processing topic 'eth'.
bdc-dev-data_consumer_eth-1  | 2023-06-26 13:07:34.559 app.consumer INFO     number of consumed transactions: 2330 | number of processed transactions: 140
bdc-dev-data_consumer_eth-1  | 2023-06-26 13:07:34.560 __main__ INFO     Exiting consumer-eth with code 0
bdc-dev-data_consumer_eth-1 exited with code 0
Starting cleanup; removing containers...
[+] Running 9/9
 ⠿ Container bdc-dev-data_consumer_eth-1  Removed                                                                                                                                                                                                         0.0s
 ⠿ Container bdc-dev-db_pool-1            Removed                                                                                                                                                                                                         0.5s
 ⠿ Container bdc-dev-data_consumer_eth-2  Removed                                                                                                                                                                                                         0.0s
 ⠿ Container bdc-dev-data_producer_eth-1  Removed                                                                                                                                                                                                         0.0s
 ⠿ Container bdc-dev-redis-1              Removed                                                                                                                                                                                                         0.5s
 ⠿ Container bdc-dev-kafka-1              Removed                                                                                                                                                                                                         2.3s
 ⠿ Container bdc-dev-db-1                 Removed                                                                                                                                                                                                         0.7s
 ⠿ Container bdc-dev-zookeeper-1          Removed                                                                                                                                                                                                         0.6s
 ⠿ Network bdc-dev_default                Removed                                                                                                                                                                                                         0.2s
Cleanup successful.
$
```

After 10 minutes of inactivity, consumers will shutdown. If no consumers are running, the rest of containers will shutdown. Now you can use the collected postgresql data in `./data-dev`.
```
$ ls -h data-dev
kafka-data  postgresql-data  zookeeper-data
```

## Running in production mode
```
▶ ./scripts/run-prod-eth.sh
Building containers...
[+] Building 0.6s (50/50) FINISHED                                                                                                                                                                                   4.1s
Data collection starting...
Adding containers to network 'bdc_default'
Done; following container logs...
bdc-data_producer_eth-1  | Waiting for Kafka container to start...
bdc-data_consumer_eth-1  | Waiting for Kafka container to start...
bdc-data_consumer_eth-2  | Waiting for Kafka container to start...
bdc-data_producer_eth-1  | Kafka container alive. Waiting 15s for Kafka startup script to finish...
bdc-data_consumer_eth-2  | Kafka container alive. Waiting 15s for Kafka startup script to finish...
bdc-data_consumer_eth-1  | Kafka container alive. Waiting 15s for Kafka startup script to finish...
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.013 __main__ INFO     Starting producer-eth
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.181 app.producer INFO     Using config: {'node_url': AnyUrl('http://host.docker.internal:8547', scheme='http', host='host.docker.internal', tld='internal', host_type='domain', port='8547'), 'db_dsn': PostgresDsn('postgres://user:postgres@db_pool:6432/db', ), 'sentry_dsn': '', 'redis_url': RedisDsn('redis://redis:6379/0', ), 'kafka_url': 'kafka:9092', 'kafka_topic': 'eth', 'number_of_consumer_tasks': 2, 'web3_requests_timeout': 30, 'web3_requests_retry_limit': 10, 'web3_requests_retry_delay': 5, 'kafka_event_retrieval_timeout': 600}
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.181 app.producer INFO     Creating data collection producer task ({'mode': <DataCollectionMode.PARTIAL: 'partial'>, 'start_block': 13000000, 'end_block': 13000020, 'topics': None, 'params': None, 'contracts': ['USDT']})
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.181 app.producer INFO     Found 8 partition(s) on topic 'eth'
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.318 app.producer INFO     Starting from block #13000000, expecting to finish at block #13000020
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.747 app.producer INFO     Finished at block #13000020 | total produced transactions: 4066
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.747 app.producer INFO     Finished producing data from all data collection tasks.
bdc-data_producer_eth-1  | 2023-06-26 13:34:39.748 __main__ INFO     Exiting producer-eth with code 0
bdc-data_consumer_eth-2  | 2023-06-26 13:34:39.852 __main__ INFO     Starting consumer-eth
bdc-data_consumer_eth-1  | 2023-06-26 13:34:39.911 __main__ INFO     Starting consumer-eth
bdc-data_producer_eth-1 exited with code 0
bdc-data_consumer_eth-2  | 2023-06-26 13:34:49.929 app.kafka.manager INFO     Consuming events in topic 'eth' for partitions: [2, 6]
bdc-data_consumer_eth-2  | 2023-06-26 13:34:49.930 app.kafka.manager INFO     Consuming events in topic 'eth' for partitions: [1, 5]
bdc-data_consumer_eth-1  | 2023-06-26 13:34:49.930 app.kafka.manager INFO     Consuming events in topic 'eth' for partitions: [4, 0]
bdc-data_consumer_eth-1  | 2023-06-26 13:34:49.930 app.kafka.manager INFO     Consuming events in topic 'eth' for partitions: [7, 3]
bdc-data_consumer_eth-2  | 2023-06-26 13:44:58.775 app.kafka.manager INFO     No event received for 600 seconds from any partition - timed out
bdc-data_consumer_eth-2  | 2023-06-26 13:44:58.791 app.consumer INFO     Finished processing topic 'eth'.
bdc-data_consumer_eth-2  | 2023-06-26 13:44:58.791 app.consumer INFO     number of consumed transactions: 785 | number of processed transactions: 65
bdc-data_consumer_eth-2  | 2023-06-26 13:45:01.040 app.kafka.manager INFO     No event received for 600 seconds from any partition - timed out
bdc-data_consumer_eth-2  | 2023-06-26 13:45:01.044 app.consumer INFO     Finished processing topic 'eth'.
bdc-data_consumer_eth-2  | 2023-06-26 13:45:01.044 app.consumer INFO     number of consumed transactions: 942 | number of processed transactions: 64
bdc-data_consumer_eth-2  | 2023-06-26 13:45:01.045 __main__ INFO     Exiting consumer-eth with code 0
bdc-data_consumer_eth-1  | 2023-06-26 13:45:02.036 app.kafka.manager INFO     No event received for 600 seconds from any partition - timed out
bdc-data_consumer_eth-1  | 2023-06-26 13:45:02.039 app.consumer INFO     Finished processing topic 'eth'.
bdc-data_consumer_eth-1  | 2023-06-26 13:45:02.039 app.consumer INFO     number of consumed transactions: 1216 | number of processed transactions: 59
bdc-data_consumer_eth-2 exited with code 0
bdc-data_consumer_eth-1  | 2023-06-26 13:45:03.936 app.kafka.manager INFO     No event received for 600 seconds from any partition - timed out
bdc-data_consumer_eth-1  | 2023-06-26 13:45:03.942 app.consumer INFO     Finished processing topic 'eth'.
bdc-data_consumer_eth-1  | 2023-06-26 13:45:03.942 app.consumer INFO     number of consumed transactions: 1123 | number of processed transactions: 76
bdc-data_consumer_eth-1  | 2023-06-26 13:45:03.942 __main__ INFO     Exiting consumer-eth with code 0
bdc-data_consumer_eth-1 exited with code 0
^Ccanceled
$
```

Now you can use the collected postgresql data in `./data` to start (or connect) to the database.
```
$ ls -h data
kafka-data  postgresql-data  zookeeper-data
```

If you need to shut down the containers while they are still collecting data, you can use
```
$ bash scripts/stop-prod-eth.sh
```
