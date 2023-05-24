# etc/
This directory contains miscellaneous python scripts with some basic functionality.

## Get top uniswap pairs
This script provides uses TheGraph API to obtain the top N uniswap pairs and prints them in a JSON format ready to be plugged into the data collection config.json.

Example usage:
```
$ python etc/get_top_uniswap_pairs.py -n 2 -e TransferFungibleEvent
[
  {
    "address": "0xe6c78983b07a07e0523b57e18aa23d3ae2519e05",
    "symbol": "UniSwap V2 Pair UETH-ULCK",
    "category": "UniSwapV2Pair",
    "events": [
      "TransferFungibleEvent"
    ]
  },
  {
    "address": "0x21b8065d10f73ee2e260e5b47d3344d3ced7596e",
    "symbol": "UniSwap V2 Pair WISE-WETH",
    "category": "UniSwapV2Pair",
    "events": [
      "TransferFungibleEvent"
    ]
  }
]
```

For details see `python etc/get_top_uniswap_pairs.py --help`.

## Query Tool
This script connects to a running PostgreSQL container and executes some pre-definde (complex) queries or statements.

For usage check `python etc/query_tool.py --help`

## Web3 request response times benchmark
This script benchmarks various web3 method request response times and prints out the statistics.

```
$ python etc/web3_method_benchmark.py
Starting web3 method benchmark (100 requests per method)
Current datetime (UTC): 2023-05-19T01:27:58.565685
---
Method 'get_block' response times: min/avg/max/stddev = 2.710/287.932/28308.644/2830.376 ms
Method 'get_transaction' response times: min/avg/max/stddev = 6.486/10.593/31.352/3.633 ms
Method 'trace_replayTransaction' response times: min/avg/max/stddev = 4.613/24.937/302.657/34.666 ms
Method 'trace_block' response times: min/avg/max/stddev = 3.558/746.057/13526.098/1383.323 ms
```
