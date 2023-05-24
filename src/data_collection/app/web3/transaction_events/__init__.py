from typing import Type, Union

from hexbytes import HexBytes
from web3.contract import Contract
from web3.types import TxReceipt

from app.model.contract import ContractCategory

from . import decorator, erc20, erc721, uniswap_pair, uniswapv2_factory
from .types import EventsGenerator


def get_transaction_events(
    contract_category: ContractCategory,
    contract: Union[Type[Contract], Contract],
    receipt: TxReceipt,
) -> EventsGenerator:
    """
    It returns all the contract events found in the given contract with the given receipt.
    """
    # FIXME: types are broken, but we ignore mypy
    # if not isinstance(contract, Contract):
    #    logger.error(f"{contract} is not of type Contract!")
    #    return None
    # assert isinstance(contract, Contract)
    for mapper in decorator.__event_mappers[contract_category]:
        yield from mapper(contract, receipt)
