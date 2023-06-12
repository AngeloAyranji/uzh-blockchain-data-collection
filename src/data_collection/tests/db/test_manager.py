import pytest
from asyncpg.exceptions import ForeignKeyViolationError


class TestInsert:
    """Tests for `INSERT INTO <table> VALUES ...`"""

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_block(self, db_manager, block_data):
        """Test insert of block data"""
        await db_manager.insert_block(**block_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_double_insert_block(self, db_manager, block_data):
        """Test double insert of the same block data"""
        await db_manager.insert_block(**block_data)
        await db_manager.insert_block(**block_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_transaction(self, db_manager, block_data, transaction_data):
        """Test insert of transaction data"""
        # Need to insert a block first to satisfy the FK constraint
        await db_manager.insert_block(**block_data)
        await db_manager.insert_transaction(**transaction_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_transaction_doesnt_raise_fk_error(
        self, db_manager, transaction_data
    ):
        """Test insert of transaction data without matching block number doesn't raise FK error"""
        await db_manager.insert_transaction(**transaction_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_internal_transaction(
        self, db_manager, block_data, transaction_data, internal_transaction_data
    ):
        """Test insert of internal transaction"""
        await db_manager.insert_block(**block_data)
        await db_manager.insert_transaction(**transaction_data)
        await db_manager.insert_internal_transaction(**internal_transaction_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_contract(self, db_manager, contract_data):
        """Test insert of contract data"""
        await db_manager.insert_contract(**contract_data)

    @pytest.mark.usefixtures("clean_db")
    @pytest.mark.parametrize("token_category", ["erc20", "erc721", "erc1155"])
    async def test_insert_token_contract(
        self, db_manager, contract_data, token_contract_data, token_category
    ):
        """Test insert of token contract data"""
        # Need to insert contract data first
        await db_manager.insert_contract(**contract_data)
        # Then insert *token* contract data
        token_contract_data["token_category"] = token_category
        await db_manager.insert_token_contract(**token_contract_data)

    @pytest.mark.usefixtures("clean_db")
    @pytest.mark.parametrize("amount", [20, -30, 0])
    async def test_insert_contract_supply_change_data(
        self,
        db_manager,
        contract_data,
        token_contract_data,
        contract_supply_change_data,
        amount,
    ):
        """Test insert of contract supply change data"""
        await db_manager.insert_contract(**contract_data)
        await db_manager.insert_token_contract(**token_contract_data)
        contract_supply_change_data["amount_changed"] = amount
        await db_manager.insert_contract_supply_change(**contract_supply_change_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_pair_contract(
        self, db_manager, pair_contract_data, contract_data
    ):
        """Test insert of pair contract data"""
        await db_manager.insert_contract(**contract_data)
        await db_manager.insert_pair_contract(**pair_contract_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_pair_liquidity_change(
        self, db_manager, pair_liquidity_change_data, contract_data, pair_contract_data
    ):
        """Test insert of pair liquity change data"""
        await db_manager.insert_contract(**contract_data)
        await db_manager.insert_pair_contract(**pair_contract_data)
        await db_manager.insert_pair_liquidity_change(**pair_liquidity_change_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_insert_nft_transfer(
        self,
        db_manager,
        nft_transfer_data,
    ):
        await db_manager.insert_nft_transfer(**nft_transfer_data)

    @pytest.mark.usefixtures("clean_db")
    async def test_updated_at_column_set_on_insert(
        self,
        db_manager,
        block_data,
        transaction_data,
        transaction_logs_data,
        internal_transaction_data,
    ):
        """Test that the updated_at column is set on insert in 4 tables"""
        await db_manager.insert_block(**block_data)
        await db_manager.insert_transaction(**transaction_data)
        await db_manager.insert_transaction_logs(**transaction_logs_data)
        await db_manager.insert_internal_transaction(**internal_transaction_data)

        for table_name in [
            "_block",
            "_transaction",
            "_transaction_logs",
            "_internal_transaction",
        ]:
            table_name = f"{db_manager.node_name}{table_name}"
            res = await db_manager.db.fetchrow(
                f"SELECT updated_at FROM {table_name} LIMIT 1"
            )
            assert res.get("updated_at") is not None

    @pytest.mark.usefixtures("clean_db")
    async def test_updated_at_updated_on_update(self, db_manager, block_data):
        """Test that the updated_at column is updated on update in 4 tables"""
        table_name = f"{db_manager.node_name}_block"

        async def fetch_updated_at():
            return await db_manager.db.fetchrow(
                f"SELECT updated_at FROM {table_name} LIMIT 1"
            )

        await db_manager.insert_block(**block_data)
        initial_updated_at = await fetch_updated_at()
        await db_manager.db.execute(f"UPDATE {table_name} SET block_number = 2")

        assert initial_updated_at < await fetch_updated_at()
