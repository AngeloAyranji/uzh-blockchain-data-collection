from typing import Any, List, Optional

from pydantic import (
    AnyUrl,
    BaseModel,
    BaseSettings,
    Field,
    PostgresDsn,
    RedisDsn,
    confrozenset,
    conlist,
    constr,
    root_validator,
    validator,
)

import app.web3.transaction_events.types as w3t
from app.model import DataCollectionMode
from app.model.contract import ContractCategory


class ContractConfig(BaseModel):
    """Describe a smart contract that the consumers should save data for

    For instance USDT, UniswapV2Factory or some UniswapPair
    """

    address: str
    """The address of the smart contract"""
    symbol: str
    """The symbol / name / description of the contract"""
    category: ContractCategory
    """The category of the contract. Mapped to contract.ContractCategory Enum."""
    events: confrozenset(item_type=constr(regex="^[A-Z][A-Za-z]*$"))
    """Constrained set of events that will be processed (stored into DB) for this contract.

    The values within this list should be equal to `EventContract` subclasses' names.

    Examples:
        ``["TransferFungibleEvent", "SwapPairEvent", "MintFungibleEvent", "BurnFungibleEvent"]``
        ``["TransferFungibleEvent"]``
    """

    @validator("events")
    def check_if_events_are_matching_event_names_in_web3_types(cls, values):
        """Check if each of the items in 'events' field is one of the ContractEvent.__name__ defined in types.py"""
        # Get names of event subclasses
        event_cls_names = set(
            [
                cls_name
                for cls_name, event_cls in w3t.__dict__.items()
                if isinstance(event_cls, type)
                and issubclass(event_cls, w3t.ContractEvent)
                and cls_name != "ContractEvent"
            ]
        )
        # Check if each event name is correct
        for v in values:
            if v not in event_cls_names:
                raise ValueError(f"{v} is not an acceptable event name.")

        return values

    def __eq__(self, __value: object) -> bool:
        return (
            self.address == __value.address
            and self.symbol == __value.symbol
            and self.category == __value.category
            and self.events == __value.events
        )

    def __hash__(self) -> int:
        return hash(
            self.address + self.symbol + self.category.value + "".join(self.events)
        )


class DataCollectionConfig(BaseSettings):
    """Store data collection configuration settings.

    Each data collection config will start producing transactions depending on its mode.
    """

    mode: DataCollectionMode
    """Mode of this data collection config. (previously called producer_type)"""
    start_block: Optional[int]
    """Starting block number. Takes precedence over the setting in the db."""
    end_block: Optional[int]
    """Ending block number. Takes precedence over the setting in the db."""

    contracts: List[ContractConfig]
    """Contains a list of smart contract objects of interest.

    Note:
        Any transaction interacting (create, call) with these addresses
        will be saved in the database. Each contract contains information about
        its category.
    """

    topics: Optional[List[Any]]
    """Can be empty, required when used with ProducerType.LOG_FILTER"""

    @root_validator
    def block_order_correct(cls, values):
        """Check if start_block <= end_block"""
        start_block = values.get("start_block")
        end_block = values.get("end_block")
        if start_block is not None and end_block is not None:
            # Verify that the end block is larger than start_block
            if start_block > end_block:
                raise ValueError(
                    f"start_block ({start_block}) must be equal or smaller than end_block ({end_block})"
                )

        return values

    @root_validator
    def mode_not_missing_fields(cls, values):
        """Validate fields not missing for each mode"""
        mode = values.get("mode")
        if mode == DataCollectionMode.LOG_FILTER:
            if values.get("topics") is None:
                raise ValueError(f'"mode": "log_filter" requires "topics" field')
        elif mode == DataCollectionMode.PARTIAL:
            if values.get("contracts") is None:
                raise ValueError(f'"mode": "partial" requires "contracts" field')
        return values


class Config(BaseSettings):
    """App configuration file"""

    node_url: AnyUrl
    """The blockchain node RPC API URL"""

    db_dsn: PostgresDsn
    """DSN for PostgreSQL"""

    sentry_dsn: Optional[str] = None
    """DSN for Sentry"""

    redis_url: RedisDsn
    """URL for Redis (needs to have a 'redis://' scheme)"""

    kafka_url: str
    """URL for Kafka"""
    kafka_topic: str
    """The Kafka topic, also used in Redis and the database to distinguish tables."""

    data_collection: conlist(DataCollectionConfig, min_items=1)
    """(constrained) list of datacollection configurations"""

    number_of_consumer_tasks: int = Field(..., env="N_CONSUMER_INSTANCES")
    """The number of consumer (`DataConsumer`) tasks that will be started"""

    web3_requests_timeout: int = Field(..., env="WEB3_REQUESTS_TIMEOUT")
    """Timeout for web3 requests in seconds"""

    web3_requests_retry_limit: int = Field(..., env="WEB3_REQUESTS_RETRY_LIMIT")
    """The number of retries for web3 requests"""

    web3_requests_retry_delay: int = Field(..., env="WEB3_REQUESTS_RETRY_DELAY")
    """The delay between retries for web3 requests in seconds"""

    kafka_event_retrieval_timeout: int = Field(..., env="KAFKA_EVENT_RETRIEVAL_TIMEOUT")
    """Timeout for retrieving events from Kafka in seconds. After this time runs out, the consumers will shut down."""
