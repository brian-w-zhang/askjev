"""Deterministic, prefix-stable sampling helpers for source adapters (Phase 6 scale-up).

Adapters keep their original seeded sample (so existing question ids stay put) and grow it with
`top_up`: the remaining pool is ordered by a salted hash of each item's stable key and the first k are
taken. Hash order does not depend on k, so a larger target always contains a smaller one.
"""

from __future__ import annotations

import hashlib
import os
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


def env_int(name: str, default: int) -> int:
    """`ASKJEV_<name>` from the environment, else the adapter's original default."""
    return int(os.environ.get(f"ASKJEV_{name}", default))


def hash_order(items: Iterable[T], key: Callable[[T], object], salt: str) -> list[T]:
    return sorted(items, key=lambda x: hashlib.sha256(f"{salt}|{key(x)}".encode()).hexdigest())


def top_up(taken: list[T], pool: Iterable[T], k: int, key: Callable[[T], object], salt: str) -> list[T]:
    """First k items of `pool` (minus those whose key is already in `taken`), in salted-hash order."""
    if k <= 0:
        return []
    have = {key(x) for x in taken}
    return hash_order((x for x in pool if key(x) not in have), key, salt)[:k]
