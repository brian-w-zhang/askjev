"""Write docs/experiments/README.md: the public index of every experiment (docs/16 pass 3).

The index lists each experiment's question, family, size and Jev's verdict, never its result: titles and results
state findings, and findings stay in the private result files. The count justification is written by hand in
INTRO and COUNT below; the numbers in it are filled from the result files.
Run from the repo root after evaluate.py: `uv run python scripts/experiments/index.py`.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from export import FAMILY

OUT = Path("data/analysis/experiments")
DOC = Path("docs/experiments/README.md")

INTRO = """# Experiments

askjev asks Jev over a million closed questions. An experiment gathers many of them into one thing a person can
learn about Jev in a minute, compared with real people or a right answer where one exists
(`docs/16-experiments-plan.md`). Each has a method doc here (`<id>.md`: question, sourcing, collection, scoring,
chart, evaluation, limits), a private result file (`data/analysis/experiments/<id>.json`) and code in
`scripts/experiments/`. Results are private and are not in this repository; the atlas shows them.

Every experiment was judged by Jev itself (`evaluator.md`): head-to-heads against every other experiment and a gold
set, which decide keep / atlas / rework / cut.
"""

COUNT = """## Why this many

{n} experiments from {sources} sources, {new:,} of the questions asked new for them. The count is what the data
supports at the bar the evaluator holds, not a target:

- **Where the human data is, the experiments are.** Every source with real human answers or a right answer was
  checked (`coverage.md`); each family is the set of angles that source supports with a clear comparison, and angles
  with no finding were cut in the rework pass rather than kept as filler (each family's cuts are listed in its
  code's report and below).
- **New questions only where an experiment needed them:** {newexp} experiments rest on {nsrc} new sources, each a
  published human dataset asked the way the study asked it (`sources/<name>`, license recorded).
- **Jev's verdicts:** {verdicts}.
- **Coverage is measured, not guessed:** `coverage.py` counts, for every branch of the tree, how much of it an
  experiment about that topic uses (the atlas's Coverage tab). Nearly every question with a right answer or real
  people's answers is now in one; what's left is mostly questions with nothing to compare Jev with (question banks
  written for this project, closed questions scraped from Q&A sites), which need new human data, not more slices.
- **Not yet:** frequency words (no open item-level human data), ATUS happiness by activity (BLS blocks scripted
  downloads), old/rich/soon (published means only), Small World of Words (license); see `research-2.md` and
  `coverage.md` for the rest of the queue. Thousands would need many more human datasets per family, not more
  slices of the same ones.
"""


def main():
    exps = [json.loads(p.read_text()) for p in sorted(OUT.glob("*.json")) if not p.name.startswith("_")]
    by = defaultdict(list)
    for e in exps:
        by[e["spec"]["family"]].append(e)
    outcomes = Counter((e.get("evaluation") or {}).get("outcome", "not evaluated") for e in exps)
    srcs = {s for e in exps for s in e["spec"].get("sources") or []}
    newexp = [e for e in exps if e["spec"].get("new_questions")]
    nsrc = {s for e in newexp for s in e["spec"].get("sources") or []}
    lines = [INTRO, COUNT.format(
        n=len(exps), sources=len(srcs), new=sum(e["spec"].get("new_questions", 0) for e in exps), newexp=len(newexp),
        nsrc=len(nsrc), verdicts=", ".join(f"{v} {k}" for k, v in outcomes.most_common()))]
    lines.append("## Index\n")
    order = [f for f in FAMILY if f in by] + sorted(f for f in by if f not in FAMILY)
    for f in order:
        es = sorted(by[f], key=lambda e: -((e.get("evaluation") or {}).get("strength") or -99))
        lines.append(f"### {FAMILY.get(f, f)} ({len(es)})\n")
        lines.append("| experiment | question | n | new | verdict |")
        lines.append("|---|---|---:|---:|---|")
        for e in es:
            s, ev = e["spec"], e.get("evaluation") or {}
            q = s["question"].replace("|", "/")
            lines.append(f"| [`{s['id']}`]({s['id']}.md) | {q} | {e['result'].get('n', 0):,} | "
                         f"{s.get('new_questions') or ''} | {ev.get('outcome', '')} |")
        lines.append("")
    from registry import CUT
    lines.append(f"## Cut ({len(CUT)})\n")
    lines += [f"- `{k}`: {v}" for k, v in CUT.items()] + [""]
    lines.append("Other docs here: `evaluator.md` (the self-evaluator and its meta-evaluation), `coverage.md` (the internal "
                 "coverage pass), `research-2.md` (the second outside research pass).\n")
    DOC.write_text("\n".join(lines))
    print(f"{DOC}: {len(exps)} experiments in {len(by)} families; {dict(outcomes)}")


if __name__ == "__main__":
    main()
