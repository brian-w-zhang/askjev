-- askjev schema (docs/06-pipeline.md §5)
create extension if not exists ltree;
create extension if not exists vector;
create extension if not exists pg_trgm;

-- TOPIC TREE ---------------------------------------------------------------
create table if not exists nodes (
  id            text primary key,
  parent_id     text references nodes(id),
  path          ltree not null,
  depth         int  not null,
  hemisphere    text not null,                  -- world | self | machine | root
  label         text not null,
  description   text not null,
  not_for       text,
  examples      text[] not null default '{}',
  source        text not null,                  -- hand | vital | category | wikidata | usecase | grown
  status        text not null default 'active', -- active | retired
  locked        bool not null default false,
  version       int  not null default 1,
  ord           int,
  share         real,                           -- L1 share of the whole corpus (percent), hand-set
  qid text, sitelinks int, pageviews bigint,
  budget        int,
  choice_card   jsonb,
  embedding     vector(384),
  created_at timestamptz default now(), updated_at timestamptz default now()
);
create index if not exists nodes_path_gist on nodes using gist (path);
create index if not exists nodes_parent on nodes (parent_id) where status = 'active';
create index if not exists nodes_emb on nodes using hnsw (embedding vector_cosine_ops);

create table if not exists node_stats (
  node_id text references nodes(id), scope text,
  n_questions int, n_asked int,
  kind_counts jsonb,
  stability real, frame_gap real, human_gap real, calibration_ece real, brier real,
  placement_conf real, fragile_share real,
  updated_at timestamptz, primary key (node_id, scope)
);

-- QUESTIONS ----------------------------------------------------------------
create table if not exists questions (
  id            text primary key,
  node_id       text references nodes(id),
  path          ltree,
  hemisphere    text not null,
  kind          text,
  shape         text,
  primitive     text not null,                  -- noul | choice | score
  text          text not null,
  options       jsonb,
  state         jsonb,
  template_id   text,
  origin        text not null,
  source text, source_item_id text, license text,
  truth         jsonb,
  flags         text[] not null default '{}',
  display_ok    bool not null default true,
  ask_count     int not null default 0,
  meta          jsonb not null default '{}',
  embedding     vector(384),
  created_at timestamptz default now()
);
create index if not exists q_path_gist on questions using gist (path);
create index if not exists q_node on questions (node_id);
create index if not exists q_tags on questions (hemisphere, kind, shape, primitive, origin);
create index if not exists q_emb on questions using hnsw (embedding vector_cosine_ops);
create index if not exists q_trgm on questions using gin (text gin_trgm_ops);

create table if not exists question_meta (
  question_id   text primary key references questions(id),
  model_served  text,
  top text, p_top real, margin real, entropy real, confidence real,
  top_h text, p_top_h real,
  objective real, disagreement real, ambiguous real, reveals_self real,
  stability real, universe_invariance real, noise real,
  frame_gap real, human_gap real, correct bool, brier real,
  placement_conf real, separation real,
  updated_at timestamptz
);
create index if not exists qm_stab on question_meta (stability);
create index if not exists qm_hgap on question_meta (human_gap);

create table if not exists question_links (
  from_id text references questions(id), to_id text references questions(id),
  type text, condition jsonb,
  primary key (from_id, to_id, type)
);

create table if not exists human_dists (
  question_id text references questions(id), population text, n int,
  distribution jsonb, source text, wave text,
  primary key (question_id, population)
);

-- UNIVERSES ----------------------------------------------------------------
create table if not exists universes (
  id text primary key, family text, method text, expected text, spec jsonb, version int
);
create table if not exists universe_questions (
  question_id text references questions(id), universe_id text references universes(id),
  text text, options jsonb, state jsonb,
  valid_llm real, valid_human bool, jev_equivalent real,
  primary key (question_id, universe_id)
);
create table if not exists universe_stats (
  node_id text references nodes(id), universe_id text references universes(id), scope text,
  n int, drift real, flip_rate real, band_shift real, violation_rate real, updated_at timestamptz,
  primary key (node_id, universe_id, scope)
);
insert into universes (id, family, method, expected, spec, version)
values ('base', 'base', 'none', 'invariant', '{}', 1) on conflict do nothing;

-- PROBES, ANSWERS, CALLS -------------------------------------------------------
create table if not exists probes (
  id text primary key,
  question_id text references questions(id),
  universe_id text not null default 'base' references universes(id),
  frame text,
  variant_kind text,
  variant_params jsonb
);
create index if not exists probes_q on probes (question_id);

create table if not exists answers (
  probe_id text references probes(id), request_hash text,
  model_served text, distribution jsonb, confidence real, score_scalar real,
  option_order jsonb, created_at timestamptz default now(),
  primary key (probe_id, request_hash)
);

create table if not exists calls (
  request_hash text primary key, kind text,
  model_served text, generation_id text, log_file text,
  latency_ms int, input_tokens int, created_at timestamptz default now()
);

-- TREE HISTORY -------------------------------------------------------------
create table if not exists placements (
  question_id text, node_id text, node_version int, method text,
  confidence real, separation real, path_probs jsonb, runner_up ltree,
  created_at timestamptz default now()
);
create index if not exists placements_q on placements (question_id);
create table if not exists tree_events (
  id bigserial primary key, type text,
  node_ids text[], proposal jsonb, metrics jsonb, accepted bool, created_at timestamptz default now()
);
create table if not exists experiments (id text primary key, config jsonb, created_at timestamptz default now());
create table if not exists experiment_probes (experiment_id text, probe_id text, primary key (experiment_id, probe_id));
