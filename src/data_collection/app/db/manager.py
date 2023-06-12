from datetime import datetime
from typing import Any, List, Optional, Union

import asyncpg

from app import init_logger
from app.db.exceptions import UnknownBlockIdentifier

log = init_logger(__name__)


class DatabaseManager:
    """
    Manage the PostgreSQL connection and CRUD operations.

    https://magicstack.github.io/asyncpg/current/usage.html
    """

    def __init__(self, postgresql_dsn: str, node_name: str) -> None:
        """
        Args:
            postgresql_dsn: connection arguments in URI format
                            e.g. postgres://user:password@host:port/database
            node_name: the type of the node (eth, etc, bsc), selects matching
                        tables for all operations
        """
        self.dsn: str = postgresql_dsn
        self.node_name = node_name
        self.db: asyncpg.Connection = None

    async def connect(self):
        """Connects to the PostgreSQL database."""
        log.debug(f"Connecting to {self.dsn}")
        self.db = await asyncpg.connect(dsn=self.dsn)
        log.debug("Connected to PostgreSQL")

    async def disconnect(self):
        """Disconnect from PostgreSQL"""
        await self.db.close()
        log.debug("Disconnected from PostgreSQL")

    async def insert_block(
        self,
        block_number: int,
        block_hash: str,
        nonce: str,
        difficulty: int,
        gas_limit: int,
        gas_used: int,
        timestamp: datetime,
        miner: str,
        parent_hash: str,
        block_reward: float,
    ):
        """
        Insert block data into <node>_block table.
        """

        table = f"{self.node_name}_block"

        await self.db.execute(
            f"""
            INSERT INTO {table} (block_number, block_hash, nonce, difficulty, gas_limit, gas_used, timestamp, miner, parent_hash, block_reward)
            VALUES ($1, $2, $3,$4, $5, $6,$7,$8, $9, $10)
            ON CONFLICT (block_number) DO NOTHING;
            """,
            block_number,
            block_hash,
            nonce,
            difficulty,
            gas_limit,
            gas_used,
            timestamp,
            miner,
            parent_hash,
            block_reward,
        )

    async def insert_transaction(
        self,
        transaction_hash: str,
        block_number: int,
        from_address: str,
        to_address: str,
        value: float,
        transaction_fee: float,
        gas_price: float,
        gas_limit: int,
        gas_used: int,
        is_token_tx: bool,
        input_data: str,
    ):
        """
        Insert transaction data into <node>_transaction table.
        """

        table = f"{self.node_name}_transaction"

        await self.db.execute(
            f"""
            INSERT INTO {table} (transaction_hash, block_number, from_address, to_address, value, transaction_fee, gas_price, gas_limit, gas_used, is_token_tx, input_data)
            VALUES ($1, $2, $3,$4, $5, $6,$7,$8, $9, $10, $11)
            ON CONFLICT (transaction_hash) DO NOTHING;
            """,
            transaction_hash,
            block_number,
            from_address,
            to_address,
            value,
            transaction_fee,
            gas_price,
            gas_limit,
            gas_used,
            is_token_tx,
            input_data,
        )

    # FIXME: not really sure about the data schema here, might be quite different
    # for example the gas stuff might not be needed
    async def insert_internal_transaction(
        self,
        transaction_hash: str,
        from_address: str,
        to_address: str,
        value: float,
        gas_limit: float,
        gas_used: int,
        input_data: str,
        call_type: str,
    ):
        """
        Insert internal transaction data into <node>_internal_transaction table.
        """
        table = f"{self.node_name}_internal_transaction"

        await self.db.execute(
            f"""
            INSERT INTO {table} (transaction_hash, from_address, to_address, value, gas_limit, gas_used, input_data, call_type)
            VALUES ($1, $2, $3,$4, $5, $6,$7,$8);
            """,
            transaction_hash,
            from_address,
            to_address,
            value,
            gas_limit,
            gas_used,
            input_data,
            call_type,
        )

    async def insert_transaction_logs(
        self,
        transaction_hash: str,
        address: str,
        log_index: int,
        data: str,
        removed: bool,
        topics: list[str],
    ):
        """
        Insert transaction logs data into <node>_transaction_logs table.
        """

        table = f"{self.node_name}_transaction_logs"

        await self.db.execute(
            f"""
            INSERT INTO {table} (transaction_hash, address, log_index, data, removed, topics)
            VALUES ($1, $2, $3,$4, $5, $6)
            ON CONFLICT (transaction_hash, log_index) DO NOTHING;
            """,
            transaction_hash,
            address,
            log_index,
            data,
            removed,
            topics,
        )

    async def insert_nft_transfer(
        self,
        transaction_hash: str,
        log_index: int,
        address: str,
        from_address: str,
        to_address: str,
        token_id: int,
    ):
        """
        Insert nft transfer data into <node>_nft_transfer table.
        """

        table = f"{self.node_name}_nft_transfer"

        await self.db.execute(
            f"""
            INSERT INTO {table} (transaction_hash, log_index, address, from_address, to_address, token_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (transaction_hash, log_index) DO NOTHING;
            """,
            transaction_hash,
            log_index,
            address,
            from_address,
            to_address,
            token_id,
        )

    async def insert_contract(
        self, address: str, transaction_hash: str, is_pair_contract: bool
    ):
        """
        Insert contract data into <node>_contract table.
        """
        table = f"{self.node_name}_contract"

        await self.db.execute(
            f"""
            INSERT INTO {table} (address, transaction_hash, is_pair_contract)
            VALUES ($1, $2, $3)
            ON CONFLICT (address) DO NOTHING;
        """,
            address,
            transaction_hash,
            is_pair_contract,
        )

    async def insert_token_contract(
        self,
        address: str,
        symbol: str,
        name: str,
        decimals: int,
        total_supply: int,
        token_category: str,
    ):
        """
        Insert token contract data into <node>_token_contract table.
        """
        table = f"{self.node_name}_token_contract"

        await self.db.execute(
            f"""
            INSERT INTO {table} (address, symbol, name, decimals, total_supply, token_category)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (address) DO NOTHING;
        """,
            address,
            symbol,
            name,
            decimals,
            total_supply,
            token_category,
        )

    async def insert_contract_supply_change(
        self, address: str, amount_changed: int, transaction_hash: str
    ):
        """
        Insert token contract supply change data into <node>_token_contract_supply_change table.
        """
        table = f"{self.node_name}_contract_supply_change"

        await self.db.execute(
            f"""
            INSERT INTO {table} (address, amount_changed, transaction_hash)
            VALUES ($1, $2, $3)
            ON CONFLICT (address, transaction_hash) DO NOTHING;
        """,
            address,
            amount_changed,
            transaction_hash,
        )

    async def insert_pair_contract(
        self,
        address: str,
        token0_address: str,
        token1_address: str,
        reserve0: int,
        reserve1: int,
        factory: str,
    ):
        """
        Insert pair contract data into <node>_pair_contract table.
        """
        table = f"{self.node_name}_pair_contract"

        await self.db.execute(
            f"""
            INSERT INTO {table} (address, token0_address, token1_address, reserve0, reserve1, factory)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (address) DO NOTHING;
        """,
            address,
            token0_address,
            token1_address,
            reserve0,
            reserve1,
            factory,
        )

    async def insert_pair_liquidity_change(
        self, address: str, amount0: int, amount1: int, transaction_hash: str
    ):
        """
        Insert pair liquidity change data into <node>_token_contract_supply_change table.
        """
        table = f"{self.node_name}_pair_liquidity_change"

        await self.db.execute(
            f"""
            INSERT INTO {table} (address, amount0, amount1, transaction_hash)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (address, transaction_hash) DO NOTHING;
        """,
            address,
            amount0,
            amount1,
            transaction_hash,
        )

    async def get_block(
        self, block_identifier: Optional[Union[str, int]] = None
    ) -> Optional[dict[str, Any]]:
        """
        Get the block data with a given identifier from the block table.

        Note:
            If block_identifier is `None`, returns the latest block data in the table.

        Returns:
            Optional[dict[str, Any]]: if available returns block data as a dict,
                                      otherwise returns `None`
        """
        table = f"{self.node_name}_block"

        if block_identifier is None:
            # Get latest / last block
            query = f"SELECT * FROM {table} ORDER BY block_number DESC LIMIT 1;"
            args = []
        elif isinstance(block_identifier, str):
            # Get block by hash
            query = f"SELECT * FROM {table} WHERE block_hash = $1;"
            args = (block_identifier,)
        elif isinstance(block_identifier, int):
            # Get block by number
            query = f"SELECT * FROM {table} WHERE block_number = $1"
            args = (block_identifier,)
        else:
            raise UnknownBlockIdentifier()

        # Fetch the first row from the table
        res = await self.db.fetchrow(query, *args)

        # Return a dictionary
        return dict(res) if res else None
