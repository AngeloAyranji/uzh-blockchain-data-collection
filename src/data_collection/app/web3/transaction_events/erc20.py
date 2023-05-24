from web3.contract import Contract

# Discarding errors on filtered events is expected
# https://github.com/oceanprotocol/ocean.py/issues/348#issuecomment-875128102
from web3.logs import DISCARD
from web3.types import TxReceipt

from app.model.contract import ContractCategory
from app.web3.transaction_events.decorator import _event_mapper
from app.web3.transaction_events.types import (
    BurnFungibleEvent,
    EventsGenerator,
    MintFungibleEvent,
    TransferFungibleEvent,
)


@_event_mapper(ContractCategory.ERC20)
def _transfer(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    # ABI for ERC20 https://gist.github.com/veox/8800debbf56e24718f9f483e1e40c35c

    burn_addresses = {
        "0x0000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000dead",
    }

    # here, contract contains ABI, which has the definition of Transfer().
    # https://web3py.readthedocs.io/en/latest/contracts.html#web3.contract.ContractEvents.myEvent

    # there might be multiple emits in the contract, that's why we're looping, and use yield.
    # contract.events.Transfer() represents the transfer event defined in the ABI. when a receipt is passed, we get the
    # actual transfers contained in that receipt.
    for eventLog in contract.events.Transfer().process_receipt(receipt, errors=DISCARD):
        if eventLog["event"] == "Transfer":
            src = eventLog["args"]["from"]
            dst = eventLog["args"]["to"]
            val = eventLog["args"]["value"]
            address = eventLog["address"]
            log_index = eventLog["logIndex"]
            if dst in burn_addresses and src in burn_addresses:
                pass
            # https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol#L298
            if dst in burn_addresses:
                yield BurnFungibleEvent(
                    address=address, log_index=log_index, account=src, value=val
                )
            # https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol#L269
            elif src in burn_addresses:
                yield MintFungibleEvent(
                    address=address, log_index=log_index, account=dst, value=val
                )

            yield TransferFungibleEvent(
                address=address,
                log_index=log_index,
                src=src,
                dst=dst,
                value=val,
            )


@_event_mapper(ContractCategory.ERC20)
def _issue(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    # USDT -> https://etherscan.io/address/0xdac17f958d2ee523a2206206994597c13d831ec7#code#L444
    # Issue = USDT owner creates tokens.
    for eventLog in contract.events.Issue().process_receipt(receipt, errors=DISCARD):
        val = eventLog["args"]["amount"]
        address = eventLog["address"]
        log_index = eventLog["logIndex"]
        yield MintFungibleEvent(
            address=address,
            log_index=log_index,
            value=val,
        )


@_event_mapper(ContractCategory.ERC20)
def _redeem(contract: Contract, receipt: TxReceipt) -> EventsGenerator:
    # Redeem = USDT owner makes tokens dissapear - no null address. if they transfer to null address, still burn.
    # getOwner -> https://etherscan.io/address/0xdac17f958d2ee523a2206206994597c13d831ec7#code#L275
    for eventLog in contract.events.Redeem().process_receipt(receipt, errors=DISCARD):
        val = eventLog["args"]["amount"]
        address = eventLog["address"]
        log_index = eventLog["logIndex"]
        yield BurnFungibleEvent(
            address=address,
            log_index=log_index,
            value=val,
        )
