import type { NextRequest } from "next/server";
import { q } from "@/lib/server/db";
import { stars } from "@/lib/server/stars";

// GET /api/stars/text?node=<id>   [{id, text, label, primitive}] for the node's stars, in star order.
// `label` is what the star shows in the sky: the text, unless several stars in the node share it (a
// template run over many inputs, "Which would you rather?"), then the part that differs: the input or the options.
export async function GET(req: NextRequest) {
  const node = req.nextUrl.searchParams.get("node") ?? "";
  const s = await stars();
  const r = s.byNode.get(node);
  if (!r) return Response.json({ questions: [] });
  const [off, n] = r;
  const ids: string[] = [];
  for (let i = off; i < off + n; i++) ids.push(s.ids.slice(i * 24, i * 24 + 24));
  const rows = await q<{ id: string; text: string; primitive: string; state: unknown; options: unknown }>(
    `select id, text, primitive, state, options from questions where id = any($1)`,
    [ids],
  );
  const shared = new Map<string, number>();
  for (const x of rows) shared.set(x.text, (shared.get(x.text) ?? 0) + 1);
  const m = new Map(rows.map((x) => [x.id, { id: x.id, text: x.text, primitive: x.primitive, label: (shared.get(x.text) ?? 0) > 1 ? distinct(x) ?? x.text : x.text }]));
  return Response.json({ questions: ids.map((id) => m.get(id) ?? { id, text: "", label: "", primitive: "" }) });
}

function distinct(x: { state: unknown; options: unknown }): string | null {
  if (x.state && typeof x.state === "object") {
    const v = Object.values(x.state as Record<string, unknown>).find((y) => typeof y === "string" && y.trim());
    if (typeof v === "string") return `“${v.trim().replace(/\s+/g, " ")}”`;
  }
  if (x.options && typeof x.options === "object" && !Array.isArray(x.options)) {
    const o = Object.entries(x.options as Record<string, unknown>).map(([k, d]) => (typeof d === "string" && d ? d : k));
    if (o.length) return o.slice(0, 3).join("  or  ");
  }
  return null;
}
