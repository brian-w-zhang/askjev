# Pipeline, storage, schema

Target: thousands of questions on day one, millions eventually. The tree must be easy for Jev to
traverse, and searchable and filterable by Jev and by the UI.

## 1. Where data lives
| Layer | Store | Holds | Why |
|---|---|---|---|
| **System of record** | **Postgres** (local Homebrew Postgres 17 for the MVP; Neon via Vercel Marketplace when it needs sharing) | the tree, questions, probes, answers, metadata, links, placements, tree events | Both the Python pipeline and the Next.js app read and write it. **ltree** handles tree paths, **pgvector** handles search, **jsonb** holds distributions, and B-tree indexes handle metadata filters |
| **Raw + logs** | files under `data/` (Parquet + zstd JSONL; move to Vercel Blob or R2 if needed) | raw downloads, normalized sources, the full request/response log of every Jev call | Immutable, cheap, and the source of truth for rebuilding |
| **Analysis** | DuckDB (reads Parquet, and Postgres via its postgres extension) | experiment crunching, calibration curves, BT fits | Fast columnar analytics without loading Postgres |

Size at 1M questions: roughly 2-4 GB in Postgres, with 384-dim local embeddings
(bigger embeddings would dominate storage). A Neon paid tier handles this; the free tier covers the 10k slice.
Confirm that the `ltree`, `vector`, and `pg_trgm` extensions are enabled when provisioning.

## 2. Stack
- **Python** (uv) pipeline with psycopg and Polars. CLI: `askjev <stage> [--source X]`. Every stage is
  idempotent and resumable.
- **Jev** is the only gateway model: `typesafe-ai/jev` (latest; 32k context) via `AI_GATEWAY_API_KEY`.
  The client is written after the gateway shape spike (`05-experiments.md` §0). The `typesafe-sdk` is not used.
- **LLM steps** (universe transforms, Score-level wording, G5 banks, node descriptions, split/group/growth
  proposals) are done by Claude Code or its subagents, which write YAML/JSONL into `authored/` for the
  pipeline to ingest. They never answer questions, and no other gateway model is called.
- **Embeddings:** a local open model, `BAAI/bge-small-en-v1.5` (384 dims, CPU, public download, no login,
  free). The pipeline uses `fastembed` (ONNX); the Next.js server uses transformers.js with the same ONNX
  weights (`Xenova/bge-small-en-v1.5`, unquantized), so query and stored vectors are compatible. A
  parity test is required: cosine > 0.99 between the two runtimes on sample texts. Query embedding takes ~10-30 ms.
- **Next.js** (later) queries Postgres directly for the tree, cards, search, and the ask box.

## 3. Directory layout
```
data/                                   # gitignored
  raw/<source>/<version>/...            # untouched downloads + SHA256 + LICENSE.txt
  normalized/<source>.parquet           # canonical questions from each adapter
  calls/<date>/<shard>.jsonl.zst        # append-only Jev request/response log
authored/                               # agent-written content (node descriptions, synthetic questions, transforms), versioned in git
sources/<source>/{adapter.py, source.yaml}   # url, license, kind/shape, primitive mapping, node mapping
tree/                                   # hand-written nodes (L0-L2, Self subtrees, Machine use cases) as YAML, versioned in git
db/migrations/                          # SQL schema
```

## 4. Stages
```
fetch → normalize → screen → dedupe → place → expand → plan → ask → explode → measure → rollup → (restructure)
```
| # | Stage | What happens |
|---|---|---|
| 1 | fetch | Download once per source version; store the checksum and license text |
| 2 | normalize | The adapter emits canonical questions + human distributions + truth → Parquet, then upsert into Postgres |
| 3 | screen | One **screen request** per candidate (`03-questions.md` §8): filter, weak-spot, kind, self-assessment |
| 4 | dedupe | Exact hash, then an embedding shortlist, then Jev "same question?" Nouls. Duplicates become links and aren't placed (`02-tree.md` §8) |
| 5 | place | Deterministic for structured sources (IPIP scale → facet node, Wikidata class → node); otherwise Jev beam placement (`02-tree.md` §7). The result goes to `placements` |
| 6 | expand | Quota sampling (`03-questions.md` §4) → **probes** (frames × shuffles, plus experiment variants) |
| 7 | plan | Group probes that share a state into requests under a **32k-token budget**; compute `request_hash`; skip hashes already logged |
| 8 | ask | Async, token bucket (1,200 req/min, 250k tok/s), ~8 workers, backoff on 429/529, fsync each log line; safe to kill and restart |
| 9 | explode | Parse the log → `answers` (per probe, options mapped back, permutation + served version recorded) |
| 10 | measure | Compute `question_meta` (answer summary, stability, frame gap, human gap, correctness) |
| 11 | rollup | Recompute `node_stats` (direct and subtree) |
| 12 | restructure | Batch job: split, group, and growth proposals → accept/reject → move questions → rollup (`02-tree.md` §8) |

