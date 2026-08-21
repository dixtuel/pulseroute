import string

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
BASE = len(BASE62_ALPHABET)


def encode_base62(num: int) -> str:
    """Encode an integer to a Base62 string."""
    if num == 0:
        return BASE62_ALPHABET[0]
    arr = []
    while num:
        num, rem = divmod(num, BASE)
        arr.append(BASE62_ALPHABET[rem])
    arr.reverse()
    return "".join(arr)


def decode_base62(b62_str: str) -> int:
    """Decode a Base62 string back to an integer."""
    num = 0
    for char in b62_str:
        num = num * BASE + BASE62_ALPHABET.index(char)
    return num
