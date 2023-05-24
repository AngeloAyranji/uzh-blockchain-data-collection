import asyncio
from asyncio import TimeoutError
from functools import wraps
from typing import Awaitable, Callable, List, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError, KafkaTimeoutError
from aiokafka.structs import RecordMetadata

from app import init_logger
from app.db.redis import RedisManager
from app.kafka.exceptions import KafkaConsumerPartitionsEmptyError, KafkaManagerError

log = init_logger(__name__)


class KafkaManager:
    """
    Manage the Kafka cluster connection.
    Base class for KafkaProducerManager and KafkaConsumerManager.
    """

    # The delay between connection attempts (in seconds)
    LINEAR_BACKOFF_DELAY = 5
    # The maximum allowed initial connection attempts before the app exits
    INITIAL_CONNECTION_MAX_ATTEMPTS = 10

    def __init__(self, kafka_url: str, topic: str, redis_url: str) -> None:
        """
        Args:
            kafka_url: the url of the Kafka cluster
            topic: the Kafka topic
        """
        self.topic = topic
        self._client = None
        self.redis_manager = RedisManager(redis_url=redis_url, topic=topic)

    async def connect(self):
        """Connect (with linear backoff) to the kafka cluster.

        Note:
            Retrying with linear backoff is required as the
            startup time of Kafka is variable (usually 25-35s)
        """
        connected, attempt_i = False, 0

        while not connected:
            # Check if we haven't reached max attempts
            attempt_i += 1
            if attempt_i > self.INITIAL_CONNECTION_MAX_ATTEMPTS:
                # Need to cleanup the producer before exiting.
                await self._client.stop()
                # Exit the app if the max attempts have been reached
                raise KafkaManagerError(
                    "Maximum number of initial connection attempts reached."
                )
            # Try to connect to the cluster
            try:
                await self._client.start()
                # If the call above doesn't raise an exception,
                # we're connected.
                connected = True
            except KafkaConnectionError as err:
                # Retry if we get an exception
                log.info(
                    f"Connection failed - retrying in {self.LINEAR_BACKOFF_DELAY}s"
                )
                await asyncio.sleep(self.LINEAR_BACKOFF_DELAY)
                continue
        log.debug("Connected to Kafka")

    async def disconnect(self):
        """Flush pending data and disconnect from the kafka cluster"""
        await self._client.stop()
        log.debug("Disconnected from Kafka")


