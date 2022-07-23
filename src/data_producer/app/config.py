from pydantic import (
    BaseSettings,
    AnyUrl
)


class Config(BaseSettings):
    """Describes an app configuration file"""

    # The blockchain node RPC API URL
    node_url: AnyUrl

    # The PostgreSQL database URL
    db_url: AnyUrl

    # Kafka URL
    kafka_url: AnyUrl

