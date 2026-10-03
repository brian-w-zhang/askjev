import type { NextRequest } from "next/server";
import { q } from "@/lib/server/db";
import { starIds, stars } from "@/lib/server/stars";

// GET /api/stars/text?node=<id>        [{id, text, label, primitive}] for the node's stars, in star order.
// GET /api/stars/text?node=<id>&at=<k>  {id} of the node's k-th star alone, so a tapped dot's card can open before
//                                       the node's texts (up to 300 KB on the biggest topics) arrive.
// `label` is what the star shows in the sky: the text, unless several stars in the node share it (a
// template run over many inputs, "Which would you rather?"), then the part that differs: the input or the options.
export async function GET(req: NextRequest) {
  const node = req.nextUrl.searchParams.get("node") ?? "";
  const s = await stars();
  const r = s.byNode.get(node);
  if (!r) return Response.json({ questions: [] });
  const [off, n] = r;
  const at = req.nextUrl.searchParams.get("at");
  if (at !== null) {
    const k = Number(at);
    if (!Number.isInteger(k) || k < 0 || k >= n) return Response.json({ error: "no such star" }, { status: 404 });
    const one = await q<{ id: string; n: number }>(
      `select id, count(*) over ()::int as n from questions where node_id = $1 and display_ok order by id collate "C" offset $2 limit 1`,
      [node, k],
    );
    if (one[0]?.n === n) return Response.json({ id: one[0].id });
    return Response.json({ id: (await starIds()).slice((off + k) * 24, (off + k + 1) * 24) });
  }
  type Row = { id: string; text: string; primitive: string; state: unknown; options: unknown };
  // stars are ordered by (node, id), so the node's shown questions in id order are its stars, without reading the
  // 25 MB id list; only when the database has moved on from the snapshot (locally, mid-pipeline) is the list needed
  let rows = await q<Row>(
    `select id, text, primitive, state, options from questions where node_id = $1 and display_ok order by id collate "C"`,
    [node],
  );
  let ids = rows.map((x) => x.id);
  if (rows.length !== n) {
    const all = await starIds();
    ids = [];
    for (let i = off; i < off + n; i++) ids.push(all.slice(i * 24, i * 24 + 24));
    rows = await q<Row>(`select id, text, primitive, state, options from questions where id = any($1)`, [ids]);
  }
  const shared = new Map<string, number>();
  for (const x of rows) shared.set(x.text, (shared.get(x.text) ?? 0) + 1);
  // previews only (hover cards, sky labels): the card fetches the full question, and some topics hold thousands of
  // long scenario texts (a Moral Machine topic was 8 MB untrimmed)
  const cut = (t: string, n: number) => (t.length > n ? t.slice(0, n - 1).trimEnd() + "…" : t);
  // `label` is sent only when it differs from the text (the client fills it in), which halves the payload
  const m = new Map(rows.map((x) => {
    const label = (shared.get(x.text) ?? 0) > 1 ? distinct(x) : null;
    return [x.id, { id: x.id, text: cut(x.text, 220), primitive: x.primitive, ...(label ? { label: cut(label, 140) } : {}) }];
  }));
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