class KafkaProducerManager(KafkaManager):
    """Manage producing events to a given Kafka topic"""

    MAX_MESSAGES_PER_PARTITION = 1000
    """Maximum amount of messages (events) stored in a single partition."""
    MESSAGES_PER_BATCH = 1024
    """
    Maximum amount of messages (events) in a single batch

    Note:   Even though the `AIOKafkaProducer` class contains a max_batch_size parameter, it is not very useful. This
            parameter refers to the *byte* size of the kafka batch, not the message / event count. Currently the default
            value of '16384' for max_batch_size caps the total message count in one batch to circa 210 messages. To get
            around this we have to create multiple batches in the size of `MESSAGES_PER_BATCH`. Or increase
            `max_batch_size` along with `message.max.bytes` in Kafka directly.
    """

    def __init__(self, kafka_url: str, redis_url: str, topic: str) -> None:
        super().__init__(kafka_url=kafka_url, redis_url=redis_url, topic=topic)
        self._client = AIOKafkaProducer(
            bootstrap_servers=kafka_url,
            enable_idempotence=True,
            max_batch_size=1024 * 128,  # 128 KB
        )
        # The currently selected partition that will receive the next batch of messages
        # Start at 0
        self._i_partition = 0

    def limit_topic_capacity(f):
        """Decorator that limits the amount of messages in a topic to MAX_MESSAGES_PER_PARTITION * n_partitions"""

        async def inner(self, *args, **kwargs):
            stall_counter = 0
            waiting_for_space = True
            while waiting_for_space:
                # Verify that there is space in the Kafka topic for more transaction hashes
                if n_txs := await self.redis_manager.get_n_transactions():
                    # Compute total max allowed messages in all partitions each time
                    # because # of partitions can change
                    n_part = await self.number_of_partitions
                    total_allowed_messages_in_partitions = (
                        self.MAX_MESSAGES_PER_PARTITION * n_part
                    )
                    if n_txs > total_allowed_messages_in_partitions:
                        if stall_counter % 60 == 0 and stall_counter:
                            # Log info about the stall every 60 seconds
                            log.warning(
                                f"Producing stalled for {stall_counter} seconds."
                            )
                        stall_counter += 1
                        # Sleep if there are too many transactions in the kafka topic
                        await asyncio.sleep(1)
                        # Try again after sleeping
                        continue
                    else:
                        waiting_for_space = False
                    # Print out info about the stall
                    if stall_counter >= 60:
                        log.info(
                            f"Continuing producing after stalling for {stall_counter} seconds."
                        )
                elif stall_counter == 0:
                    # Else if n_txs is None and stall_counter is 0, the topic (each parition) is completely empty
                    break
            result = await f(self, *args, **kwargs)
            return result

        return inner

    @property
    async def number_of_partitions(self) -> int:
        """Return the number of partitions in this topic"""
        partitions = await self._client.partitions_for(self.topic)
        return len(partitions)

    async def _choose_partition(self) -> int:
        """Return the partition that should receive the next batch of messages (events)"""
        # Choose partition
        partition = self._i_partition
        if self._i_partition != -1:
            # Increment
            self._i_partition += 1
            # If the _i_partition is the last partition,
            # continue using the mechanism that chooses a partition with the smallest amount of present txs
            if self._i_partition == await self.number_of_partitions:
                self._i_partition = -1
        else:
            partition = await self.redis_manager.get_lowest_score_partition() or 0
        return partition

    @limit_topic_capacity
    async def send_message(self, msg: str) -> Optional[RecordMetadata]:
        """Send message to a Kafka broker"""
        try:
            # Send the message
            send_future = await self._client.send(topic=self.topic, value=msg.encode())
            # Message will either be delivered or an unrecoverable
            # error will occur.
            record = await send_future

            if record:
                # Increment the appropriate partition by 1
                await self.redis_manager.incrby_n_transactions(
                    record.partition, incr_by=1
                )

                return record
            return None
        except KafkaTimeoutError:
            # Producer request timeout, message could have been sent to
            # the broker but there is no ack
            # TODO: somehow figure out whether this message should be
            # resent or not, maybe flag this message with a 'check_duplicate'
            # flag and let the consumer figure it out if these transactions are already
            # present in the database
            log.error(f"KafkaTimeoutError on {msg}")
        except KafkaError as err:
            # Generic kafka error
            log.error(f"{err} on {msg}")
            raise err

    @limit_topic_capacity
    async def send_batch(self, msgs: List[str]) -> List[RecordMetadata]:
        """Send a batch of messages to a Kafka broker"""
        if not msgs:
            log.warning("Attempted to send an empty list of messages.")
            return []
        try:
            # Split messages into chunks of size MESSAGES_PER_BATCH
            n_messages_per_batch = max(1, self.MESSAGES_PER_BATCH)
            chunks = (
                msgs[i : i + n_messages_per_batch]
                for i in range(0, len(msgs), n_messages_per_batch)
            )

            # Save `RecordMetadata` for each batch that was sent successfully
            batches_recordmetadata = []
            # Send each chunk in a separate batch
            for chunk in chunks:
                kafka_batch = self._client.create_batch()
                # Keep count of messages that were appended to the current Kafka Batch
                n_appended_messages = 0
                for msg in chunk:
                    # key and timestamp arguments are required
                    metadata = kafka_batch.append(
                        value=msg.encode(), key=None, timestamp=None
                    )
                    if metadata:
                        # Increase the counter if a Metadata object is returned
                        n_appended_messages += 1
                    else:
                        # Otherwise log a warning that Kafka might be misconfigured
                        log.warning(
                            (
                                f"No metadata found for tx ({msg}) while inserting into a batch."
                                f"This transaction has not been added to a kafka topic."
                                f"Decrease the value of MESSAGES_PER_BATCH or increase `AIOKafkaProducer.max_batch_size`"
                                f" to avoid losing further messages!"
                            )
                        )

                kafka_batch.close()
                partition = await self._choose_partition()

                # Add the batch to the partition's submission queue. If this method
                # times out, we can say for sure that batch will never be sent.
                send_fut = await self._client.send_batch(
                    kafka_batch, self.topic, partition=partition
                )

                # Batch will either be delivered or an unrecoverable error will occur.
                # Cancelling this future will not cancel the send.
                record = await send_fut

                if record:
                    # Increment the appropriate partition by the number of messages that were present in this batch
                    await self.redis_manager.incrby_n_transactions(
                        record.partition, incr_by=n_appended_messages
                    )
                    batches_recordmetadata.append(record)
                else:
                    log.warning(
                        f"Couldn't increment partition {partition} by {len(chunk)} because RecordMetadata doesn't exist."
                    )

            return batches_recordmetadata
        except KafkaTimeoutError:
            # Producer request timeout, message could have been sent to
            # the broker but there is no ack
            # TODO: somehow figure out whether this message should be
            # resent or not, maybe flag this message with a 'check_duplicate'
            # flag and let the consumer figure it out if these transactions are already
            # present in the database
            log.error(f"KafkaTimeoutError on batch")


