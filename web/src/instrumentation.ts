// Warm the embedding model, the Postgres pool and the search index at server start, so the first search is as
// fast as the rest (model load is ~0.7 s cold; a cold index read is ~0.5 s). Not on Vercel, where every route is
// its own function: a tree or node request's cold start shouldn't load the model (only search's bundle has it).
export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs" || process.env.VERCEL) return;
  const [{ embed }, { q, toVector }, { nearest }] = await Promise.all([
    import("./lib/server/embed"),
    import("./lib/server/db"),
    import("./lib/server/search"),
  ]);
  try {
    const v = toVector(await embed("warm up"));
    // the same queries a search runs, in parallel (questions, nodes)
    await Promise.all([
      nearest(v, false),
      q("select id from nodes where embedding is not null order by embedding <=> $1::vector limit 1", [v]),
    ]);
  } catch (e) {
    console.warn("askjev warmup failed:", (e as Error).message);
  }
}
