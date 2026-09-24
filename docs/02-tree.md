# The tree: a home for every closed question

The tree is **topic only**: what a question is about. What *sort* of judgment it
is goes in tags (`03-questions.md` §1). Keeping the two apart is the core design rule.
For example, "Food" holds factual, taste, social, and evaluative questions.

## 1. Indicators (what every node shows, instead of a grade)
| Indicator | Meaning | Needs |
|---|---|---|
| **Stability** | Do answers survive option shuffles and order swaps? | shuffle probes |
| **Universe drift** | How far answers move in each rewording universe (terse, old-english...) | universe probes (`05-experiments.md` §1) |
| **Calibration** | When Jev says p, is it right p of the time? | ground truth (factual, machine datasets, resolved forecasts) |
| **Human gap** | Distance between Jev's human-frame answer and real human distributions | human data |
| **Frame gap** | Self answer vs "most people" answer | both frames |
| **Placement confidence** | How sure Jev is about where the question belongs | traversal |
| **Default** (Self side) | What Jev picks when asked for itself | self frame |

Per-question values, and how each one is produced, are in `03-questions.md` §8. Nodes only hold
**rollups** of them (in `node_stats`), and the sunburst can color by any of them. Calibration exists
only as a rollup, because a single question has correctness, not calibration.

## 2. Three hemispheres
The first hop is one Jev Choice with this rule:

| Hemisphere | Rule (as given to Jev) | Example |
|---|---|---|
| **MACHINE** | The question can only be answered given a specific piece of input (a ticket, document, tool call, listing, transcript) | "Does this ticket request a refund?" |
| **SELF** | The question is about the answerer or about how people live: traits, values, preferences, choices, relationships | "Would you rather be feared or loved?" |
| **WORLD** | Everything else: things, places, events, ideas, the future | "Most influential Renaissance painter?" |

Machine questions are **template × input**: the same "Is this urgent?" runs over
millions of tickets. In the Machine hemisphere, nodes hold templates, and each question is
one template applied to one real input.

## 3. Ratios and L1 roots
The hemisphere shares are fixed at every scale (10k, 100k, 1M): **World 35 / Self 35 / Machine 30**.
L1 shares below are percentages of the whole corpus.

**WORLD (35%)**: Wikipedia-backed
| L1 | % | Backbone below it (§5) |
|---|---|---|
| Arts & Entertainment | 5 | Vital Articles (Arts) → Wikidata works and artists |
| Sports & Games | 4 | Vital (Everyday life → Sports) + pruned category graph → Wikidata athletes and teams |
| Food & Drink | 3 | Vital (Everyday life → Food) → Wikidata dishes and cuisines |
| Places & Travel | 3 | Vital (Geography) → Wikidata places |
| Nature & Animals | 3 | Vital (Biology, Earth sciences) → Wikidata taxa |
| Science & Math | 3 | Vital (Physical sciences, Mathematics) |
| Technology & Internet | 3 | Vital (Technology) |
| History | 3 | Vital (History; People → historical figures) |
| Society & Culture | 3 | Vital (Society; Philosophy & religion), non-contested only |
| Health & Body | 2 | Vital (Biology & health → Health) |
| Money & Work | 2 | Vital (Society → Economics, Business) |
| The Future | 1 | Manifold markets, by topic |

**SELF (35%)**: built by hand (§6)
| L1 | % | L2 (examples) |
|---|---|---|
| Personality | 8 | Big Five (→ 30 facets), Type (MBTI-style), Dark side (Dark Triad, narcissism), Interests (RIASEC), Humor, Motivation |
| Values & Morality | 9 | Moral foundations, Sacrificial dilemmas, Everyday ethics (AITA), Fairness & justice, Life values (Schwartz), Honesty |
| Love & Relationships | 5 | Dating & attraction, Romance, Friendship, Family, Etiquette & social norms |
| Lifestyle & Taste | 8 | Favorites (color, animal, season, number, word...), This-or-that, Would-you-rather, Habits & routines, Home & style, Leisure |
| Mind & Philosophy | 5 | Big questions (free will, meaning), Thought experiments, Consciousness & AI self-knowledge, Epistemics, Time & mortality |

