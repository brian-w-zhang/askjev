# askjev

A map of closed questions (yes/no, pick one, rate on a scale), each answered by [Jev](https://docs.typesafe.ai),
TypeSafe AI's model, to understand what Jev knows, what it defaults to, and where its judgment is jagged. It sits
next to real people's answers wherever those exist. **It is not a benchmark**: every result is an indicator, not a
score. A private project by Brian Zhang, shared with TypeSafe; not affiliated with TypeSafe.

## What's here
- **The map:** 1,043,973 questions shown (of about 1.1 million answered) on a tree of 1,727 topics, drawn as a 3D
  nebula where every question is a star. Search, open any question to see Jev's probabilities next to people's, and
  follow a question's path from the root.
- **The experiments:** 192 experiments, each gathering many questions into one thing you can learn about Jev in a
  minute. Each is a case study: the result and its chart, what it means and doesn't, caveats, Jev's own answers
  about the experiment, how it was done, and every question behind it. Ranked by Jev's own head-to-heads between the
  case studies. The public method docs are in [docs/experiments/](docs/experiments/README.md).
- **The portrait:** nine chapters built from the experiments (character, taste, words, numbers, morals, pressure,
  minds, rough edges), each linking to its case studies.

The questions come from 331 sources: surveys and polls with real human answers, published tests and norms, labeled
task datasets, and banks written for the project. Jev is the only model called (about 2.6 million calls, each cached
by request hash and never re-sent). The answers, findings and site data are private and not in this repo.

## Docs (canonical)
| Doc | What |
|---|---|
| [00-vision](docs/00-vision.md) | What this is and isn't, audience, framing rules |
| [01-jev](docs/01-jev.md) | Calling Jev through the gateway, API semantics, limits, documented jaggedness, question-writing rules |
| [02-tree](docs/02-tree.md) | The topic tree: World / Self / Machine, roots, node schema, how Jev places questions |
| [03-questions](docs/03-questions.md) | Question kinds and shapes, generators, the content filter |
| [04-datasets](docs/04-datasets.md) | Every source, with its license and verdict |
| [06-pipeline](docs/06-pipeline.md) | Stack, stages, data model, invariants, the adapter contract |
| [07-ui](docs/07-ui.md) | The map, question cards, search, navigation, deployment |
| [08-roadmap](docs/08-roadmap.md) | Decisions log and milestones |
| [10-expansion](docs/10-expansion.md) | Growing the corpus from 100k to a million questions in waves |
| [11-portrait](docs/11-portrait.md) | How the portrait's numbers and chapters are made |
| [12-polish](docs/12-polish.md) | The bar for the map, portrait and atlas, and the checks behind it |
| [16-experiments-plan](docs/16-experiments-plan.md) | Experiments, the self-evaluator and Jev's ranking |
| [17-case-studies-plan](docs/17-case-studies-plan.md) | Turning each experiment into a case study: format, style guide, memes, checks |
| [experiments/](docs/experiments/README.md) | Every experiment's method |

Earlier plans and evaluation logs (05, 09, 13-15, the coverage and routing evals) are kept for history.
Agents: see [CLAUDE.md](CLAUDE.md).

## Run
```bash
uv sync && uv run askjev migrate && uv run askjev tree     # schema and tree
uv run askjev pipeline                                     # place, screen, answer, dedupe, measure, roll up
uv run python scripts/star_layout.py                       # star positions for the map (data/stars/)
uv run python scripts/experiments/run.py                   # every experiment's result
uv run python scripts/experiments/export.py                # the atlas's data
uv run python scripts/portrait/story.py && uv run python scripts/portrait/export_page.py   # the portrait's data
cd web && npm install && npm run dev                       # the site at https://askjev.localhost
```
Checks: `scripts/experiments/cases.py check` (every number in a case study traces to its result),
`scripts/portrait/verify_page.py`, and the browser sweeps in `scripts/portrait/` (`sweep.mjs`, `interact.mjs`,
`mobile.mjs`).

## Setup
`cp .env.example .env`, then set `AI_GATEWAY_API_KEY` (Jev is `typesafe-ai/jev` through the Vercel AI Gateway, the
only model the project calls) and `DATABASE_URL` (Postgres). The site deploys on Vercel from `web/`; its private
data is published to Blob storage by `scripts/portrait/publish.py`.
