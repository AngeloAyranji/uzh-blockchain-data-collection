from enum import Enum, StrEnum, auto
from typing import List

from hexbytes import HexBytes
from pydantic import BaseModel, root_validator


class DataCollectionWorkerType(Enum):
    """The type of the worker: producing or consuming data"""

    PRODUCER = "producer"
    CONSUMER = "consumer"


class DataCollectionMode(StrEnum):
    """The data collection mode."""

    FULL = auto()
    """FULL data collection mode, ignores "contracts" field in the config file

    Note:
        producer will go through every block and produce every transaction in this block to a Kafka topic
        consumer will insert every received transaction to the database
    """
    PARTIAL = auto()
    """PARTIAL data collection mode, respects "contracts" field in the config file

    Note:
        producer will go through every block and produce every transaction in this block to a Kafka topic
        consumer will insert only transactions that are related to the contracts in the config file
    """
    LOG_FILTER = auto()
    """LOG_FILTER data collection mode

    Note:
        producer will respect log_filter topics while producing transaction hashes to a Kafka topic
        consumers will insert every received transaction to the database
    """
    GET_LOGS = auto()
    """GET_LOGS data collection mode

    Note:
        producer will respect get_logs topics while producing transaction hashes to a Kafka topic
        consumers will insert every received transaction and all the logs to the database
    """


class Web3BaseModel(BaseModel):
    """Base class for any BaseModel related to web3 data"""

    @root_validator(allow_reuse=True, pre=True)
    def transform_hexbytes(cls, values):
        """Transforms every HexBytes instance into a string value.

        Note:
            Any HexBytes value should be implicitly typed as 'str' in the pydantic model
            inheriting from this class.
        """
        for key, value in values.items():
            if isinstance(value, HexBytes):
                values[key] = value.hex()
            elif isinstance(value, List):
                # If the value is a list, recursively transform
                # potential hexbytes values
                values[key] = list(
                    map(lambda v: v.hex() if isinstance(v, HexBytes) else v, value)
                )
        return values
