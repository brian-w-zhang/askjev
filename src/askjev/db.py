from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .config import DATABASE_URL

__all__ = ["connect", "cursor", "Jsonb"]


def connect(autocommit: bool = False) -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL, autocommit=autocommit, row_factory=dict_row)


@contextmanager
def cursor():
    with connect() as conn:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
