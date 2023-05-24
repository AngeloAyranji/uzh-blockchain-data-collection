from typing import List, Optional

from pydantic import Field, validator

from app.model import Web3BaseModel


class TransactionData(Web3BaseModel):
    """Describes a transaction given by `get_transaction`"""

    transaction_hash: Optional[str] = Field(None, alias="hash")
    block_number: Optional[int] = Field(None, alias="blockNumber")
    from_address: Optional[str] = Field(None, alias="from")
    to_address: Optional[str] = Field(None, alias="to")
    value: Optional[float] = None
    gas_price: Optional[float] = Field(None, alias="gasPrice")
    gas_limit: Optional[float] = Field(None, alias="gas")
    input_data: Optional[str] = Field(None, alias="input")


class TransactionLogsData(Web3BaseModel):
    """Describes transaction receipt logs given by `get_transaction_receipt`"""

    address: Optional[str] = None
    data: Optional[str] = None
    removed: Optional[bool] = None
    topics: Optional[List[str]] = None
    log_index: Optional[int] = Field(None, alias="logIndex")
    transaction_hash: Optional[str] = Field(None, alias="transactionHash")


class TransactionReceiptData(Web3BaseModel):
    """Describes a transaction receipt given by `get_transaction_receipt`"""

    gas_used: Optional[float] = Field(None, alias="gasUsed")
    logs: Optional[List[TransactionLogsData]] = None
    transaction_type: str = Field(None, alias="type")
    contract_address: Optional[str] = Field(None, alias="contractAddress")


class InternalTransactionData(Web3BaseModel):
    """Describes an internal transaction given by `debug_traceTransaction`"""

    from_address: Optional[str] = Field(None, alias="from")
    to_address: Optional[str] = Field(None, alias="to")
    value: Optional[float] = None
    gas_used: Optional[float] = Field(None, alias="gasUsed")
    gas_limit: Optional[float] = Field(None, alias="gas")
    input_data: Optional[str] = Field(None, alias="input")
    call_type: Optional[str] = Field(None, alias="callType")

    @validator("value", "gas_used", "gas_limit", pre=True)
    def strings_to_float(cls, v):
        return float.fromhex(v)
