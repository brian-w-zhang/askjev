// Warm the local embedding model and the Postgres pool at server start, so the first search
// is as fast as the rest (model load is ~0.7 s cold).
export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  const [{ embed }, { q, toVector }] = await Promise.all([import("./lib/server/embed"), import("./lib/server/db")]);
  try {
    const v = await embed("warm up");
    // Open as many connections as one search uses in parallel (vector, trigram, nodes).
    await Promise.all([
      q("select id from questions where embedding is not null order by embedding <=> $1::vector limit 1", [toVector(v)]),
      q("select id from questions where text % 'warm up' limit 1"),
      q("select id from nodes where embedding is not null order by embedding <=> $1::vector limit 1", [toVector(v)]),
    ]);
  } catch (e) {
    console.warn("askjev warmup failed:", (e as Error).message);
  }
}
