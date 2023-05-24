import asyncio
import time

from web3.exceptions import BlockNotFound

from app import init_logger
from app.config import Config, DataCollectionConfig
from app.kafka.manager import KafkaProducerManager
from app.model import DataCollectionMode
from app.model.block import BlockData
from app.utils import log_producer_progress
from app.utils.data_collector import DataCollector
from app.web3.block_explorer import BlockExplorer

log = init_logger(__name__)


class DataProducer(DataCollector):
    """
    Produce block / transaction data from the blockchain (node) to a Kafka topic.

    This class also updates the database with block data and saves the state
    of processing (latest_processed_block).
    """

    MAX_ALLOWED_TRANSACTIONS = 200000
    """The maximum amount of allowed transactions in a single kafka topic"""
    PROGRESS_LOG_FREQUENCY = 1000
    """Log a progress status every 1000 blocks"""

    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.config = config
        self.kafka_manager: KafkaProducerManager = KafkaProducerManager(
            kafka_url=config.kafka_url,
            redis_url=config.redis_url,
            topic=config.kafka_topic,
        )

    async def _init_block_vars(self, data_collection_cfg: DataCollectionConfig):
        """Initialize start and end block numbers and variable block indices from the config and the database"""
        # Get block exploration bounds (start and end block number)
        block_explorer = BlockExplorer(
            data_collection_cfg=data_collection_cfg,
            db=self.db_manager,
            w3=self.node_connector,
        )
        start_block, end_block = await block_explorer.get_exploration_bounds()

        # Current block index, last processed block index
        i_block, i_processed_block = start_block, None

        if end_block is not None:
            # If end block contains a number, continue until we reach it
            should_continue = lambda i: i <= end_block
        else:
            # Else continue forever until a 'BlockNotFound' exception is raised
            should_continue = lambda _: True

        end_block_str = f"block #{end_block}" if end_block else "'latest' block"
        log.info(
            f"Starting from block #{start_block}, expecting to finish at {end_block_str}"
        )

        return start_block, end_block, i_block, i_processed_block, should_continue

    async def _start_logfilter_producer(
        self, data_collection_cfg: DataCollectionConfig
    ):
        """Start a log filter producer that sends only filtered transactions to kafka"""
        # TODO: Finish this method
        # as of now (March 2023) `eth_getFilterLogs` RPC method of the erigon node is unavailable
        # (https://github.com/ledgerwatch/erigon/issues/5092#issuecomment-1218133784)

        # Get list of addresses
        # addresses = list(map(lambda c: c.address, data_collection_cfg.contracts))
        # w3_filter = await self.node_connector.w3.eth.filter(
        #     {
        #         "address": addresses,
        #         "topics": data_collection_cfg.topics,
        #         "fromBlock": data_collection_cfg.start_block,
        #         "toBlock": data_collection_cfg.end_block
        #     }
        # )
        # result = await w3_filter.get_all_entries()
        # Continue in a similar fashion as in the full" producer method below
        # 1. Insert block if needed
        # 2. Send batch of txs to kafka
        # 3. Iterate until the end
        raise NotImplementedError("Log filter producer is not implemented yet")

    async def _start_producer(
        self, data_collection_cfg: DataCollectionConfig, get_block_reward: bool = False
    ):
        """Start a regular producer that goes through every block and sends all txs to kafka

        Args:
            data_collection_cfg (DataCollectionConfig): the data collection config object
            get_block_reward (bool): whether to get the block reward or not
        """
        # Initialize block variables
        (
            start_block,
            end_block,
            i_block,
            i_processed_block,
            should_continue,
        ) = await self._init_block_vars(data_collection_cfg=data_collection_cfg)
        # Start producing transactions
        try:
            # Track the total amount of transactions produced
            _total_transactions = 0
            # Timer to track the average time per block
            _initial_time_counter_stamp = time.perf_counter()
            while should_continue(i_block):
                # query the node for current block data
                block_data: BlockData = await self.node_connector.get_block_data(
                    i_block
                )

                # Insert new block
                block_reward = 0
                if get_block_reward:
                    # FIXME: call trace_block to get static block reward
                    pass

                await self._insert_block(
                    block_data=block_data, block_reward=block_reward
                )

                if block_data.transactions:
                    messages = [
                        self.encode_kafka_event(tx_hash, data_collection_cfg.mode)
                        for tx_hash in block_data.transactions
                    ]
                    _total_transactions += len(messages)
                    # Send all the transaction hashes to Kafka so consumers can process them
                    await self.kafka_manager.send_batch(msgs=messages)
                else:
                    log.debug(
                        f"Skipped sending block #{block_data.block_number} to kafka as it contains no transactions."
                    )

                # Update the processed block variable with current block index
                i_processed_block = i_block

                # Continue from the next block
                i_block += 1

                # Log a status message if needed
                log_producer_progress(
                    log=log,
                    i_block=i_processed_block,
                    start_block=start_block,
                    end_block=end_block,
                    progress_log_frequency=self.PROGRESS_LOG_FREQUENCY,
                    initial_time_counter=_initial_time_counter_stamp,
                    n_transactions=await self.kafka_manager.redis_manager.get_n_transactions(),
                )
        except BlockNotFound:
            # OK, BlockNotFound exception is raised when the latest block is reached
            log.info(
                "BlockNotFound exception raised, finished collecting data because latest block has been reached"
            )
        finally:
            if i_processed_block is None:
                log.info("Finished before collecting any block data!")
            else:
                log.info(
                    f"Finished at block #{i_processed_block} | total produced transactions: {_total_transactions}"
                )

    async def _start_producer_task(
        self, data_collection_cfg: DataCollectionConfig
    ) -> asyncio.Task:
        """
        Start a producer task depending on the data collection config producer type.
        """
        pretty_config = data_collection_cfg.dict(exclude={"contracts"})
        pretty_config["contracts"] = list(
            map(lambda c: c.symbol, data_collection_cfg.contracts)
        )
        log.info(f"Creating data collection producer task ({pretty_config})")
        # Log information about the producer
        n_partitions = await self.kafka_manager.number_of_partitions
        log.info(
            f"Found {n_partitions} partition(s) on topic '{self.kafka_manager.topic}'"
        )

        match data_collection_cfg.mode:
            case DataCollectionMode.FULL:
                return asyncio.create_task(
                    self._start_producer(data_collection_cfg, get_block_reward=True)
                )
            case DataCollectionMode.PARTIAL:
                return asyncio.create_task(
                    self._start_producer(data_collection_cfg, get_block_reward=False)
                )
            case DataCollectionMode.LOG_FILTER:
                return asyncio.create_task(
                    self._start_logfilter_producer(data_collection_cfg)
                )

    async def start_producing_data(self) -> int:
        """
        Start a subproducer for each data collection config object and wait until they all finish.

        Returns:
            exit_code: 0 if no exceptions encountered during data collection, 1 otherwise
        """
        producer_tasks = []
        data_collection_configs = self.config.data_collection

        log.info(f"Using config: {self.config.dict(exclude={'data_collection'})}")

        # Create asyncio tasks for each data collection config
        for data_collection_cfg in data_collection_configs:
            producer_tasks.append(await self._start_producer_task(data_collection_cfg))

        # Wait until all tasks finish
        result = await asyncio.gather(*producer_tasks, return_exceptions=True)
        exit_code = 0

        # Log exceptions if they occurred
        for return_value, cfg in zip(result, data_collection_configs):
            if isinstance(return_value, Exception):
                log.error(
                    f'Data collection for mode="{cfg.mode}" with {len(cfg.contracts)} contracts resulted in an exception:',
                    exc_info=(
                        type(return_value),
                        return_value,
                        return_value.__traceback__,
                    ),
                )
                exit_code = 1

        log.info("Finished producing data from all data collection tasks.")
        return exit_code

    async def _insert_block(self, block_data: BlockData, block_reward: int):
        """Insert new block data into the block table"""
        block_data_dict = block_data.dict()
        # Remove unnecessary values
        del block_data_dict["transactions"]
        await self.db_manager.insert_block(
            **block_data_dict,
            # TODO: need to calculate the block reward
            # https://ethereum.stackexchange.com/questions/5958/how-to-query-the-amount-of-mining-reward-from-a-certain-block
            block_reward=block_reward,
        )
