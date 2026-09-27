import "server-only";

// A small per-visitor limit on the endpoints that call Jev (docs/07-ui.md, Deployment), so a shared link
// can't be used to spend the gateway's rate limit. Per function instance, which is enough to stop a runaway
// client; cached requests are free anyway.
const LIMITS: Record<string, { per: number; windowMs: number }> = {
  rerank: { per: 40, windowMs: 60_000 },
  walk: { per: 10, windowMs: 60_000 },
  ask: { per: 10, windowMs: 60_000 },
};
const hits = new Map<string, number[]>();

export function limited(req: Request, kind: keyof typeof LIMITS): Response | null {
  const { per, windowMs } = LIMITS[kind];
  const who = req.headers.get("x-forwarded-for")?.split(",")[0].trim() || "local";
  const key = `${kind}:${who}`;
  const now = Date.now();
  const recent = (hits.get(key) ?? []).filter((t) => now - t < windowMs);
  if (recent.length >= per) return Response.json({ error: "Too many requests; try again in a minute." }, { status: 429 });
  recent.push(now);
  hits.set(key, recent);
  if (hits.size > 5000) hits.clear();
  return null;
}
