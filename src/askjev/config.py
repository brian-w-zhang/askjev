import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RAW = DATA / "raw"
CALLS = DATA / "calls"
TREE_DIR = ROOT / "tree"
AUTHORED = ROOT / "authored"
SOURCES = ROOT / "sources"

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/askjev")
GATEWAY_KEY = os.environ.get("AI_GATEWAY_API_KEY", "")
GATEWAY_URL = "https://ai-gateway.vercel.sh/v1/evaluate"
JEV_MODEL = "typesafe-ai/jev"  # the ONLY gateway model this project may call
# Gateway provider pinning: Jev is also served through DigitalOcean, which returned most of our 503s (2026-09-25);
# route only to TypeSafe's own endpoint. Comma-separated gateway provider slugs; empty = let the gateway choose.
JEV_PROVIDERS = [p for p in os.environ.get("ASKJEV_PROVIDERS", "typesafe-ai").split(",") if p]

# Gateway context is 32k tokens; leave headroom for tokenizer mismatch (we estimate ~4 chars/token).
REQUEST_TOKEN_BUDGET = 24_000
MAX_WORKERS = int(os.environ.get("ASKJEV_WORKERS", 8))
REQUESTS_PER_SECOND = float(os.environ.get("ASKJEV_RPS", 18))  # under the 1,200 req/min limit; lower it when running processes in parallel

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384

for d in (RAW, CALLS, AUTHORED):
    d.mkdir(parents=True, exist_ok=True)
