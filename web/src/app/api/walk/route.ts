import type { NextRequest } from "next/server";
import { walk } from "@/lib/server/walk";
import { limited } from "@/lib/server/limit";

// GET /api/walk?q=...  Jev's own beam walk down the tree (lib/server/walk.ts).
export async function GET(req: NextRequest) {
  const text = (req.nextUrl.searchParams.get("q") ?? "").trim();
  if (!text) return Response.json({ error: "q is required" }, { status: 400 });
  const slow = limited(req, "walk");
  if (slow) return slow;
  try {
    return Response.json(await walk(text));
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 503 });
  }
}
