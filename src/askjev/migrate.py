"""Apply db/migrations/*.sql in order (idempotent; tracked in schema_migrations)."""

from . import db
from .config import ROOT


def migrate():
    files = sorted((ROOT / "db" / "migrations").glob("*.sql"))
    with db.connect(autocommit=True) as conn:
        conn.execute("create table if not exists schema_migrations (name text primary key, applied_at timestamptz default now())")
        done = {r["name"] for r in conn.execute("select name from schema_migrations")}
        for f in files:
            if f.name in done:
                continue
            conn.execute(f.read_text())
            conn.execute("insert into schema_migrations (name) values (%s)", (f.name,))
            print("applied", f.name)
