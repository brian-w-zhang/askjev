import "server-only";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";
import { PORTRAIT_URL } from "../portrait/data";
import type { ExperimentsData } from "./types";

// The experiments are private like the portrait: locally scripts/experiments/export.py writes
// data/analysis/experiments.json (gitignored) and it's read from disk; in production publish.py puts it in the
// portrait's unguessable Blob folder, fetched here on the server only.
const FILE = path.join(process.cwd(), "..", "data", "analysis", "experiments.json");

let cached: { key: string; data: ExperimentsData } | null = null;
let pending: Promise<ExperimentsData | null> | null = null;

export async function loadExperiments(): Promise<ExperimentsData | null> {
  if (PORTRAIT_URL) {
    if (cached?.key === PORTRAIT_URL) return cached.data;
    pending ??= fetch(`${PORTRAIT_URL}/experiments.json`, { cache: "no-store" })
      .then((r) => (r.ok ? (r.json() as Promise<ExperimentsData>) : null))
      .then((data) => { if (data) cached = { key: PORTRAIT_URL, data }; return data; })
      .catch(() => null)
      .finally(() => { pending = null; });
    return pending;
  }
  try {
    const mtime = String(statSync(FILE).mtimeMs);
    if (cached?.key !== mtime) cached = { key: mtime, data: JSON.parse(readFileSync(FILE, "utf-8")) as ExperimentsData };
    return cached.data;
  } catch {
    return null;
  }
}
