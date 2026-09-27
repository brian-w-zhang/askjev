import { loadPortrait } from "@/components/portrait/data";

// The atlas's heavy tables (topic cards, source table), fetched only when their tab opens.
export async function GET(req: Request) {
  const d = await loadPortrait();
  if (!d) return Response.json({ error: "no portrait data" }, { status: 404 });
  const part = new URL(req.url).searchParams.get("part");
  if (part === "nodes") return Response.json(d.nodes, { headers: { "Cache-Control": "private, max-age=600" } });
  if (part === "sources") return Response.json(d.sources, { headers: { "Cache-Control": "private, max-age=600" } });
  return Response.json({ error: "part must be nodes or sources" }, { status: 400 });
}
