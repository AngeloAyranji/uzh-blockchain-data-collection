import logging

from app import init_logger
from app.config import Config
from app.consumer.tx_processor import (
    FullTransactionProcessor,
    LogFilterTransactionProcessor,
    PartialTransactionProcessor,
)
from app.kafka.exceptions import KafkaConsumerPartitionsEmptyError
from app.kafka.manager import KafkaConsumerManager
from app.model import DataCollectionMode
from app.model.abi import ContractABI
from app.utils.data_collector import DataCollector
from app.web3.parser import ContractParser

log = init_logger(__name__)


def kafka_logs_filter(record) -> bool:
    """Filters out some kafka logs"""
    msg = record.getMessage()
    should_filter = msg.startswith("Heartbeat failed for group") or msg.startswith(
        "Group Coordinator Request failed:"
    )
    return not should_filter


class DataConsumer(DataCollector):
    """
    Consume transaction hash from a given Kafka topic and save
    all required data to PostgreSQL.
    """

    def __init__(self, config: Config, contract_abi: ContractABI) -> None:
        super().__init__(config)
        self.kafka_manager: KafkaConsumerManager = KafkaConsumerManager(
            kafka_url=config.kafka_url,
            redis_url=config.redis_url,
            topic=config.kafka_topic,
            event_retrieval_timeout=config.kafka_event_retrieval_timeout,
        )
        # Create a set from all the contracts (we want to save any of these transactions)
        contracts = set()
        for data_cfg in config.data_collection:
            if data_cfg.contracts:
                contracts = contracts.union(set(data_cfg.contracts))

        # Extracts data from web3 smart contracts
        self.contract_parser = ContractParser(
            web3=self.node_connector.w3,
            contract_abi=contract_abi,
            contracts=contracts,
        )

        _tx_processor_args = [
            self.db_manager,
            self.node_connector,
            self.contract_parser,
        ]
        self._default_tx_processor = FullTransactionProcessor(*_tx_processor_args)
        self.tx_processors = {
            DataCollectionMode.FULL: self._default_tx_processor,
            DataCollectionMode.PARTIAL: PartialTransactionProcessor(
                *_tx_processor_args
            ),
            DataCollectionMode.LOG_FILTER: LogFilterTransactionProcessor(
                *_tx_processor_args
            ),
        }

        # Transaction hash of the currently processed transaction
        self._tx_hash = None

        # Number of consumed transactions (from Kafka)
        self._n_consumed_txs = 0
        # Number of processed transactions (saved to PostgreSQL or otherwise processed)
        self._n_processed_txs = 0

        # Apply kafka log filter to filter out some kafka logs
        kafka_logger = logging.getLogger("aiokafka.consumer.group_coordinator")
        kafka_logger.addFilter(kafka_logs_filter)

    async def _on_kafka_event(self, event):
        """Called when a new Kafka event is read from a topic"""
        # Get transaction hash and collection mode from Kafka event
        mode, self._tx_hash = self.decode_kafka_event(event.value.decode())
        # Increment number of consumed transactions
        self._n_consumed_txs += 1
        # Get transaction data
        tx_data, _ = await self.node_connector.get_transaction_data(self._tx_hash)
        (
            tx_receipt_data,
            w3_tx_receipt,
        ) = await self.node_connector.get_transaction_receipt_data(self._tx_hash)

        # Get the correct transaction processor for the given mode
        # otherwise use the default tx processor
        tx_processor = self.tx_processors.get(mode, self._default_tx_processor)
        # Process the transaction
        self._n_processed_txs += await tx_processor.process_transaction(
            tx_data, tx_receipt_data, w3_tx_receipt
        )

    async def start_consuming_data(self) -> int:
        """
        Start an infinite loop of consuming data from a given topic.

        Returns:
            exit_code: 0 if no exceptions encountered during data collection, 1 otherwise
        """
        exit_code = 0
        try:
            # Start consuming events from a Kafka topic and
            # handle them in _on_kafka_event
            await self.kafka_manager.start_consuming(
                on_event_callback=self._on_kafka_event
            )
        except KafkaConsumerPartitionsEmptyError:
            # Raised when a partition doesn't receive a new message for 120 seconds.
            log.info(f"Finished processing topic '{self.kafka_manager.topic}'.")
            # exit_code doesn't change, 0 = success
        except Exception as e:
            # Global handler for any exception, logs the transaction where this occurred
            # and returns exit code 1
            tx_hash = self._tx_hash or "first transaction"
            log.error(
                f"Caught exception during handling of {tx_hash}",
                exc_info=(type(e), e, e.__traceback__),
            )
            exit_code = 1
        finally:
            log.info(
                "number of consumed transactions: {} | number of processed transactions: {}".format(
                    self._n_consumed_txs, self._n_processed_txs
                )
            )
            return exit_code
