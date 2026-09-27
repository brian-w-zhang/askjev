import { readFile } from "node:fs/promises";
import path from "node:path";

// Meme templates and the tweet screenshot live in data/portrait/memes (gitignored, like the rest of the portrait's
// data), so they stay out of the public repo. Only plain file names with an image extension are served.
const DIR = path.join(process.cwd(), "..", "data", "portrait", "memes");
const TYPES: Record<string, string> = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp" };

export async function GET(_req: Request, ctx: RouteContext<"/portrait/memes/[file]">) {
  const { file } = await ctx.params;
  const type = TYPES[path.extname(file).toLowerCase()];
  if (!type || !/^[a-z0-9_-]+\.(png|jpe?g|webp)$/i.test(file)) return new Response("not found", { status: 404 });
  try {
    const body = await readFile(path.join(DIR, file));
    return new Response(body, { headers: { "Content-Type": type, "Cache-Control": "private, max-age=3600" } });
  } catch {
    return new Response("not found", { status: 404 });
  }
}
