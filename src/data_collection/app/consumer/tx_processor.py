from typing import Set, Tuple

from web3.contract import Contract
from web3.types import TxReceipt

from app import init_logger
from app.model.contract import ContractCategory
from app.model.transaction import TransactionData, TransactionReceiptData
from app.web3.transaction_events import get_transaction_events
from app.web3.transaction_events.types import (
    BurnFungibleEvent,
    BurnNonFungibleEvent,
    BurnPairEvent,
    MintFungibleEvent,
    MintNonFungibleEvent,
    MintPairEvent,
    PairCreatedEvent,
    SwapPairEvent,
    TransferFungibleEvent,
    TransferNonFungibleEvent,
)

log = init_logger(__name__)


class TransactionProcessor:
    """Base class for processing any transaction data"""

    def __init__(self, db_manager, node_connector, contract_parser):
        """
        Args:
            db_manager (DatabaseManager): Database manager
            node_connector (NodeConnector): Node connector
            contract_parser (ContractParser): Contract parser
        """
        self.db_manager = db_manager
        self.node_connector = node_connector
        self.contract_parser = contract_parser

    async def _handle_contract_creation(
        self, contract: Contract, tx_data: TransactionData, category: ContractCategory
    ) -> None:
        """Insert required contract data into the database depending on its category"""
        # Transaction is creating a contract if to_address is None
        log.info(
            f"New contract ({contract.address}, {category}) creation in {tx_data.transaction_hash}"
        )

        if category.is_erc:
            # If the contract is an ERC contract,
            # get token contract data (ERC20, ERC721 or ERC1151)
            token_contract_data = await self.contract_parser.get_token_contract_data(
                contract=contract, category=category
            )

            if not token_contract_data:
                log.warning(
                    f"Unknown token contract ABI at address: {contract.address}"
                )
                return

            # Insert token contract data into _contract and _token_contract table
            # in an SQL transaction
            async with self.db_manager.db.transaction():
                # _contract table
                await self.db_manager.insert_contract(
                    address=token_contract_data.address,
                    transaction_hash=tx_data.transaction_hash,
                )
                # _token_contract table
                await self.db_manager.insert_token_contract(
                    **token_contract_data.dict()
                )
        elif category.is_uniswap_pair:
            # If the contract is a pair contract
            pair_contract_data = await self.contract_parser.get_pair_contract_data(
                contract=contract, category=category
            )

            if not pair_contract_data:
                log.warning(f"Unknown pair contract ABI at address: {contract.address}")
                return

            # Insert pair contract data into _contract and _pair_contract table
            # in an SQL transaction
            async with self.db_manager.db.transaction():
                # _contract table
                await self.db_manager.insert_contract(
                    address=pair_contract_data.address,
                    transaction_hash=tx_data.transaction_hash,
                )
                # _token_contract table
                await self.db_manager.insert_pair_contract(**pair_contract_data.dict())

        return contract

    async def _handle_transaction_events(
        self,
        contract: Contract,
        category: ContractCategory,
        tx_data: TransactionData,
        tx_receipt: TxReceipt,
    ) -> Set[int]:
        """Insert transaction events (supply changes) into the database

        Returns:
            log_indices_to_save: a set of 'logIndex' for logs that should be saved
        """
        allowed_events = self.contract_parser.get_contract_events(contract.address)
        # Keep a list of 'logIndex' for logs that should be saved
        log_indices_to_save = set()
        # Supply Change = mints - burns
        amount_changed = 0
        pair_amount0_changed = 0
        pair_amount1_changed = 0
        for event in get_transaction_events(category, contract, tx_receipt):
            # Check if this event should be processed
            if (
                not type(event).__name__ in allowed_events
                or not event.address == contract.address
            ):
                continue
            # Mark this log to be saved
            log_indices_to_save.add(event.log_index)

            if isinstance(event, BurnFungibleEvent):
                amount_changed -= event.value
            elif isinstance(event, MintFungibleEvent):
                amount_changed += event.value
            elif isinstance(event, TransferFungibleEvent):
                pass
            elif isinstance(event, PairCreatedEvent):
                pass
            elif isinstance(event, MintPairEvent):
                pair_amount0_changed += event.amount0
                pair_amount1_changed += event.amount1
            elif isinstance(event, BurnPairEvent):
                pair_amount0_changed -= event.amount0
                pair_amount1_changed -= event.amount1
            elif isinstance(event, SwapPairEvent):
                # Swap is like a mint + burn, with different ratios
                pair_amount0_changed += event.in0
                pair_amount1_changed += event.in1
                pair_amount0_changed -= event.out0
                pair_amount1_changed -= event.out1
            elif isinstance(event, MintNonFungibleEvent):
                pass
            elif isinstance(event, BurnNonFungibleEvent):
                pass
            elif isinstance(event, TransferNonFungibleEvent):
                await self.db_manager.insert_nft_transfer(
                    address=event.address,
                    log_index=event.log_index,
                    from_address=event.src,
                    to_address=event.dst,
                    token_id=event.tokenId,
                    transaction_hash=tx_data.transaction_hash,
                )

        # Insert specific events into DB
        if amount_changed != 0:
            await self.db_manager.insert_contract_supply_change(
                address=event.address,
                transaction_hash=tx_data.transaction_hash,
                amount_changed=amount_changed,
            )

        if pair_amount0_changed != 0 or pair_amount1_changed != 0:
            await self.db_manager.insert_pair_liquidity_change(
                address=contract.address,
                amount0=pair_amount0_changed,
                amount1=pair_amount1_changed,
                transaction_hash=tx_data.transaction_hash,
            )

        # Return log indices that should be saved
        return log_indices_to_save

    async def _handle_transaction(
        self,
        tx_data: TransactionData,
        tx_receipt_data: TransactionReceiptData,
        log_indices_to_save: Set[int] = set([]),
    ) -> None:
        """Insert transaction data into the database"""
        # Get the rest of transaction data - compute transaction fee
        # (according to etherscan): fee = gas price * gas used
        gas_used = tx_receipt_data.gas_used
        tx_fee = tx_data.gas_price * gas_used

        # Insert the transaction and logs data
        await self.db_manager.insert_transaction(
            **tx_data.dict(),
            gas_used=gas_used,
            is_token_tx=True,
            transaction_fee=tx_fee,
        )

        # Insert transaction logs of interest
        logs_to_save = [
            log for log in tx_receipt_data.logs if log.log_index in log_indices_to_save
        ]
        async with self.db_manager.db.transaction():
            for tx_log in logs_to_save:
                await self.db_manager.insert_transaction_logs(**tx_log.dict())

        # check for AND insert internal transactions if needed
        internal_tx_data = await self.node_connector.get_internal_transactions(
            tx_data.transaction_hash
        )
        if internal_tx_data:
            async with self.db_manager.db.transaction():
                for internal_tx in internal_tx_data:
                    await self.db_manager.insert_internal_transaction(
                        **internal_tx.dict(), transaction_hash=tx_data.transaction_hash
                    )

    async def process_transaction(
        self,
        tx_data: TransactionData,
        tx_receipt_data: TransactionReceiptData,
        w3_tx_receipt: TxReceipt,
    ) -> bool:
        """Process transaction data (implemented by subclasses)

        Args:
            tx_data (TransactionData): Transaction data
            tx_receipt_data (TransactionReceiptData): Transaction receipt data
            w3_tx_receipt (TxReceipt): transaction receipt data in web3 format

        Returns:
            bool: True if the transaction was processed, False otherwise
        """
        raise NotImplementedError("Implemented by subclasses")


