from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.consumer.tx_processor import (
    FullTransactionProcessor,
    LogFilterTransactionProcessor,
    PartialTransactionProcessor,
)
from app.db.manager import DatabaseManager
from app.model.contract import ContractCategory
from app.model.transaction import InternalTransactionData
from app.web3.transaction_events.types import (
    BurnFungibleEvent,
    BurnPairEvent,
    MintFungibleEvent,
    MintPairEvent,
    TransferFungibleEvent,
)


class TestTransactionProcessor:
    """Tests for TransactionProcessor base class methods"""

    def test_handle_contract_creation(self):
        """Test that handle_contract_creation method is called"""
        # TODO: implement
        pass

    async def test_handle_transaction_without_internal_txs(
        self, transaction_data, transaction_receipt_data, transaction_processor
    ):
        """Test that in _handle_transaction insert to db is called once for a transaction without internal transactions"""
        # Arrange
        get_internal_transactions_mock = AsyncMock()
        get_internal_transactions_mock.return_value = []
        transaction_processor.node_connector.get_internal_transactions = AsyncMock()

        # Act
        await transaction_processor._handle_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            log_indices_to_save=set([]),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction.assert_awaited_once_with(
            **transaction_data.dict(),
            gas_used=transaction_receipt_data.gas_used,
            is_token_tx=True,
            transaction_fee=transaction_data.gas_price
            * transaction_receipt_data.gas_used,
        )
        transaction_processor.db_manager.insert_internal_transaction.assert_not_awaited()
        transaction_processor.db_manager.insert_transaction_logs.assert_not_awaited()

    async def test_handle_transaction_with_internal_txs(
        self,
        transaction_processor,
        transaction_data,
        transaction_receipt_data,
    ):
        """Test that insert to db is called once for a transaction and all internal transactions"""
        # Arrange
        internal_tx_data = InternalTransactionData(
            **{
                "from": "0x0000000",
                "to": "0x0000000",
                "value": "0x1337",
                "gasUsed": "0x1337",
                "gas": "0x1337",
                "input": "0x0000000",
                "callType": "call",
            }
        )
        get_internal_transactions_mock = AsyncMock()
        get_internal_transactions_mock.return_value = [
            internal_tx_data,
            internal_tx_data,
        ]
        transaction_processor.node_connector.get_internal_transactions = (
            get_internal_transactions_mock
        )

        # Act
        await transaction_processor._handle_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            log_indices_to_save=set([]),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction.assert_awaited_once_with(
            **transaction_data.dict(),
            gas_used=transaction_receipt_data.gas_used,
            is_token_tx=True,
            transaction_fee=transaction_data.gas_price
            * transaction_receipt_data.gas_used,
        )
        transaction_processor.node_connector.get_internal_transactions.assert_awaited_once_with(
            transaction_data.transaction_hash
        )
        assert (
            transaction_processor.db_manager.insert_internal_transaction.await_count
            == 2
        )
        transaction_processor.db_manager.insert_internal_transaction.assert_awaited_with(
            **internal_tx_data.dict(),
            transaction_hash=transaction_data.transaction_hash,
        )
        transaction_processor.db_manager.insert_transaction_logs.assert_not_awaited()

    async def test_handle_transaction_with_logs(
        self,
        transaction_processor,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that insert to db is called once for a transaction and all logs"""
        # Arrange
        transaction_receipt_data.logs = [transaction_logs_data, transaction_logs_data]
        transaction_receipt_data.logs[0].log_index = 230
        transaction_receipt_data.logs[1].log_index = 231
        transaction_processor.node_connector.get_internal_transactions = AsyncMock()

        # Act
        await transaction_processor._handle_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            log_indices_to_save=set([230, 231]),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction.assert_awaited_once_with(
            **transaction_data.dict(),
            gas_used=transaction_receipt_data.gas_used,
            is_token_tx=True,
            transaction_fee=transaction_data.gas_price
            * transaction_receipt_data.gas_used,
        )
        transaction_processor.db_manager.insert_internal_transaction.assert_not_awaited()
        assert transaction_processor.db_manager.insert_transaction_logs.await_count == 2
        transaction_processor.db_manager.insert_transaction_logs.assert_awaited_with(
            **transaction_logs_data.dict(),
        )

    async def test_transaction_fee_correct(self):
        """Test that the transaction fee is calculated correctly in _handle_transaction"""
        # TODO: Implement
        pass

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_no_event_inserted(
        self,
        mock_get_transaction_events,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that no event is inserted if no event was found"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            "TransferFungibleEvent",
            "MintFungibleEvent",
            "BurnFungibleEvent",
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = []
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction_logs.assert_not_awaited()
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([])

    @patch("app.consumer.tx_processor.get_transaction_events")
    @pytest.mark.parametrize(
        "event",
        [
            "transfer_fungible_event",
            "mint_fungible_event",
            "burn_fungible_event",
            "mint_pair_event",
            "burn_pair_event",
            "swap_pair_event",
        ],
    )
    async def test_no_event_inserted_if_not_in_config(
        self,
        mock_get_transaction_events,
        event,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
        request,
    ):
        """Test that no event is inserted if event found but is not in config"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = []
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            request.getfixturevalue(event),
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction_logs.assert_not_awaited()
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([])

    @patch("app.consumer.tx_processor.get_transaction_events")
    @pytest.mark.parametrize(
        "event,supply_change,liquidity_change",
        [
            ("transfer_fungible_event", None, None),
            ("transfer_non_fungible_event", None, None),
            ("mint_fungible_event", 1500, None),
            ("burn_fungible_event", -1500, None),
            ("mint_pair_event", None, (1500, 2500)),
            ("burn_pair_event", None, (-1500, -2500)),
            ("swap_pair_event", None, (200, 600)),
        ],
    )
    async def test_event_inserted_if_in_config(
        self,
        mock_get_transaction_events,
        event,
        supply_change,
        liquidity_change,
        transaction_processor,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
        request,
    ):
        """Test every event is inserted if event found and is present in config"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            request.getfixturevalue(event).__class__.__name__
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            request.getfixturevalue(event),
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = request.getfixturevalue(event).address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()
        transaction_processor.db_manager.insert_nft_transfer = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        if supply_change:
            transaction_processor.db_manager.insert_contract_supply_change.assert_awaited_once_with(
                address=request.getfixturevalue(event).address,
                transaction_hash=transaction_data.transaction_hash,
                amount_changed=supply_change,
            )
        else:
            transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        if liquidity_change:
            transaction_processor.db_manager.insert_pair_liquidity_change.assert_awaited_once_with(
                address=request.getfixturevalue(event).address,
                amount0=liquidity_change[0],
                amount1=liquidity_change[1],
                transaction_hash=transaction_data.transaction_hash,
            )
        else:
            transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([1337])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_transfer_fungible_to_dead_address_event_inserted(
        self,
        mock_get_transaction_events,
        dead_address,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that transfer to dead address is inserted as a log once and as a burn supply change"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            "TransferFungibleEvent",
            "BurnFungibleEvent",
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            BurnFungibleEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                value=2000,
            ),
            TransferFungibleEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                src="0xF00D",
                dst=dead_address,
                value=2000,
            ),
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_transaction_logs = AsyncMock()
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_contract_supply_change.assert_awaited_once_with(
            address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            transaction_hash="0xa76bef720a7093e99ce5532988623aaf62b490ecba52d1a94cb6e118ccb56822",
            amount_changed=-2000,
        )
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([1337])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_transfer_fungible_to_dead_address_event_not_inserted_if_not_in_config(
        self,
        mock_get_transaction_events,
        dead_address,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that transfer to dead address is not inserted as a log nor as a supply change event if not in config"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = []
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            TransferFungibleEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                src="0xF00D",
                dst=dead_address,
                value=1500,
            ),
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction_logs.assert_not_awaited()
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_transfer_fungible_from_dead_address_event_inserted(
        self,
        mock_get_transaction_events,
        dead_address,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that transfer from dead address is inserted as a log once and as a mint supply change"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            "TransferFungibleEvent",
            "MintFungibleEvent",
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            TransferFungibleEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                src=dead_address,
                dst="0xCAFE",
                value=2500,
            ),
            MintFungibleEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                value=1500,
            ),
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_contract_supply_change.assert_awaited_once_with(
            address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            transaction_hash="0xa76bef720a7093e99ce5532988623aaf62b490ecba52d1a94cb6e118ccb56822",
            amount_changed=1500,
        )
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([1337])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_transfer_fungible_from_dead_address_event_not_inserted_if_not_in_config(
        self,
        mock_get_transaction_events,
        dead_address,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that transfer from dead address is not inserted as a log nor as a supply change event if not in config"""
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = []
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            TransferFungibleEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                src=dead_address,
                dst="0xCAFE",
                value=1500,
            )
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_transaction_logs.assert_not_awaited()
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        assert result == set([])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_mint_pair_event_from_dead_address(
        self,
        mock_get_transaction_events,
        dead_address,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that mint pair event from dead address is inserted as log and mint event"""
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = ["MintPairEvent"]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            MintPairEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                sender=dead_address,
                amount0=1500,
                amount1=2500,
            )
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_awaited_once_with(
            address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            amount0=1500,
            amount1=2500,
            transaction_hash="0xa76bef720a7093e99ce5532988623aaf62b490ecba52d1a94cb6e118ccb56822",
        )
        assert result == set([1337])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_burn_pair_event_from_dead_address_inserted(
        self,
        mock_get_transaction_events,
        dead_address,
        transaction_processor,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that burn pair event to dead address is inserted as log and burn event"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = ["BurnPairEvent"]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            BurnPairEvent(
                address=contract_config_usdt.address,
                log_index=1337,
                src="0xCAFE",
                dst=dead_address,
                amount0=1500,
                amount1=2500,
            )
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_transaction_logs = AsyncMock()
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_awaited_once_with(
            address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            amount0=-1500,
            amount1=-2500,
            transaction_hash="0xa76bef720a7093e99ce5532988623aaf62b490ecba52d1a94cb6e118ccb56822",
        )
        assert result == set([1337])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_transfer_non_fungible_inserts_nft_transfer(
        self,
        mock_get_transaction_events,
        transaction_processor,
        contract_config_bayc,
        transfer_non_fungible_event,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test TransferNonFungibleEvent is inserted as NFT transfer"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = ["TransferNonFungibleEvent"]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_get_transaction_events.return_value = [
            transfer_non_fungible_event,
        ]
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_mock = Mock()
        contract_mock.address = contract_config_bayc.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()
        transaction_processor.db_manager.insert_nft_transfer = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        transaction_processor.db_manager.insert_nft_transfer.assert_awaited_once_with(
            address="0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D",
            log_index=1337,
            from_address="0xF00D",
            to_address="0xCAFE",
            token_id=1337,
            transaction_hash=transaction_data.transaction_hash,
        )
        assert result == set([1337])

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_mint_burn_fungible_combination(
        self,
        mock_get_transaction_events,
        transaction_processor,
        burn_fungible_event,
        mint_fungible_event,
        contract_config_usdt,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that multiple mint/burn fungible events together are handled correctly"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            "MintFungibleEvent",
            "BurnFungibleEvent",
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_events = [
            burn_fungible_event,
            burn_fungible_event.copy(),
            mint_fungible_event,
            mint_fungible_event.copy(),
            mint_fungible_event.copy(),
        ]
        mock_get_transaction_events.return_value = mock_events
        logs = [transaction_logs_data] * 5
        for i, log in enumerate(logs):
            log.log_index = 1337 + i
            mock_events[i].log_index = 1337 + i
        transaction_receipt_data.logs = logs
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        assert len(result) == 5
        transaction_processor.db_manager.insert_contract_supply_change.assert_awaited_once_with(
            address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
            transaction_hash="0xa76bef720a7093e99ce5532988623aaf62b490ecba52d1a94cb6e118ccb56822",
            amount_changed=1500,
        )
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_mint_burn_swap_pair_combination(
        self,
        mock_get_transaction_events,
        transaction_processor,
        burn_pair_event,
        mint_pair_event,
        swap_pair_event,
        contract_config_pair_usdc_weth,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test that multiple mint/burn/swap pair events together are handled correctly"""
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            "MintPairEvent",
            "BurnPairEvent",
            "SwapPairEvent",
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        mock_events = [
            burn_pair_event,
            mint_pair_event,
            burn_pair_event.copy(),
            mint_pair_event.copy(),
            swap_pair_event,
            swap_pair_event.copy(),
            mint_pair_event.copy(),
        ]
        mock_get_transaction_events.return_value = mock_events
        logs = [transaction_logs_data] * 7
        for i, log in enumerate(logs):
            log.log_index = 1337 + i
            mock_events[i].log_index = 1337 + i
        transaction_receipt_data.logs = logs
        contract_mock = Mock()
        contract_mock.address = contract_config_pair_usdc_weth.address
        transaction_processor.db_manager.insert_transaction_logs = AsyncMock()
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        assert len(result) == 7
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_awaited_with(
            address=contract_config_pair_usdc_weth.address,
            amount0=1900,
            amount1=3700,
            transaction_hash=transaction_data.transaction_hash,
        )

    @patch("app.consumer.tx_processor.get_transaction_events")
    async def test_handle_transaction_events_skipped_if_event_addr_not_matching(
        self,
        mock_get_transaction_events,
        transaction_processor,
        transaction_data,
        contract_config_usdt,
        transfer_fungible_event,
        mint_fungible_event,
        burn_fungible_event,
    ):
        """Test that _handle_transaction_events is skipped if event address does not
        match contract address.
        """
        # Arrange
        get_contract_events_mock = Mock()
        get_contract_events_mock.return_value = [
            "TransferFungibleEvent",
            "MintFungibleEvent",
            "BurnFungibleEvent",
        ]
        transaction_processor.contract_parser.get_contract_events = (
            get_contract_events_mock
        )
        transfer_fungible_event.address = "0x1234"
        mint_fungible_event.address = "0x1234"
        burn_fungible_event.address = "0x1234"
        mock_get_transaction_events.return_value = [
            transfer_fungible_event,
            burn_fungible_event,
            mint_fungible_event,
        ]
        contract_mock = Mock()
        contract_mock.address = contract_config_usdt.address
        transaction_processor.db_manager.insert_contract_supply_change = AsyncMock()
        transaction_processor.db_manager.insert_pair_liquidity_change = AsyncMock()
        transaction_processor.db_manager.insert_nft_transfer = AsyncMock()

        # Act
        result = await transaction_processor._handle_transaction_events(
            contract=contract_mock,
            category=Mock(),
            tx_data=transaction_data,
            tx_receipt=Mock(),
        )

        # Assert
        transaction_processor.db_manager.insert_contract_supply_change.assert_not_awaited()
        transaction_processor.db_manager.insert_pair_liquidity_change.assert_not_awaited()
        transaction_processor.db_manager.insert_nft_transfer.assert_not_awaited()
        assert result == set([])


class TestPartialTransactionProcessor:
    """Tests for PartialTransactionProcessor methods"""

    async def test_process_transaction_case1_and_case3(
        self, partial_transaction_processor, transaction_data, transaction_receipt_data
    ):
        """Test case 1. (Regular contract interaction) and case 3. (Transaction event)
        in process_transaction gets saved into db
        """
        # Arrange
        interaction_mock = AsyncMock()
        interaction_mock.return_value = (True, set())
        partial_transaction_processor._process_regular_contract_interaction = (
            interaction_mock
        )
        partial_transaction_processor._process_contract_creation = AsyncMock()
        w3_tx_receipt_mock = Mock()
        partial_transaction_processor._handle_transaction = AsyncMock()

        # Act
        saved = await partial_transaction_processor.process_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=w3_tx_receipt_mock,
        )

        # Assert
        partial_transaction_processor._process_regular_contract_interaction.assert_awaited_once_with(
            transaction_data, transaction_receipt_data, w3_tx_receipt_mock
        )
        partial_transaction_processor._process_contract_creation.assert_not_awaited()
        partial_transaction_processor._handle_transaction.assert_awaited_once_with(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            log_indices_to_save=set(),
        )
        assert saved is True

    async def test_process_transaction_case2(
        self,
        partial_transaction_processor,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test case 2. (Contract creation) in process_transaction gets saved into db"""
        # Arrange
        transaction_data.to_address = None
        transaction_receipt_data.contract_address = "0x1234"
        transaction_receipt_data.logs = [transaction_logs_data]
        contract_creation_mock = AsyncMock()
        contract_creation_mock.return_value = (True, set([1337]))
        partial_transaction_processor._process_contract_creation = (
            contract_creation_mock
        )
        partial_transaction_processor._process_regular_contract_interaction = (
            AsyncMock()
        )
        w3_tx_receipt_mock = Mock()
        partial_transaction_processor._handle_transaction = AsyncMock()

        # Act
        saved = await partial_transaction_processor.process_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=w3_tx_receipt_mock,
        )

        # Assert
        partial_transaction_processor._process_regular_contract_interaction.assert_not_awaited()
        partial_transaction_processor._process_contract_creation.assert_awaited_once_with(
            transaction_data, transaction_receipt_data, w3_tx_receipt_mock
        )
        partial_transaction_processor._handle_transaction.assert_awaited_once_with(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            log_indices_to_save=set([1337]),
        )
        assert saved is True

    async def test_process_transaction_doesnt_save_tx(
        self,
        partial_transaction_processor,
        transaction_data,
        transaction_receipt_data,
    ):
        """Test that process_transaction doesn't save transaction if should_save_tx is False"""
        partial_transaction_processor._handle_transaction = AsyncMock()
        transaction_data.to_address = None
        transaction_receipt_data.contract_address = None

        saved = await partial_transaction_processor.process_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=Mock(),
        )

        partial_transaction_processor._handle_transaction.assert_not_awaited()
        assert saved is False

    async def test_process_regular_contract_interaction_unknown_contract_flow(
        self, partial_transaction_processor, transaction_data, transaction_receipt_data
    ):
        """Test _process_regular_contract_interaction flow if an unknown contract is encountered"""
        transaction_data.to_address = "0x1234"
        transaction_receipt_data.contract_address = "0x1234"
        partial_transaction_processor._handle_transaction = AsyncMock()
        partial_transaction_processor._handle_transaction_events = AsyncMock()
        partial_transaction_processor.contract_parser.get_contract_category.return_value = (
            None
        )

        await partial_transaction_processor._process_regular_contract_interaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=Mock(),
        )

        partial_transaction_processor._handle_transaction.assert_not_awaited()
        partial_transaction_processor._handle_transaction_events.assert_not_awaited()

    async def test_process_regular_contract_interaction_known_contract_flow(
        self,
        partial_transaction_processor,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
        contract_config_usdt,
    ):
        """Test _process_regular_contract_interaction flow if a known contract is encountered"""
        # Arrange
        transaction_data.to_address = contract_config_usdt.address
        transaction_receipt_data.contract_address = contract_config_usdt.address
        partial_transaction_processor._handle_contract_creation = AsyncMock()
        partial_transaction_processor._handle_transaction = AsyncMock()
        transaction_receipt_data.logs = [transaction_logs_data]
        _handle_tx_events_mock = AsyncMock()
        _handle_tx_events_mock.return_value = set(
            [transaction_receipt_data.logs[0].log_index]
        )
        partial_transaction_processor._handle_transaction_events = (
            _handle_tx_events_mock
        )
        partial_transaction_processor.contract_parser.get_contract_category.return_value = ContractCategory(
            contract_config_usdt.category
        )
        contract_mock = Mock()
        partial_transaction_processor.contract_parser.get_contract.return_value = (
            contract_mock
        )
        w3_tx_receipt = Mock()

        # Act
        (
            should_save_tx,
            log_indices,
        ) = await partial_transaction_processor._process_regular_contract_interaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=w3_tx_receipt,
        )

        # Assert
        assert should_save_tx is True
        assert log_indices == set([1337])
        partial_transaction_processor._handle_transaction_events.assert_awaited_once_with(
            contract=contract_mock,
            category=ContractCategory.ERC20,
            tx_data=transaction_data,
            tx_receipt=w3_tx_receipt,
        )

    async def test_process_regular_contract_interaction_events_only_flow(
        self,
        partial_transaction_processor,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test _process_regular_contract_interaction flow if only events with
        addresses from config are encountered
        """
        transaction_data.to_address = "0x12347365"
        transaction_receipt_data.contract_address = None
        logs1 = transaction_logs_data.copy()
        logs1.address = "0x1234"
        logs1.log_index = 1337
        logs2 = transaction_logs_data.copy()
        logs2.address = "0x1234F00D"
        logs2.log_index = 1338
        logs3 = transaction_logs_data.copy()
        logs3.log_index = 1339
        transaction_receipt_data.logs = [logs1, logs2, logs3]
        partial_transaction_processor._handle_transaction = AsyncMock()
        partial_transaction_processor._handle_transaction_events = AsyncMock()
        partial_transaction_processor._handle_transaction_events.return_value = set(
            [1337]
        )

        def get_contract_category(address):
            if address == "0x1234":
                return ContractCategory.ERC20
            return None

        partial_transaction_processor.contract_parser.get_contract_category = MagicMock(
            side_effect=get_contract_category
        )

        # Act
        (
            should_save,
            log_indices,
        ) = await partial_transaction_processor._process_regular_contract_interaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=Mock(),
        )

        # Assert
        partial_transaction_processor._handle_transaction.assert_not_awaited()
        assert (
            partial_transaction_processor.contract_parser.get_contract_category.call_count
            == 4
        )
        partial_transaction_processor._handle_transaction_events.await_count == 1
        assert should_save is True
        assert log_indices == set([1337])

    async def test_process_contract_creation_flow_for_known_contract(
        self,
        partial_transaction_processor,
        transaction_data,
        transaction_receipt_data,
        contract_config_usdt,
    ):
        """Test _process_contract_creation flow if a contract is being created within
        this transaction for a known contract
        """
        transaction_data.to_address = None
        transaction_receipt_data.contract_address = contract_config_usdt.address
        partial_transaction_processor._handle_contract_creation = AsyncMock()
        partial_transaction_processor._handle_transaction = AsyncMock()
        _handle_tx_events_mock = AsyncMock()
        _handle_tx_events_mock.return_value = set([1337])
        partial_transaction_processor._handle_transaction_events = (
            _handle_tx_events_mock
        )
        partial_transaction_processor.contract_parser.get_contract_category.return_value = ContractCategory(
            contract_config_usdt.category
        )
        contract_mock = Mock()
        partial_transaction_processor.contract_parser.get_contract.return_value = (
            contract_mock
        )
        w3_tx_receipt = Mock()

        (
            should_save_tx,
            log_indices_to_save,
        ) = await partial_transaction_processor._process_contract_creation(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=w3_tx_receipt,
        )

        # Assert
        assert should_save_tx is True
        assert log_indices_to_save == set([1337])
        partial_transaction_processor._handle_transaction_events.assert_awaited_once_with(
            contract=contract_mock,
            category=ContractCategory.ERC20,
            tx_data=transaction_data,
            tx_receipt=w3_tx_receipt,
        )
        partial_transaction_processor._handle_contract_creation.assert_awaited_once_with(
            contract=contract_mock,
            tx_data=transaction_data,
            category=ContractCategory.ERC20,
        )

    async def test_process_contract_creation_flow_for_unknown_contract(
        self,
        partial_transaction_processor,
        transaction_data,
        transaction_receipt_data,
        contract_config_usdt,
    ):
        """Test _process_contract_creation flow if a contract is being created within
        this transaction for an unknown contract
        """
        transaction_data.to_address = None
        transaction_receipt_data.contract_address = "0x1337"
        partial_transaction_processor._handle_contract_creation = AsyncMock()
        partial_transaction_processor._handle_transaction = AsyncMock()
        _handle_tx_events_mock = AsyncMock()
        _handle_tx_events_mock.return_value = set()
        partial_transaction_processor._handle_transaction_events = (
            _handle_tx_events_mock
        )
        partial_transaction_processor.contract_parser.get_contract_category.return_value = (
            None
        )
        w3_tx_receipt = Mock()

        (
            should_save_tx,
            log_indices_to_save,
        ) = await partial_transaction_processor._process_contract_creation(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=w3_tx_receipt,
        )

        # Assert
        assert should_save_tx is False
        assert log_indices_to_save == set()
        partial_transaction_processor._handle_transaction_events.assert_not_awaited()
        partial_transaction_processor._handle_contract_creation.assert_not_awaited()


class TestFullTransactionProcessor:
    """Tests for FullTransactionProcessor methods"""

    async def test_process_transaction_flow(
        self,
        full_transaction_processor,
        transaction_data,
        transaction_receipt_data,
        transaction_logs_data,
    ):
        """Test process_transaction flow"""
        full_transaction_processor._handle_transaction = AsyncMock()
        full_transaction_processor.db_manager.insert_transaction_logs = AsyncMock()
        _handle_tx_events_mock = AsyncMock()
        _handle_tx_events_mock.return_value = set([1337])
        full_transaction_processor._handle_transaction_events = _handle_tx_events_mock
        transaction_receipt_data.logs = [transaction_logs_data]

        saved = await full_transaction_processor.process_transaction(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            w3_tx_receipt=Mock(),
        )

        # Assert
        full_transaction_processor._handle_transaction.assert_awaited_once_with(
            tx_data=transaction_data,
            tx_receipt_data=transaction_receipt_data,
            log_indices_to_save=set([1337]),
        )
        assert saved is True


class TestogFilterTransactionProcessor:
    """Tests for LogFilterTransactionProcessor methods"""

    pass
