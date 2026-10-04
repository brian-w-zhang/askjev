# askjev

> *"Everyone wants to know what Jev is, nobody asks how Jev's doing."* — @typesafeai

So I asked. Then I asked it a million other things.

[Jev](https://docs.typesafe.ai) is TypeSafe AI's model: give it any closed question (yes/no, pick one, rate on a
scale) and it hands back a probability for every answer. That makes it cheap to be curious at scale. askjev is what
happens when someone keeps asking: what's its favorite film, what does it think "several" means, would it push the
man off the footbridge, what year does it think it is, and does it cave when you say everyone disagrees?

**This is not a benchmark.** No score, no leaderboard, no model-versus-model. A benchmark asks "how good is it?";
this asks "what's it like?" It's one person's curiosity about one model: weird on purpose, next to real people's
answers wherever they exist, and every number traceable to the questions behind it.

## What's in it
- **A map of a million questions.** 1,043,973 questions shown (of about 1.1 million answered), from 312 sources, on
  a tree of 1,737 topics, drawn as a nebula where every question is a star. Open any one to see Jev's probabilities
  next to real people's answers.
- **198 experiments.** Each gathers many questions into one thing you can learn about Jev in a minute, written up as a
  case study: the result, what it means and doesn't, caveats, and every question behind it. Jev ranked them itself,
  reading the case studies two at a time.
- **A portrait.** How Jev is doing, why ask a model everything, how the questions were gathered and filed, every job
  Jev does in the project, and then its character, taste, words, numbers, morals, the pressure it bends under, and its
  rough edges.

Jev is the only model called: about 2.6 million calls carrying 13.7 million questions, each cached by request and
never sent twice. It filed the questions on the tree, screened them, answered them four ways, merged duplicates,
judged each experiment and even rated its own memes. The answers, findings and site data are private; the site is
shared with TypeSafe directly. Not affiliated with TypeSafe.

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
