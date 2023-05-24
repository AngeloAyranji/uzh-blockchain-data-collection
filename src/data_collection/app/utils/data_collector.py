from __future__ import annotations

from typing import Tuple

from app.config import Config
from app.db.manager import DatabaseManager
from app.kafka.manager import KafkaManager
from app.model import DataCollectionMode
from app.web3.node_connector import NodeConnector


class DataCollector:
    """
    Superclass for DataConsumer and DataProducer

    Manages Kafka, PostgreSQL and node connections.
    """

    KAFKA_EVENT_SEPARATOR = ":"

    def __init__(self, config: Config) -> None:
        # Initialize the manager objects
        self.kafka_manager: KafkaManager = None
        self.node_connector = NodeConnector(
            node_url=config.node_url,
            timeout=config.web3_requests_timeout,
            retry_limit=config.web3_requests_retry_limit,
            retry_delay=config.web3_requests_retry_delay,
        )
        self.db_manager = DatabaseManager(
            postgresql_dsn=config.db_dsn, node_name=config.kafka_topic
        )

    async def __aenter__(self) -> DataCollector:
        # Connect to Kafka
        await self.kafka_manager.connect()
        # Connect to the db
        await self.db_manager.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.kafka_manager.disconnect()

    def encode_kafka_event(self, tx_hash: str, mode: DataCollectionMode) -> str:
        """Create kafka event from a transaction hash and a data collection mode"""
        sep = self.KAFKA_EVENT_SEPARATOR
        return f"{mode.value}{sep}{tx_hash}"

    def decode_kafka_event(self, event: str) -> Tuple[str, DataCollectionMode]:
        """Decode a kafka event into a transaction hash and a data collection mode"""
        sep = self.KAFKA_EVENT_SEPARATOR
        mode_str, tx_hash = event.split(sep)
        return DataCollectionMode(mode_str), tx_hash
