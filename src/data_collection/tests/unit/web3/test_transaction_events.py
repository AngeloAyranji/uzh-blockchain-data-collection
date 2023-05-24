import unittest
from unittest.mock import MagicMock

from hexbytes import HexBytes
from web3.contract import Contract
from web3.contract.contract import (
    ContractEvent,
    ContractEvents,
    ContractFunction,
    ContractFunctions,
)
from web3.types import EventData, TxReceipt

from app.model.contract import ContractCategory
from app.web3 import transaction_events as te
from app.web3.transaction_events.types import (
    BurnFungibleEvent,
    BurnNonFungibleEvent,
    BurnPairEvent,
    MintFungibleEvent,
    MintNonFungibleEvent,
    MintPairEvent,
    PairCreatedEvent,
    SwapPairEvent,
    TransferFungibleEvent,
    TransferNonFungibleEvent,
)


class CommonTest(unittest.TestCase):
    def test_unknown_category_no_events(self):
        contract = MagicMock(spec=Contract)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.UNKNOWN, contract, receipt)
        events = list(events)

        contract.events.assert_not_called()
        self.assertEqual(len(events), 0)


class ERC20Tests(unittest.TestCase):
    def test_erc20_mint_transfer0x000(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x0000000000000000000000000000000000000000",
                        "to": "0x000000000000000000000000000000000000BABA",
                        "value": 42,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                MintFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    value=42,
                ),
                TransferFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x0000000000000000000000000000000000000000",
                    dst="0x000000000000000000000000000000000000BABA",
                    value=42,
                ),
            ],
            events,
        )

    def test_erc20_mint_transfer0xdead(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000dead",
                        "to": "0x000000000000000000000000000000000000BABA",
                        "value": 42,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                MintFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    value=42,
                ),
                TransferFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000dead",
                    dst="0x000000000000000000000000000000000000BABA",
                    value=42,
                ),
            ],
            events,
        )

    def test_erc20_usdt_mint_issue(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(return_value=[])
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Issue",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={"amount": 42},
                    logIndex=1337,
                )
            ]
        )
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                MintFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    value=42,
                )
            ],
            events,
        )

    def test_erc20_burn_transfer0x000(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000BABA",
                        "to": "0x0000000000000000000000000000000000000000",
                        "value": 42,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                BurnFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    value=42,
                ),
                TransferFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000BABA",
                    dst="0x0000000000000000000000000000000000000000",
                    value=42,
                ),
            ],
            events,
        )

    def test_erc20_burn_transfer0xdead(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000BABA",
                        "to": "0x000000000000000000000000000000000000dead",
                        "value": 42,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                BurnFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    value=42,
                ),
                TransferFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000BABA",
                    dst="0x000000000000000000000000000000000000dead",
                    value=42,
                ),
            ],
            events,
        )

    def test_erc20_burn_redeem(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(return_value=[])
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Redeem",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={"amount": 42},
                    logIndex=1337,
                )
            ]
        )
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                BurnFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    value=42,
                ),
            ],
            events,
        )

    def test_erc20_transfer(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000ABAB",
                        "to": "0x000000000000000000000000000000000000BABA",
                        "value": 42,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC20, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                TransferFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000ABAB",
                    dst="0x000000000000000000000000000000000000BABA",
                    value=42,
                ),
            ],
            events,
        )


