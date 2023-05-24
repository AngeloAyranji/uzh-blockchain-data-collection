import asyncio
from typing import Any, Callable, Collection, List, Tuple, Type

from aiohttp.client_exceptions import ClientConnectorError
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.types import (
    AsyncMiddlewareCoroutine,
    RPCEndpoint,
    RPCResponse,
    TxData,
    TxReceipt,
)

from app import init_logger
from app.model.block import BlockData
from app.model.transaction import (
    InternalTransactionData,
    TransactionData,
    TransactionReceiptData,
)

log = init_logger(__name__)


def async_exception_retry_middleware(
    make_request: Callable[[RPCEndpoint, Any], RPCResponse],
    w3: AsyncWeb3,
    errors: Collection[Type[BaseException]],
    retries: int,
    delay: int,
) -> AsyncMiddlewareCoroutine:
    async def middleware(method: RPCEndpoint, params: Any) -> RPCResponse:
        for i in range(retries):
            try:
                return await make_request(method, params)
            except errors as e:
                request_details_str = f"(method='{method}',params={params})"
                if i < retries - 1:
                    log.debug(
                        f"Request {request_details_str} failed: {repr(e)}. Retrying after {delay}s ({i+1})"
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    log.error(
                        f"Failed to make request {request_details_str} after {retries} retries. {repr(e)}"
                    )
                    raise
        return None

    return middleware


def async_http_retry_request_middleware(
    retries: int = 10,
    delay: int = 5,
) -> AsyncMiddlewareCoroutine:
    async def inner(make_request: Callable[[RPCEndpoint, Any], Any], w3: AsyncWeb3):
        return async_exception_retry_middleware(
            make_request,
            w3,
            (asyncio.TimeoutError, ClientConnectorError, TimeoutError),
            retries=retries,
            delay=delay,
        )

    return inner


class NodeConnector:
    """Connect to a blockchain node and scrape / mine data

    This class is responsible for all the web3 operations that
    are required by this app.
    """

    def __init__(
        self, node_url: str, timeout: int, retry_limit: int, retry_delay: int
    ) -> None:
        """
        Args:
            node_url: the RPC API URL for connecting
                        to an EVM node
        """
        # Initialize an async web3 instance
        # Workaround with headers allows to connect to the Abacus
        # JSON RPC API through an SSH tunnel. Abacus only allows hostname to
        # be "localhost" otherwise it returns a 403 response code.
        headers = {"Host": "localhost", "Content-Type": "application/json"}

        self.w3 = AsyncWeb3(
            provider=AsyncHTTPProvider(
                endpoint_uri=node_url,
                request_kwargs={"headers": headers, "timeout": timeout},
            ),
        )
        # Add retry middleware for timeouts and other connection errors
        self._retry_middleware = async_http_retry_request_middleware(
            retries=retry_limit, delay=retry_delay
        )
        self.w3.middleware_onion.add(self._retry_middleware)

    async def _make_request(self, method: RPCEndpoint, params: Any) -> RPCResponse:
        """Make a web3 request for non standard JSON RPC methods

        Note:
            E.g. trace_block, trace_replayTransaction
        """
        make_req = await self._retry_middleware(self.w3.provider.make_request, self.w3)
        return await make_req(method, params)

    async def get_block_data(self, block_id: str = "latest") -> BlockData:
        """Get block data by number/hash"""
        block_data_dict = await self.w3.eth.get_block(block_id)
        block_data = BlockData(**block_data_dict, w3_data=block_data_dict)
        return block_data

    async def get_latest_block_number(self) -> int:
        """Get latest block number"""
        return await self.w3.eth.block_number

    async def get_transaction_data(
        self, tx_hash: str
    ) -> Tuple[TransactionData, TxData]:
        """Get transaction data by hash

        Returns:
            tx_data (TransactionData)
            tx_data_dict (web3.TxData)
        """
        tx_data_dict = await self.w3.eth.get_transaction(tx_hash)
        tx_data = TransactionData(**tx_data_dict)
        return tx_data, tx_data_dict

    async def get_transaction_receipt_data(
        self, tx_hash: str
    ) -> Tuple[TransactionReceiptData, TxReceipt]:
        """Get transaction receipt data by hash

        Returns:
            tx_receipt_data (TransactionReceiptData)
            tx_receipt_data_dict (web3.TxReceipt)
        """
        tx_receipt_data_dict = await self.w3.eth.get_transaction_receipt(tx_hash)
        tx_receipt_data = TransactionReceiptData(**tx_receipt_data_dict)
        return tx_receipt_data, tx_receipt_data_dict

    async def get_block_reward(self, block_id="latest") -> dict[str, Any]:
        """Get block reward of a specific block"""
        data = await self._make_request("trace_block", [block_id])

        blockReward = 0
        for i in data["result"]:
            if i["type"] == "reward":
                blockReward = i["action"]["value"]
                break

        return int(blockReward, 16)

    async def get_internal_transactions(
        self, tx_hash: str
    ) -> List[InternalTransactionData]:
        """Get internal transaction data by hash"""
        data = await self._make_request("trace_replayTransaction", [tx_hash, ["trace"]])

        data_dict = []
        for i in data["result"]["trace"]:
            tx_data = i["action"]
            if result := i.get("result"):
                tx_data = tx_data | result
            data_dict.append(tx_data)

        internal_tx_data = list(
            map(lambda data: InternalTransactionData(**data), data_dict)
        )
        return internal_tx_data
