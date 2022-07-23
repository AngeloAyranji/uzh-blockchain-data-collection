import argparse
import asyncio

from app.config import Config


async def main(config: Config):
    pass


if __name__ == "__main__":
    # CLI arguments parser
    parser = argparse.ArgumentParser(description="Block Consumer")
    parser.add_argument(
        "--cfg",
        help="The configuration file",
        type=str,
        required=True
    )
    args = parser.parse_args()

    # Load the config file
    config = Config.parse_file(args.cfg)

    # Run the app
    asyncio.run(main(config))