class KafkaConsumerManager(KafkaManager):
    """Manage consuming events from a given Kafka topic"""

    def __init__(
        self, kafka_url: str, redis_url: str, topic: str, event_retrieval_timeout: int
    ) -> None:
        super().__init__(kafka_url=kafka_url, redis_url=redis_url, topic=topic)
        self._client = AIOKafkaConsumer(
            topic,
            bootstrap_servers=kafka_url,
            group_id=topic,
            auto_offset_reset="earliest",
        )
        # How much time (in seconds) to wait for the next event / message
        # from a Kafka topic before timing out the consumer
        self.event_retrieval_timeout = event_retrieval_timeout

        ##  Events
        # asyncio Event that is used for timing out
        # when no message from Kafka is received for some time
        self.kafka_timeout_event = asyncio.Event()

        # asyncio Event that is used for indefinite waiting while
        # consumer is consuming messages from Kafka
        self.kafka_consuming_event = asyncio.Event()

    async def _event_timeout_task(self):
        """Raise an exception if event.set() is not called for event_retrieval_timeout seconds"""
        try:
            while True:
                # Wait for event.set() to be called for event_retrieval_timeout seconds
                await asyncio.wait_for(
                    self.kafka_timeout_event.wait(), self.event_retrieval_timeout
                )
                # Reset the event timeout to wait another event_retrieval_timeout seconds for a new Kafka event
                self.kafka_timeout_event.clear()
                # Wait for the consumer to finish consuming the event
                await asyncio.wait_for(self.kafka_consuming_event.wait(), None)
                # Reset the consuming event
                self.kafka_consuming_event.clear()
        except TimeoutError as e:
            # Catch asyncio.TimeoutError from the wait event timeout and reraise it as KafkaConsumerTopicEmptyError
            # because there are no more events in the partitions
            raise KafkaConsumerPartitionsEmptyError from e

    async def _start_listening_on_topic_task(
        self,
        on_event_callback: Callable[[str], Awaitable[None]],
    ):
        """Listen for new Kafka messages on a predefined topic"""
        try:
            # Wait for new events from Kafka and call the callback
            async for event in self._client:
                # Notify the timeout task that we've received a new Kafka topic message
                self.kafka_timeout_event.set()
                # Decrement the amount of events / messages in the partition
                # this message was retrieved from
                await self.redis_manager.decr_transactions(event.partition)
                # Await the async callback
                await on_event_callback(event)
                # Notify the consuming event that we've finished consuming the Kafka message
                self.kafka_consuming_event.set()
        except TimeoutError:
            log.warning("Timed out in the listening on topic task")
            raise

    async def start_consuming(
        self, on_event_callback: Callable[[str], Awaitable[None]]
    ):
        """Consume messages from a given topic and generate (yield) events

        Args:
            on_event_callback: a callback function that is called when a new event is received from Kafka
        """
        try:
            # Log information about the partitions that this consumer is consuming from
            partitions = list(map(lambda p: p.partition, self._client.assignment()))
            log.info(
                f"Consuming events in topic '{self.topic}' for partitions: {partitions}"
            )

            # Create a consume task
            consume_task = asyncio.create_task(
                self._start_listening_on_topic_task(on_event_callback)
            )

            # Create a task for a timeout counter to run in the background
            timeout_task = asyncio.create_task(self._event_timeout_task())

            # Wait for consuming to finish
            # (with a timeout task that can interrupt the consume task by raising an exception)
            await asyncio.gather(timeout_task, consume_task)

        except KafkaConsumerPartitionsEmptyError:
            # Raised when no message is received within the specified time
            log.info(
                f"No event received for {self.event_retrieval_timeout} seconds from any partition - timed out"
            )
            raise
        finally:
            # Disconnect from Kafka
            await self.disconnect()
