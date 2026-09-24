import "server-only";
import path from "node:path";
import { config } from "dotenv";

// Secrets live in the repo-root .env (one level above web/). Loaded server-side only.
export const REPO_ROOT = path.resolve(process.cwd(), "..");
config({ path: path.join(REPO_ROOT, ".env"), quiet: true });

export const DATABASE_URL = process.env.DATABASE_URL ?? "postgresql://localhost:5432/askjev";
export function gatewayKey(): string {
  const k = process.env.AI_GATEWAY_API_KEY;
  if (!k) throw new Error("AI_GATEWAY_API_KEY missing from ../.env");
  return k;
}
