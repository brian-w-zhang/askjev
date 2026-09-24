"""Apply every labeled restructure proposal in authored/restructure/ (groups first, then splits) and log results
to docs/restructure-log.md. Proposals with < 2 labeled clusters are skipped. Each apply enforces the accept rules."""
import json
from pathlib import Path

from askjev.config import AUTHORED, ROOT
from askjev.restructure import apply

files = sorted((AUTHORED / "restructure").glob("group__*.json")) + sorted((AUTHORED / "restructure").glob("split__*.json"))
log = ["# Restructure log (round 2, Phase 6 scale)", "",
       "Proposals from `askjev restructure` (clusters) → authored labels → `apply` (Jev re-route + accept rules:",
       "split: each child ≥ 20 questions, median separation ≥ 1.5×, < 10% sibling moves; group: ≥ 80% of member questions",
       "routed to their own group).", ""]
acc = rej = skip = 0
for f in files:
    prop = json.loads(f.read_text())
    labeled = [c for c in prop["clusters"] if c["child"].get("label")]
    if len(labeled) < 2:
        skip += 1
        continue
    try:
        r = apply(str(f))
    except Exception as e:  # keep going; record the failure
        r = f"ERROR {type(e).__name__}: {e}"
    print(r, flush=True)
    acc += r.startswith("ACCEPTED")
    rej += r.startswith("REJECTED") or r.startswith("ERROR")
    log.append(f"- `{f.name}`: {r}")
log += ["", f"**Accepted {acc}, rejected {rej}, skipped (unlabeled) {skip}.**"]
(ROOT / "docs" / "restructure-log.md").write_text("\n".join(log) + "\n")
print(f"accepted {acc}, rejected {rej}, skipped {skip}")
