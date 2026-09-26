import { semanticCoords } from "@/lib/server/semantic";

// GET /api/layout   {coords: {node_id: [x, y, z]}}: node positions for the semantic layout (unit scale)
export async function GET() {
  try {
    return Response.json({ coords: await semanticCoords() });
  } catch (e) {
    return Response.json({ error: String(e) }, { status: 500 });
  }
}
