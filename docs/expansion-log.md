# Expansion log

_One section per wave (`docs/10-expansion.md` §3). Newest first._

## Wave 2: 239k → 300k (gated 2026-09-25)
**299,863 canonical questions** (+60,544), all placed and answered; 1,388 active nodes (+23); 140,253 distinct texts;
170,737 with ground truth; 76,770 human distributions; 587k cached Jev calls.

| | Wave 2 added | Rule |
|---|---|---|
| Anchored | 40,290 (**67%**) | ≥ 60% ✅ |
| Synthetic | 3,254 (5%): world thin-node bank, 67% round-trip accept | ≤ 15% ✅ |
| Hemispheres after | World 36.5 · Self 32.9 · Machine 30.6 | Self still short → wave 3 leans Self |

**Added:** Machine +26k (agent-trace success, code defects, commit types, fake reviews, receipt extraction, wine ratings,
sarcasm, BeaverTails unsafe replies, FEVER, ChemProt relations, SNIPS, e-commerce departments, escalation requests, Davidson
hate/offensive capped at 1,000); World +20k (Quora world top-up 12k, HotpotQA comparisons, Manifold +2,000 with midlife prices,
world thin-node bank); Self +14k (Moral Machine 3,000 with global and per-country vote shares, O*NET work activities 5,000,
ETHICS virtue and deontology 6,000). MedMCQA and CommonsenseQA are written but held (factual is 22.6% vs 15%).

**Measurements:** most informative: wine ratings 0.45, commit types 0.47, Devign defects 0.54, SWE-agent success 0.68,
Manifold 0.71, BeaverTails 0.74, hate/offensive 0.77. Saturated: CORD receipts 0.98, SNIPS 0.97 (stop scaling). O*NET and Moral
Machine are almost never decisive (≤ 2%). Kinds after the wave: personality 5.4 (was 3.4), evaluative 5.7, perception 0.7
(short), factual 22.6 (over).

**Tree:** template split of 6 nodes (guardrails, claim support, commands, interests, honesty/trust, sacrificial dilemmas;
12 children incl. Self-Driving Car Dilemmas and Work Activities); descend of 1,606 hint-placed questions (mammals, cities);
13,606 Quora questions placed by beam walk; cluster splits **accepted** for parents/siblings/relatives (5 children), friends/peers
(roommates, school, coworkers, events) and dating/partners (crushes, couple life, jealousy/cheating, breakups). Skipped as
question-type (not topic) splits: reading_motives, reading_feelings. `repair-paths` 0; star layout 282,224 stars in 1,324 nodes.

**Decisions:** dropped `support_tickets` (synthetic tickets, near-random labels) and `tv_pairs` (Netflix Prize data, withdrawn
after a privacy lawsuit); Yahoo closed titles capped at 4,000 (messier than Quora); template split never re-splits a template
already in its own node; descend skips questions descended before.

**Known issues:** everyday_ethics still ~4.8k (split rejected twice for sibling moves); the pipeline can answer questions before
placing them when ingest outpaces the place stage (they get placed on the next pass; no effect on answers); quora_closed's
political regex matches "electricity" (fixed in newer adapters, left in quora_closed so ids stay stable).

## Wave 1: 99k → 239k (gated 2026-09-25)
**239,319 canonical questions** (+139,861), all placed, screened and answered (4 left for the next pass); 1,365 active nodes
(+46); 111,980 distinct question texts (was 52,466); 133,474 with ground truth; 67,994 human distributions; 466k cached Jev calls.
The wave overshot 200k because sourcing ran ahead of Jev; the next wave starts from here.

| | Wave 1 added | Rule |
|---|---|---|
| Anchored (truth or human data) | 124,044 (**89%**) | ≥ 60% ✅ |
| Synthetic | 5,764 (4%): lifestyle/love 3,538 (71% round-trip accept), mind/personality 2,226 (49%) | ≤ 15% ✅ |
| Hemispheres after the wave | World 37.3% · Self 35.3% · Machine 27.3% (was 41.7 / 31.8 / 26.6) | toward 35/35/30 ✅ |

**Added** (details and verdicts in `04-datasets.md`): Machine +39k across 15 sources that fill formerly empty leaves
(toxicity, PII, hallucination grounding, tool calls, skill selection, routing, commands, taxonomy, contracts, issue triage,
paper screening, resumes); World +48k (MMLU, ARC, SciQ, OpenBookQA, StrategyQA, BoolQ remainder, Wikidata facts and
comparisons, Quora); Self +53k (Social IQa, six pairwise taste sets with co-rater human shares, full IPIP pool, SWCPQ word
pairs, EPQ-R, Moral Stories, MoralChoice, DailyDilemmas, Scruples top-up, two authored banks).

**Measurements that steer wave 2**
- **Saturated, stop scaling:** Wikidata facts (0.96 correct, 0.81 decisive), ARC 0.99, SciQ 0.97, OpenBookQA 0.95, function-call
  verification 0.96, DBpedia 0.99, MoralChoice low-ambiguity 1.00.
- **Most informative (Jev often wrong or unsure):** resume categories 0.61, civil_comments 0.73, GitHub issue type 0.73,
  Yahoo topics 0.74, HaluEval grounding 0.76, StrategyQA 0.76, BoolQ 0.79. Taste pairs are almost never decisive (1-9%),
  so they carry the human-gap signal.
- **Kinds after the wave:** factual 23.7% (target 15, over), taste 16.8, social 11.4 (over), values 11.0, evaluative 5.2 (short),
  personality 3.4 (short), perception 0.8, forecast 0.4. Wave 2 therefore holds back World factual (MedMCQA, CommonsenseQA
  are written but not ingested) and adds personality and evaluative.

**Tree at the gate**
- Template split: 19 nodes, 35 template children (Machine dataset templates, six pairwise taste sets, topical World fact
  templates). Single-template nodes stay whole (template cap governs).
- Descend: 27,589 hint-placed questions on 11 overfull parents re-walked by Jev from the parent; e.g. self.personality kept 73 of
  1,945, self.values 375 of 2,632, biology_genetics 229 of 2,452.
- Cluster splits (labels authored, Jev re-route, accept rules): **accepted** social_stories → friends/peers + dating/partners,
  family_stories → spouses + parents/siblings/relatives, quick_social_judgments → dating/partners + friends/peers,
  reading_people → reading feelings + reading motives. **Rejected:** everyday_ethics (18% sibling moves) and self.love (80%).
- New node: `self.mind.reading_people` (3,787 Social IQa items that are social reasoning, not relationships; moved from self.love).
- `repair-paths`: 0 violations. Star layout regenerated (226,279 stars in 1,267 nodes).

**Known issues**
- Still over the node cap: self.values.everyday_ethics (~4.4k, split rejected), single-template nodes (pair sets, AITA, one-dataset
  Machine nodes; bounded by the template cap), world.places.cities (fact templates that aren't topics).
- The world thin-node bank (4,859 after dropping weak Score items) was still in its round trip at the gate; it counts toward wave 2.
- Throughput: Jev ran at ~75-80% of the rate budget (a gap between 5,000-question chunks); synthetic round trips at 3 rps are slow.
- Labels known to be noisy: resume_match (filing categories), github_issues, civil_comments sub-types, Devign-style sets.

## Wave 0: baseline (2026-09-24)
99,458 questions, 1,319 active nodes, 52,466 distinct question texts; 25% human-written question text,
36% real items in a template, 26% real machine inputs in a template, 12% synthetic. Full audit:
`docs/10-expansion.md` §1. Mix and per-source numbers: `docs/corpus.md`.
