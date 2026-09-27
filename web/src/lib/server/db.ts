import "server-only";
import { Pool, types } from "pg";
import { DATABASE_URL } from "./env";

// real/float4 → number (pg returns strings for numeric by default; real is fine, bigint is not).
types.setTypeParser(20, (v) => Number(v));
types.setTypeParser(1700, (v) => Number(v));

// PlanetScale's URLs carry sslrootcert=system (libpq: use the OS trust store); node-postgres would read "system" as a
// file path. Dropping it keeps sslmode, and Node verifies against its own bundled roots, which cover PlanetScale's.
function connectionString(url: string) {
  if (!url.includes("sslrootcert=system")) return url;
  const u = new URL(url);
  u.searchParams.delete("sslrootcert");
  return u.toString();
}

const g = globalThis as unknown as { __askjevPool?: Pool };
// Connections stay open (idleTimeoutMillis: 0): a fresh connection costs ~20-30 ms, which would
// otherwise land on the first search after every idle pause.
export const pool: Pool =
  g.__askjevPool ?? (g.__askjevPool = new Pool({ connectionString: connectionString(DATABASE_URL), max: 8, idleTimeoutMillis: 0 }));

export async function q<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<T[]> {
  const r = await pool.query(sql, params);
  return r.rows as T[];
}

export const toVector = (v: ArrayLike<number>) => "[" + Array.from(v, (x) => x.toFixed(6)).join(",") + "]";

/** One query with a setting applied just for it (SET LOCAL inside a transaction; safe behind a pooler). */
export async function qWith<T = Record<string, unknown>>(setting: string, sql: string, params: unknown[] = []): Promise<T[]> {
  const c = await pool.connect();
  try {
    await c.query("begin");
    await c.query(setting);
    const r = await c.query(sql, params);
    await c.query("commit");
    return r.rows as T[];
  } catch (e) {
    await c.query("rollback").catch(() => {});
    throw e;
  } finally {
    c.release();
  }
}
