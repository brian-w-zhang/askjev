import { readFile } from "node:fs/promises";
import path from "node:path";
import { PORTRAIT_URL } from "@/components/portrait/data";

// Meme templates and the tweet screenshot: data/portrait/memes locally (gitignored, like the rest of the portrait's
// data), the portrait's Blob folder in production. Only plain file names with an image extension are served.
const DIR = path.join(process.cwd(), "..", "data", "portrait", "memes");
const TYPES: Record<string, string> = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };

export async function GET(_req: Request, ctx: RouteContext<"/portrait/memes/[file]">) {
  const { file } = await ctx.params;
  const type = TYPES[path.extname(file).toLowerCase()];
  if (!type || !/^[a-z0-9_-]+\.(png|jpe?g|webp)$/i.test(file)) return new Response("not found", { status: 404 });
  const headers = { "Content-Type": type, "Cache-Control": "public, max-age=86400, s-maxage=86400" };
  try {
    if (PORTRAIT_URL) {
      const r = await fetch(`${PORTRAIT_URL}/memes/${file}`);
      if (!r.ok) return new Response("not found", { status: 404 });
      return new Response(r.body, { headers });
    }
    return new Response(await readFile(path.join(DIR, file)), { headers });
  } catch {
    return new Response("not found", { status: 404 });
  }
}