**MACHINE (30%)**: organized by domain (what the input is about). L2s come from
TypeSafe's use-case map and cookbooks (docs digest §A).
| L1 | % | L2 |
|---|---|---|
| AI Systems & Agents | 5 | Model routing, Guardrails (jailbreak/injection, input + output), Tool-call verification, Function calling (NL → typed call), Skill/tool selection, Hallucination & citation checks, Reasoning-trace classification, Extraction verification (cascade to a bigger model) |
| Trust & Safety | 4 | Toxicity & harassment, Spam & phishing, Unsafe advice, Personal data, Brand safety, Game chat |
| Customer Support | 3 | Intent & topic, Urgency & frustration, Churn & refund, Human escalation, Routing, Voice/banking and smart-home commands, Response verification |
| Search & Retrieval | 3 | Relevance scoring, Pairwise reranking, Context selection (RAG gating), Recommendation |
| Science & Research | 3 | Paper screening, Qualitative coding, Claim-citation support, Methods checks, Entity/relation extraction |
| Software & Code | 3 | Semantic lint, Code review checks, Bug/issue triage, PR and commit classification |
| Legal & Compliance | 2 | Clause detection, Prohibited claims, Policy and regulatory checks |
| Finance, Risk & Insurance | 2 | Claims triage, Fraud indicators, KYC/AML narratives, Risk scoring |
| People & Sales | 2 | Resume-to-role match, Competency evidence, Duplicate records, Lead fit, Purchase intent |
| Commerce & Marketing | 2 | Listing categorization, Attribute extraction, Review abuse, Ad-landing alignment, Demand signals |
| Documents, Data & Analytics | 1 | Structured extraction (fields, dates, amounts via Choice), Document structure recovery, Entity resolution / KG alignment, Hierarchical taxonomy classification, Feature extraction for predictive models |

Deliberately **not** L1 roots: Politics, and religion as belief (the content filter covers
these), and General reference.

## 4. Node schema (built for Jev traversal)
Jev judges each option alone and sees names and descriptions, so every node must
describe itself unambiguously *without its siblings*.
Each node stores: a stable id, parent, **ltree path**, depth, hemisphere, `label`,
`description`, `not_for`, `examples`, `source` (hand | vital | category | wikidata | usecase | grown),
`status` (active | retired), `version`, World-only `qid`/`sitelinks`/`pageviews`, `budget`, an
embedding, and a cached **choice card** (the JSON Jev sees when choosing among siblings). Rollup
indicators live in a separate `node_stats` table. The exact schema is in `06-pipeline.md` §5.

- Children are sent to Jev in TypeSafe's contrastive-criteria shape:
  `{label: {what: description, not_for, examples, sample_children}}`. The docs are split
  between showing sample children (advanced.md) and using opaque `c0..cN` keys (the hierarchical
  cookbook). Which works better on our tree is an early experiment (`05-experiments.md` §10).
- **Fan-out is 8-30 children** (a hard cap of 50 during traversal). Above 50, insert grouping
  nodes: an LLM proposes the groups, Jev assigns members, and a person spot-checks.
- **Siblings are mutually exclusive by description.** Overlap goes into `not_for`.
- **Single parent.** The sunburst needs it.
- **Questions attach to any node**, not only leaves (§8). "Best sport?" lives at Sports, and
  "Best NBA player?" lives at NBA.
- Storage: adjacency list + ltree materialized path. Subtree = `path <@ 'root.world.sports'`;
  no closure table. Capacity: depth 7 × fan-out 20 ≈ 1.3B slots.

