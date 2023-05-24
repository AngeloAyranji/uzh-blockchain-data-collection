import argparse
import json
import sys

import requests


# function to use requests.post to make an API call to the subgraph url
def run_query(query):
    # endpoint where you are making the request
    request = requests.post(
        "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2" "",
        json={"query": query},
    )
    if request.status_code == 200:
        return request.json()
    else:
        raise Exception(
            "Query failed. return code is {}.      {}".format(
                request.status_code, query
            )
        )


def main(args):
    """Execute the GQL query and pretty print the resulting pairs."""
    query_init = """
    {{
    pairs(first: {0}, orderBy: reserveUSD, orderDirection: desc) {{
    id
    token0{{
        id
        symbol
        name
        txCount
        totalLiquidity
        decimals
    }}
    token1{{
        id
        symbol
        name
        txCount
        totalLiquidity
        decimals
    }}
    reserve0
    reserve1
    totalSupply
    reserveUSD
    reserveETH
    txCount
    createdAtTimestamp
    createdAtBlockNumber
    }}
    }}
    """.format(
        str(args.n)
    )
    query_result = run_query(query_init)

    # Create the result json that will be used in our config
    result = []
    if query_result is None:
        print(
            "TheGraph API returned an invalid value as the query result. Please try again later."
        )
        sys.exit(1)

    for pair in query_result["data"]["pairs"]:
        token0 = pair["token0"]
        token1 = pair["token1"]
        result.append(
            dict(
                address=pair["id"],
                symbol=f"UniSwap V2 Pair {token0['symbol']}-{token1['symbol']}",
                category="UniSwapV2Pair",
                events=args.events,
            )
        )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Top Uniswap pairs generator")

    parser.add_argument(
        "-n", help="The amount of pairs to query", type=int, default=100
    )
    parser.add_argument(
        "-e",
        "--events",
        help="The event names to include for the pairs",
        nargs="+",
        default=[],
        type=str,
    )

    args = parser.parse_args()
    main(args)
