"""Script for executing pre defined SQL queries / statements."""
import argparse
import asyncio
import json
from datetime import datetime

import asyncpg
import matplotlib.pyplot as plt


async def cmd_plot_overview(conn, args):
    """ """
    print(datetime.now())

    # Get the number of transactions
    n_txs_record = await conn.fetchrow(
        "SELECT count(*) FROM (SELECT transaction_hash FROM eth_transaction) AS tx"
    )
    n_txs = n_txs_record["count"]
    print(f"Number of transactions: {n_txs}")

    # Get the number of blocks
    n_blocks_record = await conn.fetchrow(
        "SELECT count(*) FROM (SELECT block_number FROM eth_block) AS blk"
    )
    n_blocks = n_blocks_record["count"]
    print(f"Number of blocks: {n_blocks}")

    # Get the number of internal transactions
    n_internal_txs_record = await conn.fetchrow(
        "SELECT COUNT(*) FROM eth_internal_transaction"
    )
    n_internal_txs = n_internal_txs_record["count"]
    print(f"Number of internal transactions: {n_internal_txs}")

    # Get the number of logs
    n_logs_record = await conn.fetchrow("SELECT COUNT(*) FROM eth_transaction_logs")
    n_logs = n_logs_record["count"]
    print(f"Number of logs: {n_logs}")

    # Get sizes of tables
    table_sizes_record = await conn.fetch(
        """
        select
        table_name,
        pg_size_pretty(pg_relation_size(quote_ident(table_name))) as size_in_db,
        pg_relation_size(quote_ident(table_name))
        from information_schema.tables
        where table_schema = 'public'
        AND (table_name = 'eth_block' OR table_name = 'eth_transaction' OR table_name = 'eth_internal_transaction' OR table_name = 'eth_transaction_logs')
        ORDER BY 3 ASC
        """
    )
    table_sizes = [record["size_in_db"] for record in table_sizes_record]
    print(table_sizes)

    # Save as figure 1
    fig, ax = plt.subplots()
    bar_names = ("Blocks", "External Transactions", "Logs", "Internal Transactions")
    counts = [n_blocks, n_txs, n_logs, n_internal_txs]

    # ax.bar(bar_names, counts)
    bars = ax.barh(bar_names, counts)
    ax.bar_label(bars, fmt="{:,}", padding=16)
    ax.set_ylabel("Record Type")
    ax.set_xlabel("# of records in DB")
    ax.set_title("Database overview")
    ax.set_xscale("log")
    ax.set_xlim(1, 4e12)

    for bar, size_in_db in zip(ax.patches, table_sizes):
        ax.text(
            2,
            bar.get_y() + bar.get_height() / 2,
            size_in_db,
            color="white",
            ha="left",
            va="center",
        )

    fig.savefig(f"{args.output_dir}/database_overview.png", bbox_inches="tight")

    print(datetime.now())


async def cmd_plot_others(conn, args):
    """"""
    # Number of logs per contract
    n_logs_per_contract_records = await conn.fetch(
        """
        SELECT address, count(*) AS n_logs
        FROM eth_transaction_logs
        GROUP BY address
        ORDER BY n_logs DESC
        """
    )
    n_logs_per_contract = {
        r.get("address"): r.get("n_logs") for r in n_logs_per_contract_records
    }

    # Load config
    cfg = json.load(open(args.config_path))
    cfg_dict = {c["address"].lower(): c for c in cfg["data_collection"][0]["contracts"]}
    symbols = []
    contract_categories = []
    contract_colors = {
        "UniSwapV2Pair": "lightskyblue",
        "erc20": "green",
        "erc721": "orange",
    }
    n_logs_per_symbol = []

    def remove_prefix(s, prefix):
        return s[len(prefix) :] if s.startswith(prefix) else s

    for address, n_logs in n_logs_per_contract.items():
        address = address.lower()
        if cfg_dict.get(address):
            symbol = remove_prefix(cfg_dict[address]["symbol"], "UniSwap V2 Pair ")
            symbols.append(symbol)
            contract_categories.append(cfg_dict[address]["category"])
            n_logs_per_symbol.append(n_logs)

    # Save as figure 1
    fig, ax = plt.subplots(figsize=(20, 10))

    for i, symbol in enumerate(symbols):
        color = contract_colors[contract_categories[i]]
        ax.bar(symbol, n_logs_per_symbol[i], color=color, label=contract_categories[i])

    ax.set_ylabel("# of logs")
    ax.set_xlabel("Symbol")
    ax.set_title("Number of logs per contract")
    ax.set_yscale("log")
    ax.set_xticklabels(symbols, rotation=90)
    labels = list(contract_colors.keys())
    ax.legend(
        [plt.Rectangle((0, 0), 1, 1, color=contract_colors[label]) for label in labels],
        labels,
        loc="upper right",
        prop={"size": 14},
    )

    fig.savefig(
        f"{args.output_dir}/database_logs_per_contract.png", bbox_inches="tight"
    )


