from web3.contract import Contract

# Discarding errors on filtered events is expected
# https://github.com/oceanprotocol/ocean.py/issues/348#issuecomment-875128102
from web3.logs import DISCARD
from web3.types import TxReceipt

from app import init_logger
from app.model.contract import ContractCategory
from app.web3.transaction_events.decorator import _event_mapper
from app.web3.transaction_events.types import (
    BurnPairEvent,
    EventsGenerator,
    MintPairEvent,
    SwapPairEvent,
)


@_event_mapper(ContractCategory.UNI_SWAP_V2_PAIR)
def _mint(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    for eventLog in contract.events.Mint().process_receipt(receipt, errors=DISCARD):
        sender = eventLog["args"]["sender"]
        amount0 = eventLog["args"]["amount0"]
        amount1 = eventLog["args"]["amount1"]
        address = eventLog["address"]
        log_index = eventLog["logIndex"]
        yield MintPairEvent(
            address=address,
            log_index=log_index,
            sender=sender,
            amount0=amount0,
            amount1=amount1,
        )


@_event_mapper(ContractCategory.UNI_SWAP_V2_PAIR)
def _burn(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    # https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L134
    # Burn of pairs in Uniswap -> taking back liquidity from the pool "to" their address or another one.
    for eventLog in contract.events.Burn().process_receipt(receipt, errors=DISCARD):
        sender = eventLog["args"]["sender"]
        amount0 = eventLog["args"]["amount0"]
        amount1 = eventLog["args"]["amount1"]
        to = eventLog["args"]["to"]
        address = eventLog["address"]
        log_index = eventLog["logIndex"]
        yield BurnPairEvent(
            address=address,
            log_index=log_index,
            src=sender,
            dst=to,
            amount0=amount0,
            amount1=amount1,
        )


@_event_mapper(ContractCategory.UNI_SWAP_V2_PAIR)
def _swap(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    # https://github.com/Uniswap/v2-core/blob/master/contracts/UniswapV2Pair.sol#L51
    for eventLog in contract.events.Swap().process_receipt(receipt, errors=DISCARD):
        sender = eventLog["args"]["sender"]
        amount_0_in = eventLog["args"]["amount0In"]
        amount_1_in = eventLog["args"]["amount1In"]
        amount_0_out = eventLog["args"]["amount0Out"]
        amount_1_out = eventLog["args"]["amount1Out"]
        to = eventLog["args"]["to"]
        address = eventLog["address"]
        log_index = eventLog["logIndex"]
        yield SwapPairEvent(
            address=address,
            log_index=log_index,
            src=sender,
            dst=to,
            in0=amount_0_in,
            in1=amount_1_in,
            out0=amount_0_out,
            out1=amount_1_out,
        )
