import { loadPortrait } from "@/components/portrait/data";

// The atlas's heavy tables (topic cards, source table), fetched only when their tab opens. Cached at the edge like
// the map's API: the data changes only with a publish, which redeploys and clears it (the proxy still gates first
// when SITE_KEY is set).
export async function GET(req: Request) {
  const d = await loadPortrait();
  if (!d) return Response.json({ error: "no portrait data" }, { status: 404 });
  const part = new URL(req.url).searchParams.get("part");
  if (part === "nodes") return Response.json(d.nodes, { headers: { "Cache-Control": "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800" } });
  if (part === "sources") return Response.json(d.sources, { headers: { "Cache-Control": "public, max-age=0, s-maxage=86400, stale-while-revalidate=604800" } });
  return Response.json({ error: "part must be nodes or sources" }, { status: 400 });
}