Asks from the UI run stages 3-5 and 7-11 inline for a single question, using the merged screen + answer request.

## 5. Schema (Postgres)
```sql
create extension if not exists ltree;  create extension if not exists vector;  create extension if not exists pg_trgm;

-- TOPIC TREE -------------------------------------------------------------
create table nodes (
  id            text primary key,              -- stable slug; World entity leaves 'wd_Q36159'
  parent_id     text references nodes(id),
  path          ltree not null,                -- root.world.sports.basketball.nba
  depth         int  not null,
  hemisphere    text not null,                 -- world | self | machine
  label         text not null,
  description   text not null,                 -- standalone: what belongs here
  not_for       text,                          -- boundary cases → named sibling
  examples      text[] not null default '{}',
  source        text not null,                 -- hand | vital | category | wikidata | usecase | grown
  status        text not null default 'active',-- active | retired
  locked        bool not null default false,   -- hand-written L0-L2: never auto-restructured
  version       int  not null default 1,
  ord           int,
  qid text, sitelinks int, pageviews bigint,   -- World only
  budget        int,                           -- allocated canonical-question budget
  choice_card   jsonb,                         -- cached {label:{what,not_for,examples,sample_children}} for Jev
  embedding     vector(384),                   -- label + description (local bge-small)
  created_at timestamptz default now(), updated_at timestamptz default now()
);
create index on nodes using gist (path);
create index on nodes (parent_id) where status = 'active';
create index on nodes using hnsw (embedding vector_cosine_ops);

create table node_stats (                      -- rollups, recomputed; kept off the hot nodes table
  node_id text references nodes(id), scope text,   -- 'direct' | 'subtree'
  n_questions int, n_asked int,
  kind_counts jsonb,                           -- {"taste": 120, "factual": 40, ...}
  stability real, frame_gap real, human_gap real, calibration_ece real, brier real,
  placement_conf real, fragile_share real,
  updated_at timestamptz, primary key (node_id, scope)
);

-- QUESTIONS (canonical; the unit of the mix) --------------------------------
create table questions (
  id            text primary key,              -- content hash of (primitive, text, options, state)
  node_id       text references nodes(id),
  path          ltree,                         -- denormalized copy of the node path (fast subtree filters)
  hemisphere    text not null,
  kind          text,                          -- World/Self
  shape         text,                          -- Machine
  primitive     text not null,                 -- noul | choice | score
  text          text not null,                 -- for Machine: the template instructions
  options       jsonb,                         -- Choice options / Score levels (ordered) / Noul criteria
  state         jsonb,                         -- context; for Machine the real input
  template_id   text,                          -- Machine and G2 families
  origin        text not null,                 -- dataset | template | wikidata-fact | typesafe-docs | synthetic | mined | asked
  source text, source_item_id text, license text,
  truth         jsonb,                         -- ground truth if known
  flags         text[] not null default '{}',  -- content filter / weak spots
  display_ok    bool not null default true,
  ask_count     int not null default 0,        -- incremented by duplicates
  embedding     vector(384),
  created_at timestamptz default now()
);
create index on questions using gist (path);
create index on questions (node_id);
create index on questions (hemisphere, kind, shape, primitive, origin);
create index on questions using hnsw (embedding vector_cosine_ops);
create index on questions using gin (text gin_trgm_ops);

create table question_meta (                   -- the small, filterable per-question core (03-questions.md §8)
  question_id   text primary key references questions(id),
  model_served  text,
  top text, p_top real, margin real, entropy real, confidence real,          -- self frame
  top_h text, p_top_h real,                                                -- human frame
  objective real, disagreement real, ambiguous real, reveals_self real,   -- Jev self-assessment
  stability real, universe_invariance real, noise real,                 -- measured
  frame_gap real, human_gap real, correct bool, brier real,
  placement_conf real, separation real,
  updated_at timestamptz
);
create index on question_meta (stability);  create index on question_meta (human_gap);

create table question_links (                  -- follow-ups, variants, duplicates: never tree edges
  from_id text references questions(id), to_id text references questions(id),
  type text,                                   -- follow_up | variant | duplicate | pair_reverse | decoy_of
  condition jsonb,                             -- e.g. {"answer": "yes"} for follow_up
  primary key (from_id, to_id, type)
);

create table human_dists (
  question_id text references questions(id), population text, n int,
  distribution jsonb, source text, wave text, primary key (question_id, population)
);

-- PROBES AND ANSWERS -----------------------------------------------------
-- UNIVERSES (overlays on the same tree; 05-experiments.md §1) ------------------
create table universes (
  id text primary key,                         -- 'base', 'terse', 'old-english', 'negated', ...
  family text, method text,                    -- method: llm | code
  expected text,                               -- invariant | flip | explore
  spec jsonb, version int                      -- exact transform prompt/code ref
);
create table universe_questions (              -- the transformed text of a question in a universe
  question_id text references questions(id), universe_id text references universes(id),
  text text, options jsonb, state jsonb,       -- option ids stable, text transformed
  valid_llm real, valid_human bool, jev_equivalent real,   -- gate + the (non-gating) Jev equivalence Noul
  primary key (question_id, universe_id)
);
create table universe_stats (
  node_id text references nodes(id), universe_id text references universes(id), scope text,
  n int, drift real, flip_rate real, band_shift real, violation_rate real, updated_at timestamptz,
  primary key (node_id, universe_id, scope)
);

create table probes (                          -- what is sent: question × universe × frame × variant
  id text primary key,                         -- hash of the exact sent question JSON + state
  question_id text references questions(id),
  universe_id text not null default 'base' references universes(id),
  frame text,                                  -- self | human | human@FR | none
  variant_kind text,                           -- base | shuffle | label_scheme | inversion | decoy | scale_k | meta | repeat
  variant_params jsonb
);
create table answers (
  probe_id text references probes(id), request_hash text,   -- request_hash → the call log on disk
  model_served text, distribution jsonb, confidence real, score_scalar real,
  option_order jsonb, created_at timestamptz,
  primary key (probe_id, request_hash)
);
create table calls (                           -- index of the on-disk log (bodies stay on disk)
  request_hash text primary key, kind text,    -- jev
  model_served text, log_file text, latency_ms int, input_tokens int, created_at timestamptz
);

-- TREE HISTORY -----------------------------------------------------------
create table placements (                      -- every placement and move, never overwritten
  question_id text, node_id text, node_version int, method text,  -- deterministic | jev | split | manual
  confidence real, separation real, path_probs jsonb, runner_up ltree, created_at timestamptz
);
create table tree_events (
  id bigserial primary key, type text,         -- split | group | grow | retire | edit
  node_ids text[], proposal jsonb, metrics jsonb, accepted bool, created_at timestamptz
);
create table experiments (id text primary key, config jsonb, created_at timestamptz);
create table experiment_probes (experiment_id text, probe_id text, primary key (experiment_id, probe_id));
```

