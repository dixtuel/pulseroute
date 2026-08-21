import time

import redis.asyncio as aioredis


class SnowflakeGenerator:
    """
    Twitter Snowflake-inspired 64-bit Distributed ID Generator.
    - 41 bits: Timestamp (milliseconds since custom epoch ~69 years)
    - 10 bits: Machine/Node ID (0-1023)
    - 12 bits: Sequence counter (0-4095 per millisecond)
    """
    EPOCH = 1704067200000  # 2024-01-01 00:00:00 UTC

    def __init__(self, node_id: int = 1):
        self.node_id = node_id & 0x3FF
        self.sequence = 0
        self.last_timestamp = -1

    def next_id(self) -> int:
        timestamp = int(time.time() * 1000) - self.EPOCH
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 0xFFF
            if self.sequence == 0:
                while timestamp <= self.last_timestamp:
                    timestamp = int(time.time() * 1000) - self.EPOCH
        else:
            self.sequence = 0

        self.last_timestamp = timestamp
        return (timestamp << 22) | (self.node_id << 12) | self.sequence


snowflake = SnowflakeGenerator(node_id=1)


async def generate_unique_slug(redis_cli: aioredis.Redis | None = None, length: int = 6) -> str:
    from pulseroute.common.base62 import encode_base62
    if redis_cli:
        try:
            val = await redis_cli.incr("pulseroute:global:id_counter")
            slug = encode_base62(val)
            if len(slug) < length:
                slug = slug.rjust(length, "0")
            return slug
        except Exception:
            pass
    # Fallback to Snowflake + Base62
    unique_id = snowflake.next_id()
    slug = encode_base62(unique_id)
    return slug[-length:] if len(slug) >= length else slug.rjust(length, "0")
