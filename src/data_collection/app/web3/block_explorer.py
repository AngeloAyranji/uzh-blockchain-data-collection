from collections import namedtuple

from app.config import DataCollectionConfig
from app.db.manager import DatabaseManager
from app.web3.node_connector import NodeConnector

ExplorationBounds = namedtuple("ExplorationBounds", ["start_block", "end_block"])


class BlockExplorer:
    """Decide the start and end block numbers of the data collection process"""

    # Start from the genesis block by default
    DEFAULT_START_BLOCK = 0
    # End with the latest block by default
    DEFAULT_END_BLOCK = None

    def __init__(
        self,
        data_collection_cfg: DataCollectionConfig,
        db: DatabaseManager,
        w3: NodeConnector,
    ) -> None:
        self.cfg_start_block = data_collection_cfg.start_block
        self.cfg_end_block = data_collection_cfg.end_block
        self.db = db
        self.w3 = w3

    async def get_exploration_bounds(self) -> ExplorationBounds:
        """
        Determine the starting and ending block numbers based on configuration and database values

        Note:
            Configuration values take precedence over the database values.
        """
        # Default configuration
        start_block, end_block = self.DEFAULT_START_BLOCK, self.DEFAULT_END_BLOCK

        # Get latest inserted block from db
        last_block = None
        if res := await self.db.get_block():
            last_block = res["block_number"]

        # Get starting block from external sources if available
        if self.cfg_start_block is not None:
            # Give priority to config
            start_block = self.cfg_start_block
        elif last_block is not None:
            # If last block number contains a value, use this as the starting block number
            start_block = last_block
            start_block_data = await self.w3.get_block_data(start_block)
            start_block_txs = start_block_data.transactions

            # Verify that all the transactions in this block are
            # present in the transactions table
            last_block_txs = self.db.get_block_transactions(last_block)

            if start_block_txs == last_block_txs:
                # If all transactions from start_block are already present in the
                # `*_transactions` table then continue from the next block
                start_block += 1
            else:
                # Otherwise start from the last inserted block, in other words
                # insert the transactions again because some are missing
                pass

        # Get ending block if available in config
        if self.cfg_end_block is not None:
            end_block = self.cfg_end_block

        return ExplorationBounds(start_block=start_block, end_block=end_block)