## 6. How the schema serves each access pattern
| Need | Query |
|---|---|
| **Jev traversal step** | `select choice_card from nodes where parent_id = $1 and status = 'active' order by ord`. Cards are cached per node version, so one read builds the Choice |
| **Subtree filter** | `questions where path <@ 'root.world.sports'` + kind/primitive/origin indexes |
| **Fragile or interesting questions** | join `question_meta`: `stability < 0.67`, `human_gap > 0.3`, `frame_gap` desc... |
| **Search** (instant, then refined) | Local query embedding → pgvector HNSW top-k + `pg_trgm` → results in ~50 ms, each with its `path` (the animation starts from this). Then **one** Jev request reranks the top 20 (~150 ms). Optionally Jev's own tree walk runs in the background, and the UI shows where it diverges from the embedding path |
| **Dedupe** | exact `id`, then pgvector top-10 on `embedding` → one batched request of Jev "same question?" Nouls |
| **Placement of a new question** | Fast path: the nodes of its 10 nearest questions become the candidates, and **one** Jev Choice picks among them (plus `none`). Full beam traversal only when the candidates are spread across L1s or the Choice isn't confident |
| **Sunburst** | `nodes` + `node_stats` (scope `subtree`) for 2 rings at a time, queried live |
| **Reproducibility** | `answers.request_hash` → `calls.log_file` → the exact request/response body |

## 7. Invariants
- Never re-send a request whose hash is already logged. The first response is canonical;
  deliberate repeats get a `repeat` probe variant with an index.
- Content hashes dedupe exact repeats; near-duplicates become `duplicate` links.
- Every displayed answer traces to a raw request/response and the served version. Never compare
  across served versions within one analysis.
- Questions and nodes are flagged or retired, never deleted. Moves are logged in `placements`.
- `questions.path` is always updated in the same transaction as `node_id`.

## 8. Adapter contract
```python
class Adapter:
    source: str
    def fetch(self, raw_dir) -> None                          # download into raw/<source>/<version>/
    def normalize(self, raw_dir) -> Iterator[Question]        # canonical questions (+ HumanDist, truth)
```
Adding a source means adding `sources/<name>/adapter.py` + `source.yaml`, and nothing else changes.
The primitive mapping (e.g. Likert 1-5 → 5 Score levels written as concrete situations) lives in the
adapter.
