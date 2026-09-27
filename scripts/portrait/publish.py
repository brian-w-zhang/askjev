"""Publish the portrait's private data to production (docs/11-portrait.md §7).

Uploads data/analysis/portrait.json and the meme images into a fresh, unguessable Vercel Blob folder and sets the
site's PORTRAIT_URL to it. The site fetches both on the server (components/portrait/data.ts,
app/portrait/memes/[file]/route.ts), so the folder's address never reaches a browser, and the pages stay behind the
site key. Nothing is committed to the public repo. Needs BLOB_READ_WRITE_TOKEN (from .env) and the Vercel CLI.

  uv run python scripts/portrait/publish.py            # upload and set PORTRAIT_URL
  uv run python scripts/portrait/publish.py --deploy   # ... and redeploy production
"""

from __future__ import annotations

import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sync_prod import env  # noqa: E402  (reads .env without printing it)

ROOT = Path(__file__).resolve().parent.parent.parent
FILES = [ROOT / "data" / "analysis" / "portrait.json"] + sorted((ROOT / "data" / "portrait" / "memes").glob("*.webp"))


def main() -> None:
    token = env("BLOB_READ_WRITE_TOKEN")
    if not token:
        raise SystemExit("no BLOB_READ_WRITE_TOKEN")
    # the read-write token only: an OIDC token left by `vercel env pull` makes the CLI demand a store id too
    blob_env = {k: v for k, v in os.environ.items() if k not in ("VERCEL_OIDC_TOKEN", "BLOB_STORE_ID")}
    blob_env["BLOB_READ_WRITE_TOKEN"] = token
    folder = "portrait-" + secrets.token_urlsafe(12)
    base = None
    for p in FILES:
        name = p.name if p.suffix == ".json" else f"memes/{p.name}"
        out = subprocess.run(["vercel", "blob", "put", str(p), "--pathname", f"{folder}/{name}", "--access", "public"],
                             capture_output=True, text=True, env=blob_env)
        if out.returncode:
            raise SystemExit(f"upload of {p.name} failed: " + re.sub(r"vercel_blob_rw_\w+", "[redacted]", out.stderr.strip()[-400:]))
        m = re.search(r"https://\S+", out.stdout + out.stderr)
        if m and p.suffix == ".json":
            base = m.group(0).rsplit("/", 1)[0]
        print("uploaded", name)
    if not base:
        raise SystemExit("no URL for portrait.json")
    # print only the host, not the unguessable folder
    print("PORTRAIT_URL set to a new folder on", base.split("/")[2])
    subprocess.run(["vercel", "env", "rm", "PORTRAIT_URL", "production", "--yes"], cwd=ROOT / "web", capture_output=True)
    subprocess.run(["vercel", "env", "add", "PORTRAIT_URL", "production"], cwd=ROOT / "web", input=base, text=True, check=True,
                   capture_output=True)
    if "--deploy" in sys.argv:
        subprocess.run(["vercel", "deploy", "--prod", "--yes"], cwd=ROOT / "web", check=True)


if __name__ == "__main__":
    main()
