import type { NextRequest } from "next/server";
import { balloon } from "@/lib/layouts/balloon";
import { forceInput, forceRelax } from "@/lib/layouts/force";
import { simulate } from "@/lib/layouts/forceSim";
import { treeKey, type LayoutInput } from "@/lib/layouts/common";
import type { TreeNode } from "@/lib/types";
import { stars } from "@/lib/server/stars";
import { subtreeRows } from "@/lib/server/tree";

// GET /api/layout/web?key=<tree key>   {P: final positions}: the Web layout's simulation and overlap pass, run here once instead
// of in every first visitor's browser (seconds on a phone). It lays out exactly what the map loads (the whole tree,
// the snapshot's question counts) and answers 409 if the browser's tree key differs, so the browser simulates itself.
// The edge keeps each key until the next deploy; a data sync that changes the tree changes the key.
const memo = new Map<string, Promise<number[]>>();

async function settle(): Promise<{ key: string; P: Promise<number[]> }> {
  // the same rows the map gets from /api/tree?root=root&depth=12, merged the way the store merges them
  const rows = JSON.parse(JSON.stringify(await subtreeRows("root", 12))) as TreeNode[];
  const nodes: Record<string, TreeNode> = {};
  for (const r of rows) nodes[r.id] = r;
  const base = nodes.root?.depth ?? 0;
  const byParent: Record<string, TreeNode[]> = {};
  for (const r of rows) if (r.parent_id) (byParent[r.parent_id] ??= []).push(r);
  const children: Record<string, string[]> = {};
  for (const r of rows) {
    if (r.depth >= base + 12) continue;
    children[r.id] = (byParent[r.id] ?? []).sort((a, b) => (a.ord ?? 999) - (b.ord ?? 999) || a.id.localeCompare(b.id)).map((n) => n.id);
  }
  const s = await stars();
  const direct = new Map(s.index.nodes.map(([id, , n]) => [id, n]));
  const inp: LayoutInput = { nodes, children, direct, rootId: "root", semantic: null };
  const key = treeKey(inp);
  let P = memo.get(key);
  if (!P) {
    P = Promise.resolve().then(() => {
      const { sim } = forceInput(inp, balloon(inp));
      return forceRelax(sim, simulate(sim)).map((v) => Math.round(v * 100) / 100);
    });
    memo.clear();
    memo.set(key, P);
  }
  return { key, P };
}

export async function GET(req: NextRequest) {
  try {
    const { key, P } = await settle();
    if (req.nextUrl.searchParams.get("key") !== key) return Response.json({ key }, { status: 409, headers: { "cache-control": "no-store" } });
    return Response.json({ P: await P }, { headers: { "cache-control": "public, max-age=0, s-maxage=31536000" } });
  } catch (e) {
    return Response.json({ error: String(e) }, { status: 500, headers: { "cache-control": "no-store" } });
  }
}
