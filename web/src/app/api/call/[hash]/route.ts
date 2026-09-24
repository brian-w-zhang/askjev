import { q } from "@/lib/server/db";

// GET /api/call/<request_hash>: the cached response (answers + usage) and where the full body lives.
export async function GET(_req: Request, ctx: RouteContext<"/api/call/[hash]">) {
  const { hash } = await ctx.params;
  const row = (await q(`select * from calls where request_hash = $1`, [hash]))[0];
  if (!row) return Response.json({ error: `no call ${hash}` }, { status: 404 });
  return new Response(JSON.stringify(row, null, 2), { headers: { "content-type": "application/json" } });
}
