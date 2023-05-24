from unittest.mock import AsyncMock, Mock

import pytest

from app.consumer import kafka_logs_filter
from app.model import DataCollectionMode


class TestKafkaLogsFilter:
    def test_log_filter_filters_logs(self):
        """Test that kafka_logs_filter filters out some logs"""
        record = Mock()
        record.getMessage.return_value = "Heartbeat failed for group"
        assert kafka_logs_filter(record) is False

        record.getMessage.return_value = "Group Coordinator Request failed:"
        assert kafka_logs_filter(record) is False

    def test_log_filter_does_not_filter_logs(self):
        """Test that kafka_logs_filter does not filter out some logs"""
        record = Mock()
        record.getMessage.return_value = "Some other message"
        assert kafka_logs_filter(record) is True


class TestDataConsumer:
    """Tests for methods in DataConsumer"""

    @pytest.mark.parametrize(
        "mode",
        [
            DataCollectionMode.FULL,
            DataCollectionMode.PARTIAL,
            DataCollectionMode.LOG_FILTER,
        ],
    )
    async def test_on_kafka_event(
        self,
        mode,
        transaction_data,
        transaction_receipt_data,
        consumer_factory,
        config_factory,
        data_collection_config_factory,
        contract_config_usdt,
        contract_abi,
    ):
        """Test that a regular event (transaction) is handled for two modes: full and partial"""
        # Arrange
        data_collection_config = data_collection_config_factory([contract_config_usdt])
        data_collection_config.mode = mode
        consumer = consumer_factory(
            config_factory([data_collection_config]),
            contract_abi,
        )
        consumer.node_connector.get_transaction_data = AsyncMock()
        consumer.node_connector.get_transaction_data.return_value = (
            transaction_data,
            None,
        )
        consumer.node_connector.get_transaction_receipt_data = AsyncMock()
        w3_tx_receipt_mock = Mock()
        consumer.node_connector.get_transaction_receipt_data.return_value = (
            transaction_receipt_data,
            w3_tx_receipt_mock,
        )
        process_tx_mock = AsyncMock()
        process_tx_mock.return_value = True
        consumer.tx_processors[mode].process_transaction = process_tx_mock
        kafka_event = Mock()
        kafka_event.value = f"{mode.value}:0x1234".encode()

        # Act
        await consumer._on_kafka_event(event=kafka_event)

        # Assert
        consumer.tx_processors[mode].process_transaction.assert_awaited_once_with(
            transaction_data,
            transaction_receipt_data,
            w3_tx_receipt_mock,
        )
        # consumer.node_connector.get_transaction_data.assert_awaited_once()
        # consumer.node_connector.get_transaction_receipt_data.assert_awaited_once()
        # if mode == DataCollectionMode.FULL:
        #     consumer._consume_full.assert_awaited_once()
        #     consumer._consume_partial.assert_not_awaited()
        # elif mode == DataCollectionMode.PARTIAL:
        #     consumer._consume_full.assert_not_awaited()
        #     consumer._consume_partial.assert_awaited_once()

        assert consumer._n_consumed_txs == 1
        assert consumer._n_processed_txs == 1

    async def test_on_kafka_event_n_processed_txs(
        self,
        transaction_data,
        transaction_receipt_data,
        consumer_factory,
        config_factory,
        data_collection_config_factory,
        contract_config_usdt,
        contract_abi,
    ):
        """Test on_kafka_event doesn't increment n_processed_txs if transaction is not processed"""
        # Arrange
        mode = DataCollectionMode.PARTIAL
        data_collection_config = data_collection_config_factory([contract_config_usdt])
        data_collection_config.mode = mode
        consumer = consumer_factory(
            config_factory([data_collection_config]),
            contract_abi,
        )
        consumer.node_connector.get_transaction_data = AsyncMock()
        consumer.node_connector.get_transaction_data.return_value = (
            transaction_data,
            Mock(),
        )
        consumer.node_connector.get_transaction_receipt_data = AsyncMock()
        w3_tx_receipt_mock = Mock()
        consumer.node_connector.get_transaction_receipt_data.return_value = (
            transaction_receipt_data,
            w3_tx_receipt_mock,
        )
        process_tx_mock = AsyncMock()
        process_tx_mock.return_value = False
        consumer.tx_processors[mode].process_transaction = process_tx_mock
        kafka_event = Mock()
        kafka_event.value = f"partial:0x1234".encode()

        # Act
        await consumer._on_kafka_event(event=kafka_event)

        # Assert
        consumer.tx_processors[mode].process_transaction.assert_awaited_once_with(
            transaction_data,
            transaction_receipt_data,
            w3_tx_receipt_mock,
        )
        assert consumer._n_processed_txs == 0
