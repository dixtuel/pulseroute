from pulseroute.common.base62 import decode_base62, encode_base62


def test_base62_roundtrip():
    test_numbers = [0, 1, 61, 62, 1000, 999999, 123456789012345]
    for num in test_numbers:
        encoded = encode_base62(num)
        assert isinstance(encoded, str)
        assert decode_base62(encoded) == num


def test_base62_zero():
    assert encode_base62(0) == "0"
    assert decode_base62("0") == 0
