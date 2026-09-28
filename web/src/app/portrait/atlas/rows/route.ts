import { readFile } from "node:fs/promises";
import path from "node:path";
import { q } from "@/lib/server/db";
import { PORTRAIT_URL } from "@/components/portrait/data";
import type { Row } from "@/components/portrait/types";

// Every question behind an experiment, a page at a time (docs/17 item 6). The ordered id list is private, written by
// scripts/experiments/export.py (data/analysis/experiment_rows/<id>.json, or the same file in the Blob folder in
// production); the questions and Jev's answers come from the database.
const PAGE = 5;
const lists = new Map<string, [string, string][]>();

async function list(id: string): Promise<[string, string][] | null> {
  if (!/^[a-z0-9_]+$/.test(id)) return null;
  const hit = lists.get(id);
  if (hit) return hit;
  let data: [string, string][] | null = null;
  try {
    if (PORTRAIT_URL) {
      const r = await fetch(`${PORTRAIT_URL}/experiment_rows/${id}.json`, { cache: "no-store" });
      data = r.ok ? await r.json() : null;
    } else {
      data = JSON.parse(await readFile(path.join(process.cwd(), "..", "data", "analysis", "experiment_rows", `${id}.json`), "utf-8"));
    }
  } catch {
    data = null;
  }
  if (data) lists.set(id, data);
  return data;
}

type Dist = Record<string, number>;
const norm = (d: Dist | null) => {
  if (!d) return null;
  const t = Object.values(d).reduce((a, b) => a + b, 0) || 1;
  return Object.fromEntries(Object.entries(d).map(([k, v]) => [k, v / t]));
};

export async function GET(req: Request) {
  const u = new URL(req.url);
  const id = u.searchParams.get("id") ?? "";
  const page = Math.max(0, Number(u.searchParams.get("page") ?? 0) || 0);
  const filter = u.searchParams.get("filter") ?? "";
  const all = await list(id);
  if (!all) return Response.json({ error: "no such experiment" }, { status: 404 });
  const pool = filter === "wrong" || filter === "differs" ? all.filter(([, f]) => f === filter) : all;
  const slice = pool.slice(page * PAGE, page * PAGE + PAGE);
  const ids = slice.map(([i]) => i);
  const [qs, ans, hum] = await Promise.all([
    q<{ id: string; text: string; state: unknown; options: unknown; primitive: Row["primitive"]; node_id: string; source: string; hemisphere: Row["hemisphere"]; truth: unknown }>(
      `select id, text, state, options, primitive, node_id, source, hemisphere, truth from questions where id = any($1)`, [ids]),
    q<{ question_id: string; frame: string; distribution: Dist }>(
      `select p.question_id, p.frame, a.distribution from probes p join answers a on a.probe_id = p.id
        where p.question_id = any($1) and p.universe_id = 'base' and p.variant_kind = 'base'`, [ids]),
    q<{ question_id: string; population: string | null; n: number | null; distribution: Dist }>(
      `select distinct on (question_id) question_id, population, n, distribution from human_dists
        where question_id = any($1) order by question_id, n desc nulls last`, [ids]),
  ]);
  const byQ = new Map(qs.map((x) => [x.id, x]));
  const rows: (Row & { flag: string })[] = [];
  for (const [qid, flag] of slice) {
    const x = byQ.get(qid);
    if (!x) continue;
    const self = ans.find((a) => a.question_id === qid && (a.frame === "self" || a.frame === "none"))?.distribution ?? null;
    const people = ans.find((a) => a.question_id === qid && a.frame === "human")?.distribution ?? null;
    const h = hum.find((a) => a.question_id === qid);
    const opts = x.options as Record<string, string | null> | string[] | null;
    const labels = opts && !Array.isArray(opts) ? Object.fromEntries(Object.entries(opts).filter(([, v]) => v).map(([k, v]) => [k, String(v)])) : undefined;
    const jev = norm(self);
    const top = jev ? Object.entries(jev).sort((a, b) => b[1] - a[1])[0] : null;
    rows.push({
      id: qid, text: x.text, state: x.state ? (typeof x.state === "string" ? x.state : JSON.stringify(x.state)).slice(0, 600) : null,
      options: Array.isArray(opts) ? opts : Object.keys(opts ?? {}), labels, primitive: x.primitive, node: x.node_id, source: x.source,
      hemisphere: x.hemisphere, jev, people: norm(people), human: h ? { dist: norm(h.distribution) as Dist, n: h.n, population: h.population } : null,
      truth: (x.truth ?? null) as Row["truth"], correct: null, top: top?.[0] ?? "", p_top: top?.[1] ?? 0, flag,
    });
  }
  return Response.json({ rows, total: pool.length, page, pages: Math.ceil(pool.length / PAGE) },
    { headers: { "Cache-Control": "private, max-age=600" } });
}
