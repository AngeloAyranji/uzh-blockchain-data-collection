from web3.contract import Contract

# Discarding errors on filtered events is expected
# https://github.com/oceanprotocol/ocean.py/issues/348#issuecomment-875128102
from web3.logs import DISCARD
from web3.types import TxReceipt

from app.model.contract import ContractCategory
from app.web3.transaction_events.decorator import _event_mapper
from app.web3.transaction_events.types import EventsGenerator, PairCreatedEvent


@_event_mapper(ContractCategory.UNI_SWAP_V2_FACTORY)
def _pair_created(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    # PairCreation -> https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Factory.sol#L13
    for eventLog in contract.events.PairCreated().process_receipt(
        receipt, errors=DISCARD
    ):
        if eventLog["event"] == "PairCreated":
            token0 = eventLog["args"]["token0"]
            token1 = eventLog["args"]["token1"]
            pair = eventLog["args"]["pair"]
            address = eventLog["address"]
            log_index = eventLog["logIndex"]
            yield PairCreatedEvent(
                address=address,
                log_index=log_index,
                pair_address=pair,
                token0=token0,
                token1=token1,
            )
