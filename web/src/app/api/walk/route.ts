import type { NextRequest } from "next/server";
import { askjev } from "@/lib/server/cli";

// GET /api/walk?q=...  Jev's own beam walk down the tree (`uv run askjev walk --json`).
export async function GET(req: NextRequest) {
  const text = (req.nextUrl.searchParams.get("q") ?? "").trim();
  if (!text) return Response.json({ error: "q is required" }, { status: 400 });
  try {
    return Response.json(await askjev(["walk", "--json", text]));
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 503 });
  }
}
