import { askjev } from "@/lib/server/cli";

const PRIMITIVES = new Set(["noul", "choice", "score"]);

// POST /api/ask {text, primitive, options, state} → `uv run askjev ask --json '<payload>'`.
export async function POST(req: Request) {
  const body = (await req.json()) as { text?: string; primitive?: string; options?: unknown; state?: unknown };
  const text = (body.text ?? "").trim();
  if (!text) return Response.json({ error: "Write a question first." }, { status: 400 });
  if (!PRIMITIVES.has(body.primitive ?? "")) return Response.json({ error: "Pick Noul, Choice or Score." }, { status: 400 });
  const payload = { text, primitive: body.primitive, options: body.options ?? null, state: body.state ?? null };
  try {
    return Response.json(await askjev(["ask", "--json", JSON.stringify(payload)], 180_000));
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 503 });
  }
}
