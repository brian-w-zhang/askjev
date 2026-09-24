# askjev

A tree that has a place for every closed question a human or a program could ask (yes/no, pick one,
rate on a scale), filled with real questions answered by [Jev](https://docs.typesafe.ai),
TypeSafe AI's System One model. The goal is to understand Jev: its capabilities, its defaults, and
where its judgments are jagged. **It is not a benchmark.** Private project (Brian + TypeSafe).

**Status:** planning complete, no code yet. Next: gateway and determinism spikes, then the tree skeleton.

## Docs (canonical; read in order)
| Doc | What |
|---|---|
| [00-vision](docs/00-vision.md) | What this is and isn't, audience, framing rules, success |
| [01-jev](docs/01-jev.md) | How we call Jev (gateway), API semantics, limits, determinism, documented jaggedness, question-writing rules, legal |
| [02-tree](docs/02-tree.md) | Indicators, World / Self / Machine, 28 L1 roots + ratios, node schema, Jev traversal and growth, validation |
| [03-questions](docs/03-questions.md) | Tags (kind/shape), target mix, generators, allocation, synthetic method, content filter, scale ladder |
| [04-datasets](docs/04-datasets.md) | Every source with a license and a verdict, Machine seeds, structure sources |
| [05-experiments](docs/05-experiments.md) | The jaggedness experiments and the finding format |
| [06-pipeline](docs/06-pipeline.md) | Stack, stages, batching, data model, invariants, adapter contract |
| [07-ui](docs/07-ui.md) | Sunburst, question cards, findings page, search, private ask box |
| [08-roadmap](docs/08-roadmap.md) | Decisions log, milestones, open questions |

Agents: see [CLAUDE.md](CLAUDE.md).

## Setup
`cp .env.example .env`, then set `AI_GATEWAY_API_KEY` (Jev = `typesafe-ai/jev` via Vercel AI Gateway; the
only model the project calls) and `DATABASE_URL` (local Postgres for the MVP, Neon later).

## Resources
Read-only source material in [resources/](resources/): the Diogo Almeida interview transcript,
the full TypeSafe docs archive + digest, Brian's Notion notes, and the origin conversation
(historical).
