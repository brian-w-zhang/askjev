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
- **The map.** 1,043,973 questions (of 1,109,409 answered) from 312 sources, filed on a tree of 1,737 topics in three
  hemispheres (the World, the Self, the Machine), drawn as a dithered nebula where every question is a dot. Search by
  meaning, fly down a question's path, and open any one to see Jev's probabilities next to real people's answers.
- **The atlas: 198 experiments.** Each gathers thousands of questions into one thing you can learn about Jev in a
  minute, written up as a case study: the result, what it means and what it doesn't, the caveats, Jev's own take on
  it, and every question behind it.
- **The portrait.** A long read in fourteen chapters: how Jev is doing (asked on real wellbeing scales), why ask a
  model everything, where the questions came from, every job Jev does in this project, and then its personality,
  taste, language, numbers, confidence, morals, risk, the peer pressure it bends under, its habits, and where similar
  tasks at work get different results.

The answers, findings and site data stay private: the site is shared with TypeSafe directly, and this repo holds the
code and the method. Not affiliated with TypeSafe.

## Jev, all the way down
Jev is the only model called. It doesn't just answer the questions; it runs the project. Every step that needs a
judgment is one small typed question to Jev, and code does the rest.

| Layer | What Jev is asked | Type | Questions | Calls |
|---|---|---|---:|---:|
| **Read** | describe each question: is it factual, ambiguous, revealing about the answerer; how much would people disagree? | yes/no, rate | 3,847,618 | 216,977 |
| | screen it for contested politics and graphic content | yes/no | 2,359,406 | 17,452 |
| | flag known weak spots (arithmetic, counting, exact numbers, dates) | yes/no | 1,118,836 | |
| **File** | walk it down the topic tree, one choice per level, three paths at once | pick one | 2,304,842 | 1,748,915 |
| | is this the same question as that one? | yes/no | 99,922 | 99,922 |
| **Answer** | answer as asked, and with the options reordered or the scale reversed | as written | 3,289,691 | 490,156 |
| | answer the way most people would | as written | 643,975 | 104 |
| **Judge** | this experiment is about you: does it match how you see yourself, is the comparison fair, which caveat matters? | yes/no, rate, pick one | 9,204 | 1,398 |
| | which of these two teaches a curious reader something more surprising? | pick one | 31,424 | 31,424 |
| **Laugh** | how funny is this meme? | rate | 225 | 225 |
| **Search** | which of these 20 questions does the search mean? | pick one | live | 350 |

That's 2.6 million calls carrying 13.7 million questions. Jev takes many questions per request when they share
context, so one call can screen, describe and flag a batch at once; the median call took 244 ms. Every request is
cached by its hash and never sent twice, and the version that served it is logged with the answer.

Two places Jev checks its own inputs:
- **Synthetic questions earn their place.** Where no dataset existed, questions were written for this project and
  then walked down the tree blind; only the ones Jev filed where they were meant to go were kept (64% of 270,562).
- **Placement is measured.** Jev's walk reaches the right branch 91.6% of the time on a 332-question held-out set,
  so the map's structure is something Jev mostly agrees with, not just something imposed on it.

What isn't Jev:
- **Claude** wrote the synthetic questions, the topic descriptions, the case studies and the meme captions. It
  never answers a question.
- **bge-small-en-v1.5**, run locally, makes the embeddings: similar questions for search and duplicates, nearest
  topics, and the map's Meaning layout.
- **Code** turns sources into questions, and turns Jev's answers into experiments, intervals and charts.

## How a question gets onto the map
```
fetch → normalize → screen → dedupe → place → answer → measure → roll up → (restructure)
```
1. **Gather.** One adapter per source (polls, personality tests, trivia, labeled work datasets, crowd judgments,
   Reddit and Stack Exchange) turns its rows into closed questions, keeping the real answer key and the crowd's
   answer split wherever they exist. 46% of questions have a right answer; 22% have real people's answers.
2. **Screen.** Jev reads each question for contested politics and graphic content. Those are answered but not
   shown (65,436 hidden), and a narrower second pass released questions the first caught by mistake.
3. **Dedupe.** Exact hashes, then an embedding shortlist, then Jev decides; duplicates become links, not new dots
   (5,729 merged).
4. **Place.** Structured sources file themselves (a personality item goes to its facet). Everything else is walked
   down the tree by Jev: one choice per level, three paths at once, stopping at a leaf, when Jev says "here", or one
   level up when it's unsure. Crowded topics split.
5. **Answer.** Each question is asked as written, for "most people", with its options shuffled and with rating
   scales reversed, so every answer carries its own stability check.
6. **Measure and roll up.** Per question: Jev's answer, its stability, the gap to its "most people" answer, the gap
   to real people, and whether it's right. Per topic, the same rolled up over the branch.

The pipeline is idempotent and resumable: kill it anywhere and it picks up where it left off, without re-sending a
request it already has.

## Stack
| | Local | Production |
|---|---|---|
| Pipeline | Python (uv), psycopg, Polars | none: production reads a copy |
| Database | Postgres 17 with `ltree` (tree paths), `pgvector` (search), `jsonb` (distributions) | PlanetScale Postgres, a trimmed copy loaded by `scripts/sync_prod.py` (full or delta) |
| Embeddings | `fastembed` (ONNX) | transformers.js with the same ONNX weights, inside the search function; half-precision vectors with a 1-bit HNSW index, then an exact re-rank |
| Jev | Vercel AI Gateway (`typesafe-ai/jev`) | the same, behind a per-visitor limit; cached answers are free |
| Site | Next.js 16, React Three Fiber, a custom dither pass | Vercel: static portrait, atlas and case studies; read-only APIs cached at the edge |
| Big files | `data/` (Parquet, zstd JSONL call logs) | Vercel Blob: the star snapshot and the portrait's data |

A few details:
- **The map draws a million dots.** Each question is 12 bytes in one packed buffer (its topic, an offset inside the
  topic's ball and a few indicators), drawn as a single instanced mesh and dithered onto TypeSafe's palette at
  half resolution. Layouts compute in a web worker.
- **Search** embeds the query, finds the nearest questions by meaning, then asks Jev once to reorder the top 20 and
  say whether any of them is really the question.
- **Jev's tree walk runs in TypeScript in production**, a port of the pipeline's walk that builds byte-identical
  requests, so it reuses the cached answers.

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
`scripts/portrait/verify_page.py` (every number on the portrait traces to the claims ledger), and the browser
checks in `scripts/portrait/`: `sweep.mjs`, `interact.mjs`, `mobile.mjs`, and `perf.mjs` (how long clicks and page
switches take on a desktop and a phone).

## Setup
`cp .env.example .env`, then set `AI_GATEWAY_API_KEY` (Jev is `typesafe-ai/jev` through the Vercel AI Gateway, the
only model the project calls) and `DATABASE_URL` (Postgres). The site deploys to Vercel from `web/` on every push to
`main`. Data reaches production separately: `scripts/sync_prod.py` copies the database, and
`scripts/portrait/publish.py` uploads the portrait's and the atlas's data to Blob storage.
