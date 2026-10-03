import "server-only";
import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { REPO_ROOT } from "./env";

// Star layout files written by scripts/star_layout.py (docs/07-ui.md). Locally they're read from data/stars and
// reloaded when they change; in production (STARS_URL set) they're fetched from Vercel Blob, where
// scripts/sync_prod.py uploads them with each data sync. Each file loads on its own, the first time a route needs
// it: the index is 100 KB, but the dots are 12 MB and the ids 25 MB, and a cold function answering a topic or a
// dot's text shouldn't wait for files it never reads.
const DIR = path.join(REPO_ROOT, "data", "stars");
const REMOTE = process.env.STARS_URL?.replace(/\/$/, "");
// production: every sync uploads to a fresh folder, so the folder names the snapshot
const REMOTE_VERSION = REMOTE ? createHash("sha1").update(REMOTE).digest("hex").slice(0, 12) : "";

export interface StarIndex { nodes: [string, number, number][]; count: number }
export interface Stars { version: string; index: StarIndex; byNode: Map<string, [number, number]> }

/** The snapshot's version: the Blob folder in production, the layout file's mtime locally. */
export async function starVersion(): Promise<string> {
  return REMOTE ? REMOTE_VERSION : String(Math.round((await stat(path.join(DIR, "stars.bin"))).mtimeMs));
}

const memo = new Map<string, { v: string; p: Promise<unknown> }>();
function once<T>(name: string, v: string, load: () => Promise<T>): Promise<T> {
  const m = memo.get(name);
  if (m?.v === v) return m.p as Promise<T>;
  const p = load();
  memo.set(name, { v, p });
  p.catch(() => { if (memo.get(name)?.p === p) memo.delete(name); });
  return p;
}

async function raw(name: string): Promise<Buffer> {
  if (!REMOTE) return readFile(path.join(DIR, name));
  const r = await fetch(`${REMOTE}/${name}`);
  if (!r.ok) throw new Error(`stars: ${name} ${r.status}`);
  return Buffer.from(await r.arrayBuffer());
}

/** Which nodes own which stars: [node id, first star, count] in star order (stars are ordered by node, then id). */
export async function stars(): Promise<Stars> {
  const v = await starVersion();
  return once("index", v, async () => {
    const index = JSON.parse((await raw("nodes.json")).toString("utf8")) as StarIndex;
    return { version: v, index, byNode: new Map(index.nodes.map(([id, off, n]) => [id, [off, n] as [number, number]])) };
  });
}

/** The packed dots (12 bytes per star, see scripts/star_layout.py). */
export async function starBin(): Promise<Buffer> {
  return once("bin", await starVersion(), () => raw("stars.bin"));
}

/** Question ids in star order: 24-char ids, concatenated. */
export async function starIds(): Promise<string> {
  return once("ids", await starVersion(), async () => (await raw("ids.txt")).toString("latin1"));
}

/** Index of a question's dot in the snapshot, or -1. */
export function starOf(s: Stars, ids: string, nodeId: string, id: string): number {
  const r = s.byNode.get(nodeId);
  if (!r) return -1;
  const k = ids.slice(r[0] * 24, (r[0] + r[1]) * 24).indexOf(id);
  return k >= 0 && k % 24 === 0 ? r[0] + k / 24 : -1;
}

/** Production: the semantic layout precomputed into the snapshot (semantic.json), or null to compute it here. */
export async function remoteSemantic(): Promise<Record<string, [number, number, number]> | null> {
  if (!REMOTE) return null;
  const r = await fetch(`${REMOTE}/semantic.json`);
  return r.ok ? ((await r.json()) as Record<string, [number, number, number]>) : null;
}
