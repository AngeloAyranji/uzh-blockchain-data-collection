class KafkaManagerError(Exception):
    """Class for KafkaManager related errors"""

    pass


class KafkaConsumerPartitionsEmptyError(KafkaManagerError):
    """Raised when a message is not retrieved from any partition for a some time."""

    pass


class KafkaConsumerTimeoutError(KafkaManagerError):
    """Raised when a TimeoutError happens during consuming transactions.

    Note:
        This exception is not raised when simply waiting for new topic events.
    """
