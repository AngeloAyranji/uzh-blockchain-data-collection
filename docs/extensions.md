# Extensions
## Add new Event
TODO: Description of how to add an event goes here
## Add new Contract ABI
TODO: Description of how to add a Contract ABI goes here
## Add new data collection mode

Adding a new data collection / processing mode can be useful if you want to make use of parallelization via Kafka workers. This is an example on how we added the `get_logs` data collection mode.

1. Add new `DataCollectionMode` enum value in [app/model/__init__.py](/src/data_collection/app/model/__init__.py).
  * `GET_LOGS = auto()`
  * add documentation if needed
2. Update [app/config.py](/src/data_collection/app/config.py) if needed
  * (e.g. get_logs method requires 'params' field)
    ```
    class DataCollectionConfig(BaseSettings):
        ...
        params: Optional[Dict[str, Any]]
        """Can be none, required when used with DataCollectionMode.GET_LOGS

        Note:
            This field has to have the same JSON format as the eth_getLogs RPC method:
            https://www.quicknode.com/docs/ethereum/eth_getLogs
        """
    ```
3. Update [app/producer.py](/src/data_collection/app/producer.py) to account for the new `DataCollectionMode`
  * add new method `_start_get_logs_producer()` to `DataProducer`.
    ```
    async def _start_get_logs_producer(
        self, data_collection_cfg: DataCollectionConfig
    ):
        """Start a producer that uses the `eth_getLogs` RPC method to get all the transactions"""
    ```
  * add `match` case for the new `DataCollectionMode` in `_start_producer_task()` method:
    ```
    case DataCollectionMode.GET_LOGS:
        return asyncio.create_task(
            self._start_get_logs_producer(data_collection_cfg)
        )
    ```
  * implement `_start_get_logs_producer()`:
  * call `eth_getLogs` and then send all transactions to Kafka
    ```
        """Start a producer that uses the `eth_getLogs` RPC method to get all the transactions"""
        # Get logs
        logs = await self.node_connector.w3.eth.get_logs(filter_params=data_collection_cfg.params)

        # Send them to Kafka
        if logs:
            # Encode the logs as kafka events
            messages = [
                self.encode_kafka_event(log["transactionHash"].hex(), data_collection_cfg.mode)
                for log in logs
            ]
            # Send all the transaction hashes to Kafka so consumers can process them
            await self.kafka_manager.send_batch(msgs=messages)

        log.info(f"Finished collecting {len(logs)} logs")
    ```
4. (Optional) implement a new transaction processor for the new DataCollectionMode in [app/consumer/tx_processor.py](/src/data_collection/app/consumer/tx_processor.py)
  * Create new class for `GetLogsTransactionProcessor`
  * Update `self.tx_processors` in `DataConsumer` to use this new `GetLogsTransactionProcessor`
  ```
    self.tx_processors = {
        ...,
        DataCollectionMode.GET_LOGS: GetLogsTransactionProcessor(*_tx_processor_args)
    }
  ```
5. Update the JSON config and run the app

## Support more blockchains
TODO:
