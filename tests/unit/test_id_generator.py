import pytest

from pulseroute.common.base62 import decode_base62, encode_base62
from pulseroute.common.id_generator import SnowflakeGenerator, generate_unique_slug


def test_snowflake_uniqueness():
    gen = SnowflakeGenerator(node_id=1)
    ids = [gen.next_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    assert all(i > 0 for i in ids)


def test_base62_roundtrip():
    test_numbers = [0, 1, 61, 62, 1000, 999999, 123456789012345]
    for num in test_numbers:
        encoded = encode_base62(num)
        assert isinstance(encoded, str)
        assert decode_base62(encoded) == num


def test_base62_zero():
    assert encode_base62(0) == "0"
    assert decode_base62("0") == 0


@pytest.mark.asyncio
async def test_generate_unique_slug_fallback():
    slug = await generate_unique_slug(redis_cli=None, length=6)
    assert len(slug) == 6
    assert isinstance(slug, str)
