import { askjev } from "@/lib/server/cli";
import { evaluate } from "@/lib/server/jev";
import { limited } from "@/lib/server/limit";

const PRIMITIVES = new Set(["noul", "choice", "score"]);
const GATEWAY: Record<string, string> = { noul: "boolean", choice: "choice", score: "score" };
// same framing as the pipeline's answer probes (src/askjev/answer.py)
const NEUTRAL_STATE = { context: "Independent standalone questions. Answer each one on its own." };
const HUMAN = "Do not give your own view. Choose the answer that most people would give (the most common human answer).";

// Where the full flow can't run (production has no Python and visitors shouldn't write into the corpus),
// the ask box is answer-only (docs/07-ui.md, Ask box): one Jev request, Jev's own answer and what it thinks most
// people would say, nothing stored but the cached call. Locally it's the full flow (dedupe, place, answer, measure).
const ANSWER_ONLY = !!process.env.VERCEL || process.env.ASK_MODE === "answer";

// POST /api/ask {text, primitive, options, state}
export async function POST(req: Request) {
  const body = (await req.json()) as { text?: string; primitive?: string; options?: unknown; state?: unknown };
  const text = (body.text ?? "").trim();
  if (!text) return Response.json({ error: "Write a question first." }, { status: 400 });
  if (!PRIMITIVES.has(body.primitive ?? "")) return Response.json({ error: "Pick Noul, Choice or Score." }, { status: 400 });
  const slow = limited(req, "ask");
  if (slow) return slow;
  const prim = body.primitive!;
  const options = body.options ?? null;
  if (ANSWER_ONLY) {
    const gq = (instructions: unknown) => (options ? { type: GATEWAY[prim], instructions, criteria: options } : { type: GATEWAY[prim], instructions });
    try {
      const { response } = await evaluate(NEUTRAL_STATE, { self: gq(text), human: gq({ question: text, perspective: HUMAN }) } as never);
      const dist = (k: string) => {
        const a = response.answers?.[k];
        if (!a) return null;
        return a.type === "boolean" ? { true: a.probability ?? 0, false: 1 - (a.probability ?? 0) } : a.probabilities ?? null;
      };
      return Response.json({ answer_only: true, text, primitive: prim, options, answers: { self: dist("self"), human: dist("human") } });
    } catch (e) {
      return Response.json({ error: (e as Error).message }, { status: 503 });
    }
  }
  const payload = { text, primitive: prim, options, state: body.state ?? null };
  try {
    return Response.json(await askjev(["ask", "--json", JSON.stringify(payload)], 180_000));
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 503 });
  }
}