class ERC721Tests(unittest.TestCase):
    def test_erc721_mint_transfer0x000(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x0000000000000000000000000000000000000000",
                        "to": "0x000000000000000000000000000000000000BABA",
                        "tokenId": 4,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC721, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                MintNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    tokenId=4,
                ),
                TransferNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x0000000000000000000000000000000000000000",
                    dst="0x000000000000000000000000000000000000BABA",
                    tokenId=4,
                ),
            ],
            events,
        )

    def test_erc721_mint_transfer0xdead(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000dead",
                        "to": "0x000000000000000000000000000000000000BABA",
                        "tokenId": 4,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC721, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                MintNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    tokenId=4,
                ),
                TransferNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000dead",
                    dst="0x000000000000000000000000000000000000BABA",
                    tokenId=4,
                ),
            ],
            events,
        )

    def test_erc721_burn_transfer0x00(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000BABA",
                        "to": "0x0000000000000000000000000000000000000000",
                        "tokenId": 4,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC721, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                BurnNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    tokenId=4,
                ),
                TransferNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000BABA",
                    dst="0x0000000000000000000000000000000000000000",
                    tokenId=4,
                ),
            ],
            events,
        )

    def test_erc721_burn_transfer0xdead(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000BABA",
                        "to": "0x000000000000000000000000000000000000dead",
                        "tokenId": 4,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC721, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                BurnNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    tokenId=4,
                ),
                TransferNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000BABA",
                    dst="0x000000000000000000000000000000000000dead",
                    tokenId=4,
                ),
            ],
            events,
        )

    def test_erc721_transfer(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        transfer_event = MagicMock(spec=ContractEvent)
        transfer_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Transfer",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "from": "0x000000000000000000000000000000000000BABA",
                        "to": "0x000000000000000000000000000000000000ABAB",
                        "tokenId": "5",
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Transfer = MagicMock(return_value=transfer_event)
        issue_event = MagicMock(spec=ContractEvent)
        issue_event.process_receipt = MagicMock(return_value=[])
        contract.events.Issue = MagicMock(return_value=issue_event)
        redeem_event = MagicMock(spec=ContractEvent)
        redeem_event.process_receipt = MagicMock(return_value=[])
        contract.events.Redeem = MagicMock(return_value=redeem_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(ContractCategory.ERC721, contract, receipt)
        events = list(events)

        self.assertEqual(
            [
                TransferNonFungibleEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x000000000000000000000000000000000000BABA",
                    dst="0x000000000000000000000000000000000000ABAB",
                    tokenId="5",
                )
            ],
            events,
        )


class UniSwapV2Tests(unittest.TestCase):
    def test_uniSwapV2_newPair(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        pairCreated_event = MagicMock(spec=ContractEvent)
        pairCreated_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="PairCreated",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "token0": "0x0000000000000000000000000000000000000001",
                        "token1": "0x0000000000000000000000000000000000000002",
                        "pair": "0x0000000000000000000000000000000000000003",
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.PairCreated = MagicMock(return_value=pairCreated_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(
            ContractCategory.UNI_SWAP_V2_FACTORY, contract, receipt
        )
        events = list(events)

        self.assertEqual(
            [
                PairCreatedEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    pair_address="0x0000000000000000000000000000000000000003",
                    token0="0x0000000000000000000000000000000000000001",
                    token1="0x0000000000000000000000000000000000000002",
                    log_index=1337,
                )
            ],
            events,
        )

    def test_uniSwapV2Pair_mint(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        Mint_event = MagicMock(spec=ContractEvent)
        Mint_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Mint",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "sender": "0x0000000000000000000000000000000000000001",
                        "amount0": 2,
                        "amount1": 3,
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Mint = MagicMock(return_value=Mint_event)
        Burn_event = MagicMock(spec=ContractEvent)
        Burn_event.process_receipt = MagicMock(return_value=[])
        contract.events.Burn = MagicMock(return_value=Burn_event)
        Swap_event = MagicMock(spec=ContractEvent)
        Swap_event.process_receipt = MagicMock(return_value=[])
        contract.events.Swap = MagicMock(return_value=Swap_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(
            ContractCategory.UNI_SWAP_V2_PAIR, contract, receipt
        )
        events = list(events)

        self.assertEqual(
            [
                MintPairEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    sender="0x0000000000000000000000000000000000000001",
                    amount0=2,
                    amount1=3,
                )
            ],
            events,
        )

    def test_uniSwapV2Pair_burn(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        Burn_event = MagicMock(spec=ContractEvent)
        Burn_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Burn",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "sender": "0x0000000000000000000000000000000000000001",
                        "amount0": 2,
                        "amount1": 3,
                        "to": "0x0000000000000000000000000000000000000002",
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Burn = MagicMock(return_value=Burn_event)
        Mint_event = MagicMock(spec=ContractEvent)
        Mint_event.process_receipt = MagicMock(return_value=[])
        contract.events.Mint = MagicMock(return_value=Mint_event)
        Swap_event = MagicMock(spec=ContractEvent)
        Swap_event.process_receipt = MagicMock(return_value=[])
        contract.events.Swap = MagicMock(return_value=Swap_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(
            ContractCategory.UNI_SWAP_V2_PAIR, contract, receipt
        )
        events = list(events)

        self.assertEqual(
            [
                BurnPairEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x0000000000000000000000000000000000000001",
                    dst="0x0000000000000000000000000000000000000002",
                    amount0=2,
                    amount1=3,
                ),
            ],
            events,
        )

    def test_uniSwapV2Pair_swap(self):
        contract = MagicMock(spec=Contract)
        contract.events = MagicMock(spec=ContractEvents)
        Burn_event = MagicMock(spec=ContractEvent)
        Burn_event.process_receipt = MagicMock(spec=ContractEvent)
        contract.events.Burn = MagicMock(return_value=Burn_event)
        Mint_event = MagicMock(spec=ContractEvent)
        Mint_event.process_receipt = MagicMock(return_value=[])
        contract.events.Mint = MagicMock(return_value=Mint_event)
        Swap_event = MagicMock(spec=ContractEvent)
        Swap_event.process_receipt = MagicMock(
            return_value=[
                EventData(
                    event="Swap",
                    address="0x000000000000000000000000000000000000AAAA",
                    args={
                        "sender": "0x0000000000000000000000000000000000000001",
                        "amount0In": 2,
                        "amount1In": 3,
                        "amount0Out": 4,
                        "amount1Out": 5,
                        "to": "0x0000000000000000000000000000000000000002",
                    },
                    logIndex=1337,
                )
            ]
        )
        contract.events.Swap = MagicMock(return_value=Swap_event)
        receipt = MagicMock(spec=TxReceipt)

        events = te.get_transaction_events(
            ContractCategory.UNI_SWAP_V2_PAIR, contract, receipt
        )
        events = list(events)

        self.assertEqual(
            [
                SwapPairEvent(
                    address="0x000000000000000000000000000000000000AAAA",
                    log_index=1337,
                    src="0x0000000000000000000000000000000000000001",
                    dst="0x0000000000000000000000000000000000000002",
                    in0=2,
                    in1=3,
                    out0=4,
                    out1=5,
                ),
            ],
            events,
        )


if __name__ == "__main__":
    unittest.main()
