from pulseroute.common.id_generator import SnowflakeGenerator


def test_snowflake_uniqueness():
    gen = SnowflakeGenerator(node_id=1)
    ids = [gen.next_id() for _ in range(1000)]
    assert len(set(ids)) == 1000
    assert all(i > 0 for i in ids)
