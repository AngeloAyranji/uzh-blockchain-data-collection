from datetime import datetime
from typing import List

from pydantic import Field, validator

from app.model import Web3BaseModel


class BlockData(Web3BaseModel):
    """Describes a block given by `get_block`"""

    block_number: int = Field(..., alias="number")
    block_hash: str = Field(..., alias="hash")
    nonce: str
    difficulty: int
    gas_limit: int = Field(..., alias="gasLimit")
    gas_used: int = Field(..., alias="gasUsed")
    timestamp: datetime
    transactions: List[str]
    miner: str
    parent_hash: str = Field(..., alias="parentHash")

    @validator("timestamp", pre=True)
    def timestamp_to_datetime(cls, v):
        """Integer timestamp to datetime.datetime validator"""
        return datetime.fromtimestamp(v)