class PartialTransactionProcessor(TransactionProcessor):
    """Process transactions with mode partial

    Save only the transactions that are related to the
    contracts in the config and only their respective events.

    Note:
        This processor (`process_transaction`) covers 3 distinct cases of when we want to save a transaction:
        1. Regular contract interaction (to_address=address in config)
        2. Contract creation (receipt.contract_address=address in config)
        3. Transaction event (any eventLog.address=address in config)

        If one of the above cases is true, we save the transaction and its events
        (if event.address is in config).
    """

    async def _process_regular_contract_interaction(
        self,
        tx_data: TransactionData,
        tx_receipt_data: TransactionReceiptData,
        w3_tx_receipt: TxReceipt,
    ) -> Tuple[bool, Set[int]]:
        """Process regular contract interaction case (1.) and transaction event case (3.)"""
        should_save_tx, log_indices_to_save = False, set()
        # 1. Regular contract interaction
        # Get unique event addresses from the transaction receipt
        event_addresses = set([log.address for log in tx_receipt_data.logs])
        contract_address = tx_data.to_address
        contract_category = self.contract_parser.get_contract_category(contract_address)

        # Edge case for events whose eventLog.address is in the
        # config but to_address is not in the config
        if not contract_category:
            # For each unique event address in the transaction receipt, check if the event address is in the config
            for address in event_addresses:
                if contract_category := self.contract_parser.get_contract_category(
                    address
                ):
                    # If the address is in the config, try to insert the appropriate logs into DB
                    contract_address = address
                    contract = self.contract_parser.get_contract(
                        contract_address=contract_address,
                        category=contract_category,
                    )
                    # Handle transaction events
                    log_indices = await self._handle_transaction_events(
                        contract=contract,
                        category=contract_category,
                        tx_data=tx_data,
                        tx_receipt=w3_tx_receipt,
                    )
                    # Union of all log indices to save
                    log_indices_to_save = log_indices_to_save.union(log_indices)
            # Only save the transaction and selected logs, if any of the events were relevant
            should_save_tx = len(log_indices_to_save) > 0

        else:
            contract = self.contract_parser.get_contract(
                contract_address=contract_address, category=contract_category
            )
            # Handle transaction events
            log_indices_to_save = await self._handle_transaction_events(
                contract=contract,
                category=contract_category,
                tx_data=tx_data,
                tx_receipt=w3_tx_receipt,
            )
            should_save_tx = True

        return should_save_tx, log_indices_to_save

    async def _process_contract_creation(
        self,
        tx_data: TransactionData,
        tx_receipt_data: TransactionReceiptData,
        w3_tx_receipt: TxReceipt,
    ) -> Tuple[bool, Set[int]]:
        """Process contract creation case (2.)"""
        # 2. Contract creation
        contract_address = tx_receipt_data.contract_address
        contract_category = self.contract_parser.get_contract_category(contract_address)

        if contract_category:
            # Only handle the contract creation if the contract is in the config
            contract = self.contract_parser.get_contract(
                contract_address=contract_address, category=contract_category
            )

            await self._handle_contract_creation(
                contract=contract, tx_data=tx_data, category=contract_category
            )

            # Handle transaction events
            log_indices_to_save = await self._handle_transaction_events(
                contract=contract,
                category=contract_category,
                tx_data=tx_data,
                tx_receipt=w3_tx_receipt,
            )

            return True, log_indices_to_save
        return False, set()

    async def process_transaction(
        self,
        tx_data: TransactionData,
        tx_receipt_data: TransactionReceiptData,
        w3_tx_receipt: TxReceipt,
    ) -> bool:
        should_save_tx, log_indices_to_save = False, set()

        if tx_data.to_address:
            # Case 1. Regular contract interaction or Case 3. Transaction event
            (
                should_save_tx,
                log_indices_to_save,
            ) = await self._process_regular_contract_interaction(
                tx_data, tx_receipt_data, w3_tx_receipt
            )
        elif tx_receipt_data.contract_address:
            # Case 2. Contract creation
            (
                should_save_tx,
                log_indices_to_save,
            ) = await self._process_contract_creation(
                tx_data, tx_receipt_data, w3_tx_receipt
            )

        if should_save_tx:
            # Insert transaction + Internal transactions
            await self._handle_transaction(
                tx_data=tx_data,
                tx_receipt_data=tx_receipt_data,
                log_indices_to_save=log_indices_to_save,
            )

        return should_save_tx


class FullTransactionProcessor(TransactionProcessor):
    """Process transactions with mode full

    Note:
        Directly save every tx data to db without any further processing.
    """

    async def process_transaction(
        self,
        tx_data: TransactionData,
        tx_receipt_data: TransactionReceiptData,
        w3_tx_receipt: TxReceipt,
    ) -> bool:
        # Insert transaction + Logs + Internal transactions
        await self._handle_transaction(
            tx_data=tx_data,
            tx_receipt_data=tx_receipt_data,
            log_indices_to_save=set(map(lambda l: l.log_index, tx_receipt_data.logs)),
        )
        return True


class LogFilterTransactionProcessor(TransactionProcessor):
    """Process transactions with mode log_filter"""

    pass