async def cmd_event(conn, args):
    """Event command handler

    Args:
        conn (asyncpg.Connection): connection to the database
        args (argparse.args): command line arguments
    """
    raise NotImplementedError()


async def cmd_supply(conn, args):
    """Supply command handler

    Args:
        conn (asyncpg.Connection): connection to the database
        args (argparse.args): command line arguments
    """

    async with conn.transaction():
        # Postgres requires non-scrollable cursors to be created
        # and used in a transaction.

        # Base string and args of the SQL query
        query = """
        SELECT S.amount_changed, B.timestamp
        FROM eth_contract_supply_change AS S
        INNER JOIN eth_transaction AS T
          ON S.transaction_hash=T.transaction_hash
          AND S.address=$1
        INNER JOIN eth_block AS B
          ON T.block_number=B.block_number
          AND T.block_number >= $2
        """
        query_args = [args.address, args.start_block]

        # Update the query if end_block is supplied
        if args.end_block:
            query += "\n  AND T.block_number < $3"
            query_args.append(args.end_block)

        # Finish the query
        query += "\nORDER BY B.timestamp ASC"

        # Create a Cursor object - Total supply change vs time in a given block interval
        # https://magicstack.github.io/asyncpg/current/api/index.html?highlight=fetch#cursors
        cur = conn.cursor(query, *query_args)

        n_records = 0
        async for record in cur:
            n_records += 1
            print(record)

        if n_records == 0:
            print(f"No supply changes found for specified address ('{args.address}').")


async def main():
    parser = argparse.ArgumentParser(description="PostgreSQL query tool")
    # Set default function to None
    parser.set_defaults(func=None)
    parser.add_argument(
        "--db-dsn",
        help="PostgreSQL DSN ('postgresql://<user>:<pw>@<host>:<port>/<dbname>')",
        required=True,
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(description="Available commands")

    # 'event' command
    parser_event = subparsers.add_parser(
        name="event", description="Selects transaction logs that contain an event"
    )
    parser_event.set_defaults(func=cmd_event)
    parser_event.add_argument(
        "-t", "--type", help="The event type (Transfer, Swap, ...)", required=True
    )
    parser_event.add_argument(
        "-a", "--address", help="Compute the total amount of events for a contract"
    )

    # 'supply' command
    parser_supply = subparsers.add_parser(
        name="supply", description="Show the supply changes for a given contract"
    )
    parser_supply.set_defaults(func=cmd_supply)
    parser_supply.add_argument(
        "-a", "--address", help="Contract address to compute supply for", required=True
    )

    parser_supply.add_argument(
        "-s", "--start-block", help="Starting block, included.", type=int, default=0
    )
    parser_supply.add_argument(
        "-e", "--end-block", help="Ending block, not included.", type=int, default=None
    )

    # 'plot_overview' command
    parser_plot = subparsers.add_parser(
        name="plot_overview",
        description="Plot overview graphs from data in the database",
    )
    parser_plot.set_defaults(func=cmd_plot_overview)
    parser_plot.add_argument(
        "-o", "--output-dir", help="Output directory name", required=True
    )

    # 'plot_others' command
    parser_plot = subparsers.add_parser(
        name="plot_others", description="Plot some graphs from data in the database"
    )
    parser_plot.set_defaults(func=cmd_plot_others)
    parser_plot.add_argument(
        "-o", "--output-dir", help="Output directory name", required=True
    )
    parser_plot.add_argument(
        "-c", "--config-path", help="Path to the config file", required=True
    )

    # Get the CLI arguments
    args = parser.parse_args()

    if args.func:
        dsn = args.db_dsn
        # Establish a postgres connection
        conn = await asyncpg.connect(dsn=dsn)

        try:
            # Execute the correct command
            await args.func(conn, args)
        finally:
            # Exit postgres
            await conn.close()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
