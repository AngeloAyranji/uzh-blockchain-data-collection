from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.consumer.tx_processor import (
    FullTransactionProcessor,
    PartialTransactionProcessor,
    TransactionProcessor,
)


def _tx_processor_factory(
    tx_processor_class: type[TransactionProcessor],
) -> TransactionProcessor:
    processor = tx_processor_class(MagicMock(), Mock(), Mock())
    processor.db_manager.insert_transaction = AsyncMock()
    processor.db_manager.insert_transaction_logs = AsyncMock()
    processor.db_manager.insert_internal_transaction = AsyncMock()
    return processor


@pytest.fixture
def transaction_processor() -> TransactionProcessor:
    return _tx_processor_factory(TransactionProcessor)


@pytest.fixture
def partial_transaction_processor() -> PartialTransactionProcessor:
    return _tx_processor_factory(PartialTransactionProcessor)


@pytest.fixture
def full_transaction_processor() -> FullTransactionProcessor:
    return _tx_processor_factory(FullTransactionProcessor)
