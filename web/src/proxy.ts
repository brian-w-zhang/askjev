import { NextResponse, type NextRequest } from "next/server";

// Private by default (docs/08-roadmap.md; docs/07-ui.md, Deployment): when SITE_KEY is set (production), the site
// opens only for people with the shared link. `?key=<SITE_KEY>` once sets a cookie and drops the key from the
// URL; after that it just works. Without SITE_KEY (local dev) everything is open.
const COOKIE = "askjev_key";

export function proxy(req: NextRequest) {
  const key = process.env.SITE_KEY;
  if (!key) return NextResponse.next();
  const given = req.nextUrl.searchParams.get("key");
  if (given === key) {
    const clean = req.nextUrl.clone();
    clean.searchParams.delete("key");
    const res = NextResponse.redirect(clean);
    res.cookies.set(COOKIE, key, { httpOnly: true, secure: true, sameSite: "lax", maxAge: 60 * 60 * 24 * 180, path: "/" });
    return res;
  }
  if (req.cookies.get(COOKIE)?.value === key) return NextResponse.next();
  if (req.nextUrl.pathname.startsWith("/api/")) return NextResponse.json({ error: "private" }, { status: 401 });
  return new NextResponse(
    `<!doctype html><meta charset="utf-8"><title>askjev</title><meta name="viewport" content="width=device-width">` +
      `<body style="margin:0;height:100vh;display:grid;place-items:center;background:#dbf0ff;color:#1e1e1e;font:16px/1.4 system-ui">` +
      `<div style="box-shadow:0 0 0 1px #1e1e1e;background:#dedede;padding:0 3px 12px;max-width:360px">` +
      `<div style="background:#1e1e1e;color:#fefefe;padding:2px 8px;margin:0 -3px 12px;font-family:ui-monospace,monospace">askjev</div>` +
      `<p style="margin:0 12px">This site is private. Open it with the link you were sent.</p></div>`,
    { status: 401, headers: { "content-type": "text/html; charset=utf-8" } },
  );
}

export const config = {
  // everything except Next's own assets and the icons (so a shared link still shows its icon)
  matcher: ["/((?!_next/|favicon.ico|icon.svg|apple-icon.png).*)"],
};
