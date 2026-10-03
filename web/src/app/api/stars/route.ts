import type { NextRequest } from "next/server";
import { starBin, starVersion, stars } from "@/lib/server/stars";

// GET /api/stars               {nodes: [[node_id, offset, count]...], count, version}
// GET /api/stars?bin=1&v=<v>   the packed star buffer (12 bytes per star, see scripts/star_layout.py). Asked for by
// the snapshot's version, it never changes, so browsers keep it: a return visit draws the map from disk, not 6 MB.
// like next.config.ts's other read-only routes: the edge keeps it until the next deploy, browsers revalidate
const EDGE = "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  try {
    if (sp.get("bin")) {
      const [buf, v] = await Promise.all([starBin(), starVersion()]);
      const cache = sp.get("v") === v ? "public, max-age=31536000, s-maxage=31536000, immutable" : EDGE;
      return new Response(new Uint8Array(buf), { headers: { "content-type": "application/octet-stream", "cache-control": cache } });
    }
    const s = await stars();
    return Response.json({ ...s.index, version: s.version }, { headers: { "cache-control": EDGE } });
  } catch {
    return Response.json({ error: "no star layout: run `uv run python scripts/star_layout.py`" }, { status: 404 });
  }
}
