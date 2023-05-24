import asyncio
import statistics
import time
from datetime import datetime
from typing import List

from web3 import Web3
from web3.eth import AsyncEth
from web3.geth import AsyncGethAdmin, AsyncGethPersonal, AsyncGethTxPool, Geth
from web3.net import AsyncNet

node_url = "http://localhost:8547"

headers = {
    "Host": "localhost",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
}
w3 = Web3(
    provider=Web3.AsyncHTTPProvider(
        endpoint_uri=node_url, request_kwargs={"headers": headers, "timeout": 300}
    ),
    modules={
        "eth": (AsyncEth,),
        "net": (AsyncNet,),
        "geth": (
            Geth,
            {
                "txpool": (AsyncGethTxPool,),
                "perosnal": (AsyncGethPersonal,),
                "admin": (AsyncGethAdmin,),
            },
        ),
    },
    middlewares=[],
)

N_REQUESTS = 100


def print_method_response_time_statistics(method_name: str, request_times: List[float]):
    min_r = min(request_times)
    avg_r = sum(request_times) / len(request_times)
    max_r = max(request_times)
    stddev_r = statistics.stdev(request_times)
    print(
        f"Method '{method_name}' response times: min/avg/max/stddev = {min_r:.3f}/{avg_r:.3f}/{max_r:.3f}/{stddev_r:.3f} ms"
    )


async def main(block_number):
    """
    Args:
        block_number: starting block number
    """
    print(f"Starting web3 method benchmark ({N_REQUESTS} requests per method)")
    print(f"Current datetime (UTC): {datetime.utcnow().isoformat()}\n---")
    request_times_getBlock = []
    # keep a list of txs for later
    tx_hashes = []
    for i in range(N_REQUESTS):
        start = time.perf_counter()
        block_data = await w3.eth.get_block(block_number + i)
        if len(block_data["transactions"]) > 1 and len(tx_hashes) < N_REQUESTS:
            tx_hashes.append(block_data["transactions"][0])
            tx_hashes.append(block_data["transactions"][1])
        request_times_getBlock.append((time.perf_counter() - start) * 1000)
        time.sleep(0.05)

    # to ms divided by n_reqs
    print_method_response_time_statistics("get_block", request_times_getBlock)

    request_times_getTransaction = []
    for i in range(N_REQUESTS):
        start = time.perf_counter()
        tx_data_dict = await w3.eth.get_transaction(tx_hashes[i])
        request_times_getTransaction.append((time.perf_counter() - start) * 1000)
        time.sleep(0.05)

    print_method_response_time_statistics(
        "get_transaction", request_times_getTransaction
    )

    request_times_internaltx = []
    for i in range(N_REQUESTS):
        """Get internal transaction data by hash"""
        start = time.perf_counter()
        data = await w3.provider.make_request(
            "trace_replayTransaction", [tx_hashes[i].hex(), ["trace"]]
        )
        request_times_internaltx.append((time.perf_counter() - start) * 1000)
        time.sleep(0.05)

    print_method_response_time_statistics(
        "trace_replayTransaction", request_times_internaltx
    )

    request_times_blockReward = []
    for i in range(N_REQUESTS):
        start = time.perf_counter()
        data = await w3.provider.make_request("trace_block", [block_number + i])
        request_times_blockReward.append((time.perf_counter() - start) * 1000)
        time.sleep(0.05)

    print_method_response_time_statistics("trace_block", request_times_blockReward)


asyncio.run(main(15500000))
