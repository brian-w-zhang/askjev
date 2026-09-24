import { evaluate } from "@/lib/server/jev";

// POST /api/rerank {q, candidates: [{id, text}]} → ONE Jev Choice over up to 20 candidates (c0..c19).
export async function POST(req: Request) {
  const { q: query, candidates } = (await req.json()) as { q: string; candidates: { id: string; text: string }[] };
  const cands = (candidates ?? []).slice(0, 20);
  if (!query || cands.length < 2) return Response.json({ order: cands.map((c) => ({ id: c.id, p: null })), skipped: true });
  const criteria: Record<string, string> = {};
  cands.forEach((c, i) => (criteria[`c${i}`] = c.text));
  try {
    const { hash, cached, response, latencyMs } = await evaluate(
      { search_query: query },
      { rerank: { type: "choice", instructions: "Which of these questions best matches the search query?", criteria } },
    );
    const probs = response.answers?.rerank?.probabilities ?? {};
    const order = cands
      .map((c, i) => ({ id: c.id, p: probs[`c${i}`] ?? 0 }))
      .sort((a, b) => b.p - a.p);
    return Response.json({ order, hash, cached, latency_ms: latencyMs, confidence: response.answers?.rerank?.confidence ?? null });
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 502 });
  }
}
