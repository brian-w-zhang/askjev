import { evaluate } from "@/lib/server/jev";
import { limited } from "@/lib/server/limit";

// POST /api/rerank {q, candidates: [{id, text}]} → ONE Jev request: a Choice over up to 20 candidates (c0..c19), and a
// Noul on whether any of them really asks what the query asks (a Choice always crowns a winner, so it can't say "none").
export async function POST(req: Request) {
  const slow = limited(req, "rerank");
  if (slow) return slow;
  const { q: query, candidates } = (await req.json()) as { q: string; candidates: { id: string; text: string }[] };
  const cands = (candidates ?? []).slice(0, 20);
  if (!query || cands.length < 2) return Response.json({ order: cands.map((c) => ({ id: c.id, p: null })), skipped: true });
  const criteria: Record<string, string> = {};
  cands.forEach((c, i) => (criteria[`c${i}`] = c.text));
  try {
    const { hash, cached, response, latencyMs } = await evaluate(
      { search_query: query, candidates: cands.map((c) => c.text) },
      {
        rerank: { type: "choice", instructions: "Which of these questions best matches the search query?", criteria },
        match: {
          type: "boolean", // the gateway's name for a Noul
          instructions: "Does at least one question in `candidates` ask essentially what `search_query` is asking about?",
          criteria: {
            true: "One of the candidates is about the same thing the query is looking for, even if worded differently.",
            false: "None of the candidates is about what the query asks; they only share words or are unrelated.",
          },
        },
      },
    );
    const probs = response.answers?.rerank?.probabilities ?? {};
    const order = cands
      .map((c, i) => ({ id: c.id, p: probs[`c${i}`] ?? 0 }))
      .sort((a, b) => b.p - a.p);
    const m = response.answers?.match as { probability?: number; noul?: number } | undefined;
    const match = m?.probability ?? m?.noul ?? null;
    return Response.json({ order, match, hash, cached, latency_ms: latencyMs, confidence: response.answers?.rerank?.confidence ?? null });
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 502 });
  }
}
