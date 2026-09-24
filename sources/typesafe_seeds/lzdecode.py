"""Minimal pure-Python port of lz-string's decompressFromEncodedURIComponent.

The TypeSafe docs embed each cookbook's playground request (state + questions) in a
`console.typesafe.ai/playground#share/<lz-string>` link; this decodes those links.
"""

from __future__ import annotations

_KEY = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-$"
_IDX = {c: i for i, c in enumerate(_KEY)}


def decompress_uri(data: str) -> str | None:
    data = data.replace(" ", "+")
    if not data:
        return ""
    return _decompress(len(data), 32, lambda i: _IDX[data[i]], data)


def _decompress(length: int, reset_value: int, get_next, _src) -> str | None:
    dictionary: dict[int, str] = {0: "0", 1: "1", 2: "2"}
    enlarge_in, dict_size, num_bits = 4, 4, 3
    result: list[str] = []
    pos, val, index = reset_value, get_next(0), 1

    def read(nbits: int) -> int:
        nonlocal pos, val, index
        bits, power, maxpower = 0, 1, 1 << nbits
        while power != maxpower:
            resb = val & pos
            pos >>= 1
            if pos == 0:
                pos = reset_value
                val = get_next(index) if index < length else 0
                index += 1
            bits |= (1 if resb > 0 else 0) * power
            power <<= 1
        return bits

    nxt = read(2)
    if nxt == 0:
        c = chr(read(8))
    elif nxt == 1:
        c = chr(read(16))
    else:
        return ""
    dictionary[3] = c
    w = c
    result.append(c)
    while True:
        if index > length:
            return ""
        cc = read(num_bits)
        if cc == 0:
            dictionary[dict_size] = chr(read(8))
            dict_size += 1
            cc = dict_size - 1
            enlarge_in -= 1
        elif cc == 1:
            dictionary[dict_size] = chr(read(16))
            dict_size += 1
            cc = dict_size - 1
            enlarge_in -= 1
        elif cc == 2:
            return "".join(result)
        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1
        if cc in dictionary:
            entry = dictionary[cc]
        elif cc == dict_size:
            entry = w + w[0]
        else:
            return None
        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1
        w = entry
        if enlarge_in == 0:
            enlarge_in = 1 << num_bits
            num_bits += 1
