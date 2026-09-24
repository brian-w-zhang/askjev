import "server-only";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { q } from "./db";
import { gatewayKey, REPO_ROOT } from "./env";

// Jev over Vercel AI Gateway. typesafe-ai/jev is the ONLY gateway model this app may call.
export const JEV_MODEL = "typesafe-ai/jev";
const GATEWAY_URL = "https://ai-gateway.vercel.sh/v1/evaluate";

type Json = null | boolean | number | string | Json[] | { [k: string]: Json };

/** Sorted-key compact JSON, byte-compatible with orjson OPT_SORT_KEYS for our request bodies. */
export function canonical(v: Json): string {
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  if (v && typeof v === "object")
    return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}";
  return JSON.stringify(v);
}

/** Same hash as the Python client (askjev.jev.Request): sha256 of {"body", "repeat"}. */
export function requestHash(body: Json): string {
  return crypto.createHash("sha256").update(canonical({ body, repeat: 0 })).digest("hex");
}

export interface JevResponse {
  model?: string;
  answers: Record<string, { type: string; choice?: string; probability?: number; probabilities?: Record<string, number>; confidence?: number }>;
  usage?: { inputTokens?: number; outputTokens?: number };
  providerMetadata?: { gateway?: { generationId?: string } };
}

function logLine(rec: object): string {
  const day = new Date().toISOString().slice(0, 10);
  const dir = path.join(REPO_ROOT, "data", "calls", day);
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `web-${process.pid}.jsonl`);
  const fd = fs.openSync(file, "a");
  try {
    fs.writeSync(fd, JSON.stringify(rec) + "\n");
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
  return path.relative(REPO_ROOT, file);
}

/**
 * Send one request, or return the cached response if its hash is already in `calls`.
 * Identical requests are never re-sent (CLAUDE.md).
 */
export async function evaluate(state: Json, questions: Record<string, Json>): Promise<{ hash: string; cached: boolean; response: JevResponse; latencyMs: number }> {
  const body = { model: JEV_MODEL, state, questions } as Json;
  const hash = requestHash(body);
  const hit = await q<{ response: JevResponse; latency_ms: number }>(
    "select response, latency_ms from calls where request_hash = $1 and response is not null",
    [hash],
  );
  if (hit.length) return { hash, cached: true, response: hit[0].response, latencyMs: 0 };

  const t0 = Date.now();
  const r = await fetch(GATEWAY_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${gatewayKey()}`, "Content-Type": "application/json" },
    body: canonical(body),
  });
  const latencyMs = Date.now() - t0;
  if (!r.ok) throw new Error(`jev ${r.status}: ${(await r.text()).slice(0, 300)}`);
  const resp = (await r.json()) as JevResponse;
  const logFile = logLine({ hash, repeat: 0, t: Date.now() / 1000, latency_ms: latencyMs, request: body, response: resp });
  const slim = { model: resp.model, answers: resp.answers, usage: resp.usage };
  const served = `${resp.model ?? JEV_MODEL}@${new Date().toISOString().slice(0, 10)}`;
  await q(
    `insert into calls (request_hash, kind, model_served, generation_id, log_file, latency_ms, input_tokens, response)
     values ($1,'jev',$2,$3,$4,$5,$6,$7) on conflict (request_hash) do nothing`,
    [hash, served, resp.providerMetadata?.gateway?.generationId ?? null, logFile, latencyMs, resp.usage?.inputTokens ?? null, JSON.stringify(slim)],
  );
  return { hash, cached: false, response: resp, latencyMs };
}