## 5. Where the World hemisphere comes from (Wikipedia)
**Use Wikipedia, but not the raw category graph as the tree.** The raw graph has loops,
enumeration categories ("X by country", "1990s births"), maintenance categories, about 2M
nodes, and uneven depth.
1. **Backbone = Vital Articles** (L1 10 → L5 50k), a curated list whose sections already
   match the World L1s. It's fetched via the MediaWiki API
   (`list=categorymembers`, `Category:Wikipedia level-N vital articles`, then strip `Talk:`).
   Each Vital Article is placed under an L2 and spot-checked. **Implemented (Phase 6):** the ~1,000 Level-3
   articles are topic nodes (`source = vital`, not locked) under their World L2, mapped through each article's
   Vital section (`scripts/vital_l3_nodes.py`, reusing `sources/vital4`'s section map; politicians and political
   ideology excluded). Level-4 articles are entity questions (`sources/vital4`), which sit in their L3 topic node
   when one exists and at the L2 otherwise.
2. **Depth only where needed** (e.g. Sports → Basketball → NBA): crawl the category graph
   from the relevant category to depth 3-4 using the **dumps** (`categorylinks.sql.gz`), then:
   - drop hidden/maintenance categories and names matching `/ by | births| deaths|stubs|lists of/`
   - give each category a **single parent**: the parent on the shortest path to the root,
     tie-broken by member count
   - prune with a Jev Noul: "Is this a topic people have opinions about or are curious about?"
3. **Leaves = Wikidata entities**, ranked by sitelinks and capped at 50 per node for Choice menus.
4. **Pageviews** (Pageviews API) give the curiosity weight used in allocation.

IAB Content Taxonomy 3.1 is **not** part of the tree. It's used only as sensitive-topic
tags for the content filter, and as a coverage checklist.

## 6. Where the Self and Machine hemispheres come from
- **Self:** hand-written L2-L3 (~150 nodes). Psychometric instruments are already trees
  (Big Five → 30 facets → items; MFQ foundations; OEJTS dichotomies; RIASEC types).
  Datasets and synthetic banks fill the rest.
- **Machine:** L2 = use cases. Below them are **template nodes**, seeded from about 150 example
  questions in TypeSafe's docs and cookbooks (digest §B) plus labeled datasets (`04-datasets.md`).
  Items are the templates applied to real inputs.

## 7. Jev traversal: placement, search, asking
**Placement** (state = the question text + options):
1. At the root, one Choice over the 3 hemispheres.
2. Descend with **beam K=3**. Each level is one request holding one Choice per beam node
   (independent questions over the same state batch together). Every node also offers
   `here` ("belongs at this node itself") and `none` ("fits none of these").
3. Path score = geometric mean of step probabilities. Stop on `here`, at a leaf, or when
   the best step is < 0.3.
