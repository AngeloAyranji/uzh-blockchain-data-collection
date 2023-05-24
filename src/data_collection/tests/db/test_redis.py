import pytest


class TestRedisManager:
    @pytest.mark.usefixtures("clean_redis")
    @pytest.mark.parametrize("amount", [10, -15, 0])
    async def test_incrby(self, redis_manager, amount):
        """Test incrby n transactions for a single partition"""
        partition = 0
        await redis_manager.incrby_n_transactions(partition, amount)

        retrieved_amount = await redis_manager.redis.zmscore(
            redis_manager._sorted_set_key, [partition]
        )
        assert retrieved_amount[0] == amount

    @pytest.mark.usefixtures("clean_redis")
    @pytest.mark.parametrize("n_decr", [1, 4])
    async def test_decr(self, redis_manager, n_decr):
        """Test decr for a single partition"""
        partition = 0
        for _ in range(n_decr):
            await redis_manager.decr_transactions(partition)

        retrieved_amount = await redis_manager.redis.zmscore(
            redis_manager._sorted_set_key, [partition]
        )
        assert retrieved_amount[0] == -1 * n_decr

    @pytest.mark.usefixtures("clean_redis")
    async def test_get_lowest_score_partition(self, redis_manager):
        """Test whether the lowest score partition is returned"""
        # Insert a "score" (n_transactions / n_messages / n_events)
        # for a few partitions
        min_partition = 1
        await redis_manager.incrby_n_transactions(partition=0, incr_by=2800)
        await redis_manager.incrby_n_transactions(partition=min_partition, incr_by=24)
        await redis_manager.incrby_n_transactions(partition=2, incr_by=135)

        lowest_score_partition = await redis_manager.get_lowest_score_partition()

        assert lowest_score_partition == min_partition

    @pytest.mark.usefixtures("clean_redis")
    async def test_get_lowest_score_partition_notexists(self, redis_manager):
        """
        Test whether the lowest score partition is None if
        no partitions were created
        """
        lowest_score_partition = await redis_manager.get_lowest_score_partition()

        assert lowest_score_partition is None

    @pytest.mark.usefixtures("clean_redis")
    async def test_get_lowest_score_partition_equal(self, redis_manager):
        """
        Test whether the lowest score partition is None if
        no partitions were created
        """
        # Insert the same "score" for two partitions
        await redis_manager.incrby_n_transactions(partition=0, incr_by=10)
        await redis_manager.incrby_n_transactions(partition=1, incr_by=10)
        lowest_score_partition = await redis_manager.get_lowest_score_partition()

        assert lowest_score_partition == 0 or lowest_score_partition == 1

    @pytest.mark.usefixtures("clean_redis")
    @pytest.mark.parametrize("amounts", [[2500, 165, 41100, 0, 222], []])
    async def test_get_n_transactions(self, redis_manager, amounts):
        """Test the total number of transactions is correct"""
        for i in range(len(amounts)):
            await redis_manager.incrby_n_transactions(partition=i, incr_by=amounts[i])

        n_txs = await redis_manager.get_n_transactions()

        assert n_txs == sum(
            amounts
        ), "The total number of transactions must be equal to the sum of inserted txs"
