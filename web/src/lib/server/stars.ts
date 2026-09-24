import "server-only";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { REPO_ROOT } from "./env";

// Star layout files written by scripts/star_layout.py (docs/07-ui.md). Reloaded when the files change.
const DIR = path.join(REPO_ROOT, "data", "stars");

export interface StarIndex { nodes: [string, number, number][]; count: number }

let cache: { mtime: number; index: StarIndex; bin: Buffer; ids: string; byNode: Map<string, [number, number]> } | null = null;

export async function stars() {
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
