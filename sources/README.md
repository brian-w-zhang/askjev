# Source adapters

One folder per source: `sources/<name>/adapter.py` + `sources/<name>/source.yaml`.
Run with `uv run askjev source <name>`: `fetch()` then `normalize()` →
`data/normalized/<name>.jsonl` (gitignored). Then `uv run askjev ingest <name>` loads it into Postgres.

## Contract
```python
# sources/<name>/adapter.py
from pathlib import Path
from typing import Iterator
from askjev.model import Question, HumanDist

NAME = "<name>"

def fetch(raw_dir: Path) -> None:
    """Download public files into raw_dir (skip anything needing a login). Idempotent: skip if present."""

def normalize(raw_dir: Path) -> Iterator[Question]:
    """Yield canonical Questions. Sample/cap here to the target count in source.yaml."""
```
`source.yaml`: `name, url, license, version, target (count for the 10k slice), hemisphere, kind|shape, notes`.

## Question fields (src/askjev/model.py)
- `text`: the question in the **self frame**, full and standalone (Jev never sees ids).
  Machine: the template instructions, e.g. "Does this message request a refund?".
- `primitive`: `noul` (yes/no) | `choice` (2-255 options) | `score` (2-10 ordered levels).
- `options`:
  - choice: `{"key": "description or None"}`. Keys are short, readable, and distinct; Jev sees them.
  - score: `["level 0", ...]` low→high, **each level a concrete standalone situation**, not a degree word.
    For Likert agreement use concrete levels, e.g. ["This does not describe me at all", "This describes me a little",
    "This describes me moderately well", "This describes me well", "This describes me very well"].
  - noul: `{"true": "...", "false": "..."}` or None.
- `state`: context JSON (the dilemma, scenario, passage, ticket). None for stateless questions.
- `hemisphere`: world | self | machine. `kind` (world/self): personality, values, taste, evaluative,
  social, factual, forecast, perception. `shape` (machine): classify, detect, score, route, rank, verify, extract.
- `origin`: dataset | template | wikidata-fact | typesafe-docs | synthetic.
- `node_hint`: tree node id where it belongs (see `tree/*.yaml`). A best guess is fine: placement falls
  back to a Jev walk from the deepest existing ancestor.
- `truth`: ground truth if known (choice key; noul true/false; score level index).
- `human`: list of `HumanDist(population, distribution, n, source, wave)`. The distribution keys must match
  the option keys (choice), `"0".."k"` (score), or `"true"/"false"` (noul). Shares sum to 1.
- `human_text`: optional explicit "most people" wording; otherwise the pipeline wraps `text`.
- `license`, `source_item_id`, `meta` (anything source-specific).

## Rules
- Public downloads only (HF `https://huggingface.co/datasets/<id>/resolve/main/<file>`, OSF, GitHub raw...).
  No logins and no tokens. Never call any model API.
- Follow docs/01-jev.md §7: one judgment per question, no arithmetic, dates, or counting; categorical facts only.
- Flag contested politics in `meta["flags"] = ["political"]` (don't drop it). Drop sexual content involving
  minors and slurs outright; flag other sexual or self-harm content with `"sensitive"`.
- Deterministic sampling (seeded) so reruns produce identical ids.
