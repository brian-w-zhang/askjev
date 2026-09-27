import "server-only";
import { readFileSync, statSync } from "node:fs";
import path from "node:path";
import type { PortraitData } from "./types";

// The portrait's data is private: scripts/portrait/export_page.py writes it to data/analysis (gitignored), and it is
// read here on the server, never shipped from web/public. Re-read only when the export rewrites it.
const FILE = path.join(process.cwd(), "..", "data", "analysis", "portrait.json");

let cached: { mtime: number; data: PortraitData } | null = null;

export function loadPortrait(): PortraitData | null {
  try {
    const mtime = statSync(FILE).mtimeMs;
    if (cached?.mtime !== mtime) cached = { mtime, data: JSON.parse(readFileSync(FILE, "utf-8")) as PortraitData };
    return cached.data;
  } catch {
    return null;
  }
}
