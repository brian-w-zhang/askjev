import "server-only";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";
import type { PortraitData } from "./types";

// The portrait's data is private. Locally, scripts/portrait/export_page.py writes it to data/analysis (gitignored)
// and it's read from disk, re-read when the export rewrites it. In production, scripts/portrait/publish.py puts it
// in an unguessable Blob folder and sets PORTRAIT_URL; it's fetched here on the server, never by the browser, and
// the pages stay behind the site key. The memes live in the same folder (app/portrait/memes).
const FILE = path.join(process.cwd(), "..", "data", "analysis", "portrait.json");
export const PORTRAIT_URL = process.env.PORTRAIT_URL?.replace(/\/$/, "") || null;

let cached: { key: string; data: PortraitData } | null = null;
let pending: Promise<PortraitData | null> | null = null;

export async function loadPortrait(): Promise<PortraitData | null> {
  if (PORTRAIT_URL) {
    if (cached?.key === PORTRAIT_URL) return cached.data;
    pending ??= fetch(`${PORTRAIT_URL}/portrait.json`, { cache: "no-store" })
      .then((r) => (r.ok ? (r.json() as Promise<PortraitData>) : null))
      .then((data) => { if (data) cached = { key: PORTRAIT_URL, data }; return data; })
      .catch(() => null)
      .finally(() => { pending = null; });
    return pending;
  }
  try {
    const mtime = String(statSync(FILE).mtimeMs);
    if (cached?.key !== mtime) cached = { key: mtime, data: JSON.parse(readFileSync(FILE, "utf-8")) as PortraitData };
    return cached.data;
  } catch {
    return null;
  }
}
