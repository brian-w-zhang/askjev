"""Dump fastembed (Python) vectors for sample texts to web/parity.json.

The Next.js server embeds search queries with transformers.js; web/scripts/embed_parity.mjs
compares its vectors against these (cosine > 0.99 required, docs/06-pipeline.md §2).
Run: uv run python scripts/embed_parity.py
"""
import json
from pathlib import Path

from askjev.embed import embed

TEXTS = [
    "Is a hot dog a sandwich?",
    "Who is the greater basketball player?",
    "How well does this statement describe you: \"I am the life of the party.\"",
    "Does `message` request a refund?",
    "best pizza topping",
]

vecs = embed(TEXTS)
out = Path(__file__).resolve().parents[1] / "web" / "parity.json"
out.write_text(json.dumps({"texts": TEXTS, "vectors": [[float(x) for x in v] for v in vecs]}))
print(f"wrote {out} ({len(TEXTS)} x {vecs.shape[1]})")
