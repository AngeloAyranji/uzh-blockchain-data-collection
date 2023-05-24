"""Script for executing pre defined SQL queries / statements."""
import argparse
import asyncio

import asyncpg


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
