import "server-only";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { REPO_ROOT } from "./env";

// Star layout files written by scripts/star_layout.py (docs/07-ui.md). Locally they're read from data/stars and
// reloaded when they change; in production (STARS_URL set) they're fetched once from Vercel Blob, where
// scripts/sync_prod.sh uploads them with each data sync.
const DIR = path.join(REPO_ROOT, "data", "stars");
const REMOTE = process.env.STARS_URL?.replace(/\/$/, "");

export interface StarIndex { nodes: [string, number, number][]; count: number }

interface Snapshot { mtime: number; index: StarIndex; bin: Buffer; ids: string; byNode: Map<string, [number, number]> }
let cache: Snapshot | null = null;
let loading: Promise<Snapshot> | null = null;

async function fromRemote(): Promise<Snapshot> {
  const get = async (f: string) => {
    const r = await fetch(`${REMOTE}/${f}`);
    if (!r.ok) throw new Error(`stars: ${f} ${r.status}`);
    return r;
  };
  const [index, bin, ids] = await Promise.all([
    get("nodes.json").then((r) => r.json() as Promise<StarIndex & { version?: number }>),
    get("stars.bin").then(async (r) => Buffer.from(await r.arrayBuffer())),
    get("ids.txt").then((r) => r.text()),
  ]);
  const byNode = new Map(index.nodes.map(([id, off, n]) => [id, [off, n] as [number, number]]));
  return { mtime: index.version ?? 0, index, bin, ids, byNode };
}

export async function stars(): Promise<Snapshot> {
  if (REMOTE) {
    if (cache) return cache; // a sync redeploys, which starts fresh instances
    loading ??= fromRemote()
      .then((c) => (cache = c))
      .finally(() => { loading = null; });
    return loading;
  }
  const mtime = (await stat(path.join(DIR, "stars.bin"))).mtimeMs;
  if (cache?.mtime === mtime) return cache;
  const [index, bin, ids] = await Promise.all([
    readFile(path.join(DIR, "nodes.json"), "utf8").then((s) => JSON.parse(s) as StarIndex),
    readFile(path.join(DIR, "stars.bin")),
    readFile(path.join(DIR, "ids.txt"), "utf8"),
  ]);
  const byNode = new Map(index.nodes.map(([id, off, n]) => [id, [off, n] as [number, number]]));
  cache = { mtime, index, bin, ids, byNode };
  return cache;
}

/** Index of a question's dot in the snapshot, or -1 (ids.txt holds 24-char ids in star order). */
export function starOf(s: Snapshot, nodeId: string, id: string): number {
  const r = s.byNode.get(nodeId);
  if (!r) return -1;
  const k = s.ids.slice(r[0] * 24, (r[0] + r[1]) * 24).indexOf(id);
  return k >= 0 && k % 24 === 0 ? r[0] + k / 24 : -1;
}

/** Production: the semantic layout precomputed into the snapshot (semantic.json), or null to compute it here. */
export async function remoteSemantic(): Promise<Record<string, [number, number, number]> | null> {
  if (!REMOTE) return null;
  const r = await fetch(`${REMOTE}/semantic.json`);
  return r.ok ? ((await r.json()) as Record<string, [number, number, number]>) : null;
}
