import type { NextRequest } from "next/server";
import { stars } from "@/lib/server/stars";

// GET /api/stars          {nodes: [[node_id, offset, count]...], count, version}
// GET /api/stars?bin=1    the packed star buffer (12 bytes per star, see scripts/star_layout.py)
export async function GET(req: NextRequest) {
  let s;
  try {
    s = await stars();
  } catch {
    return Response.json({ error: "no star layout: run `uv run python scripts/star_layout.py`" }, { status: 404 });
  }
  if (req.nextUrl.searchParams.get("bin"))
    return new Response(new Uint8Array(s.bin), { headers: { "content-type": "application/octet-stream", "cache-control": "no-cache" } });
  return Response.json({ ...s.index, version: s.mtime });
}
