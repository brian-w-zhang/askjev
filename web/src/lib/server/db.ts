import "server-only";
import { Pool, types } from "pg";
import { DATABASE_URL } from "./env";

// real/float4 → number (pg returns strings for numeric by default; real is fine, bigint is not).
types.setTypeParser(20, (v) => Number(v));
types.setTypeParser(1700, (v) => Number(v));

const g = globalThis as unknown as { __askjevPool?: Pool };
export const pool: Pool =
  g.__askjevPool ?? (g.__askjevPool = new Pool({ connectionString: DATABASE_URL, max: 8 }));

export async function q<T = Record<string, unknown>>(sql: string, params: unknown[] = []): Promise<T[]> {
  const r = await pool.query(sql, params);
  return r.rows as T[];
}

export const toVector = (v: ArrayLike<number>) => "[" + Array.from(v, (x) => x.toFixed(6)).join(",") + "]";