4. The output is the node, placement confidence, runner-up path, and **separation** (top/second path score;
   about 1× means ambiguous). Single-child nodes aren't counted as decisions. When
   confidence is low, stop at the parent level (the SEC cookbook's fallback).
5. Cost: about 7 levels × 150 ms ≈ 1 s, for fractions of a cent.

**Fast paths (latency matters in the UI):**
- **Search:** local embeddings + pgvector give results in ~50 ms, each with its tree path. One Jev
  request then reranks the top 20. Jev's own walk down the tree is optional and runs in the background;
  it's shown when it diverges from the embedding path.
- **Placing new questions:** the nodes of the 10 nearest existing questions become candidates, and one Jev
  Choice picks among them. The full beam traversal above is the fallback, and it's the default for
  bulk pipeline placement, where latency doesn't matter.

**Asking:** dedupe → place → answer bundle (`03-questions.md` §8) → attach, and the indicators
start accruing.

**Placement is also a signal.** If one question's universe versions land in different L1s, that's
either real ambiguity or Jev instability, and both are worth surfacing. The tree is in effect
Jev's own ontology.

## 8. Questions, follow-ups, and rebalancing
**Two separate structures:**
- The **topic tree** holds only topic nodes. Jev walks it, and it's what the sunburst draws.
- **Questions are never tree nodes.** Each canonical question hangs off exactly one topic node,
  at the most specific node it fully fits (a general question stays high: "Best sport?" →
  Sports). In the sunburst, questions appear in the side panel, or as an optional outer ring of
  dots, never as branches.
- **Follow-ups are edges between questions**, not tree depth: `question_links(from, to, type,
  condition)`. Types: `follow_up` (with an answer condition, e.g. "if yes → Favorite
  topping?"), `duplicate`, `pair_reverse`, `decoy_of`. Shuffles, frames, and universe rewordings
  are *probes* of the same question, not linked questions.
  Follow-up chains render as a thread on the question card, and Jev never routes through them.

Why not make questions nodes? Jev would be choosing between topics and questions at the
same step, depth would explode with follow-ups, and every insert would reshape the tree.

**Overload is prevented in three layers, cheapest first:**
1. **Dedupe (on insert).** Exact content hash, then an embedding shortlist (top 10), then a Jev
   Noul batch: "Is this the same question as candidate k?" A duplicate becomes a `duplicate`
   link to the canonical question and bumps its `ask_count`. So 1,000 phrasings of one niche
   question become 1 canonical question with 999 variants, and those real-world rewordings double as
   free stability data.
2. **Split (a batch job, when a node is too full).** Trigger: a node holds more than about 150
   canonical questions directly, *and* embedding clustering finds 2 or more coherent clusters of at least 20.
   An LLM proposes 2-8 children (label, description, not_for), and Jev re-routes all of the
   node's questions. Accept the split only if each new child gets at least 20 questions, the
   median separation is at least 1.5×, and questions under other siblings don't move. General
   questions stay at the parent via `here`. **Depth grows where the questions are dense.**
3. **Group (when a node has too many children).** Above 30 children (hard cap 50), insert
   intermediate grouping nodes, with the same propose → route → accept loop.

**Growth from orphans** follows the same loop: a question whose best option at node N is
`none` (p > 0.5) joins N's orphan pool. At about 20 orphans, cluster them, propose a child,
re-route, and accept or reject.

**Stability rules:**
- Node ids never change. A split creates children and *moves* questions, and every move is logged in
  `placements` (with the node version) and in `tree_events`.
- Nodes are retired (`status = retired`), never deleted. Merging a grown node that stayed nearly
  empty is rare and manual.
- Restructuring runs as a batch job (nightly, or on demand), never on each insert. Rollups are
  recomputed afterwards.
- **Hand-written nodes (L0-L2) are never auto-restructured.** Splits and groups happen only below them.

**Balance is kept separate from demand.** Generated questions follow the budgets
(`03-questions.md` §4). Asked questions are demand and can exceed a node's budget. So:
the mix report counts **canonical questions only**; experiments sample **stratified by node**; and
sunburst sizes use log-scaled counts. A hot niche shows up as depth and `ask_count`,
not as a giant slice.

## 9. Validating the tree
- **Known-path taxonomies:** CPC patents, the Shopify product taxonomy, MeSH, and SEC SIC (from
  TypeSafe's cookbooks) have correct paths, so we can test Jev routing on them before trusting it on ours.
- **Traversal check:** place about 500 dataset questions with known intended nodes, and fix
  descriptions where routing gets confused.
- **Coverage test ("every question has a home"):** place about 1k questions from sources *never
  used to build the tree* (AskReddit titles, Quora, random Hugging Face datasets, the Jev cookbook questions).
  Target: < 5% `none` at L2. Rerun after each growth round.

## 10. Build order
1. Hand-write root → 3 hemispheres → 28 L1 → about 200 L2 nodes (description, not_for,
   examples). This is the most important artifact, so do it carefully.
2. Run the known-path taxonomy test and the traversal check, and fix descriptions.
3. World: attach Vital Articles L3-L5, then Wikidata leaves and category-graph depth where needed.
4. Machine: attach template nodes under the use-case L2s.
5. Run the coverage test → growth and split rounds → fill budgets (`03-questions.md`).
