from typing import Optional

from redis import asyncio as aioredis

from app import init_logger

log = init_logger(__name__)


class RedisManager:
    """Manage a Redis DB connection and CRUD operations

    Mainly used to keep the current number of messages (transaction hashes) in a given topic.
    """

    def __init__(self, redis_url: str, topic: str) -> None:
        """
        Args:
            redis_url (str): the url to a Redis database
            topic (str): the topic that this manager is associated with (topic=node name)
        """
        # The redis database instance
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        # The key used for storing the number of transactions per partition in Redis
        self._sorted_set_key = f"{topic}_n_transactions"

    async def get_n_transactions(self) -> int:
        """Return the total number of unprocessed transactions from all partitions"""
        if sorted_partitions := await self.redis.zrange(
            name=self._sorted_set_key, start=0, end=-1, withscores=True
        ):
            return sum([int(pair[1]) for pair in sorted_partitions])
        return 0

    async def get_lowest_score_partition(self) -> Optional[int]:
        """Return the name of the partition with the lowest score"""
        if sorted_partitions := await self.redis.zrange(
            name=self._sorted_set_key, start=0, end=-1
        ):
            return int(sorted_partitions[0])
        return None

    async def decr_transactions(self, partition: int):
        """Decrement the number of transactions by one for the given partition"""
        await self.incrby_n_transactions(partition=partition, incr_by=-1)

    async def incrby_n_transactions(self, partition: int, incr_by: int = 1):
        """Increment the number of transactions for a given partition"""
        await self.redis.zincrby(self._sorted_set_key, incr_by, partition)
