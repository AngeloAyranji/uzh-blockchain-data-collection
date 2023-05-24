# Kafka

Modified entrypoint for Kafka to allow the previous zookeper session to expire. Otherwise, Kafka container will exit before zookeeper is able to drop the previous session and the whole app will fail.

Refer to [this link for more info](https://github.com/wurstmeister/kafka-docker/issues/389#issuecomment-800814529).

## Development scripts
A collection of commands useful for development purposes.

### Get number of events per partition
This command shows the amount of events / messages sent to and present in each partition for a given topic (group).

The `LAG` column shows the amount of messages left unconsumed in a given partition.

```
$ docker exec -it bdc-kafka-1 /bin/bash -c '${KAFKA_HOME}/bin/kafka-consumer-groups.sh --describe --bootstrap-server kafka:9092 --group eth'
```