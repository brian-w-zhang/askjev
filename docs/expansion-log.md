# Expansion log

_One section per wave (`docs/10-expansion.md` §3). Newest first._

## Waves 7-9: 612k → 938k (gated together 2026-09-26)
**937,967 canonical questions** (+325,721), all placed and answered; 1,695 active nodes (+60); star layout regenerated.
Hemispheres: World 35.1 · Self 31.9 · Machine 33.0. Three overlapping ingests (Self real data, Machine's last round and
World thin areas, then new World/Self sources) were placed and answered together and gated as one.

| | Waves 7-9 | Rule |
|---|---|---|
| Anchored | 282,567 (**87%**) | ≥ 60% ✅ |
| Synthetic | 28,578 (9%): Self bank W7 (**57%** round-trip accept), World bank W10 (**55%**), ratings bank (**81%**) | ~15-20% guideline ✅ |

**Added.** Self (126k): Reddit polls to 60k (30k Self + 15k World), Social Chemistry +20k, Social IQa +15k, Moral Machine
+8k, Scruples, single-item taste ratings with real rating distributions (12,361; films, books, board games, anime, beer)
plus the authored ratings bank (7,013), StoryCommonsense 6k, Empathetic Dialogues and ISEAR 3k each, Stack Overflow
tool preferences 4k, 538 candy/cuisine, choices13k gambles, Wulff lotteries, the Basel-Berlin risk battery, the AIMS
AI-sentience survey. World (104k): wikidata_g4 to its full pool, Pantheon history 9k and athletes 2.7k, World Bank
country pairs 8.8k, Yahoo +8.8k, USDA nutrients 7k, CommonsenseQA 6k, AnAge animal pairs 5k, MedMCQA 5k, GOAT +3.6k,
Wikidata companies 2.8k. Machine (95.5k): the new Healthcare, Education and Operations L1s (clinical transcriptions, drug
reviews, ICD-10 chapters, liver labs, short-answer and math-answer grading, essay traits, Loghub, HDFS and Blue Gene/L
logs) and the last round aimed at ai_systems, trust & safety, people, code, search, support and research (39 datasets).

**Measurements.** Most informative Machine sets: HDFS anomalies 0.44 and ASAP essay traits 0.46 (never decisive), STS-B
0.47, deceptive hotel reviews 0.50, HelpSteer2 correctness 0.58, Dolly routing 0.60, ESCO titles 0.63, code comments 0.64,
CiteWorth 0.65 (never decisive). Saturated (≥ 95% correct, ≥ 60% decisive; frozen): wikidata_g4, Pantheon history and
athletes, Wikidata companies. Self emotion reading: ISEAR 0.69, Empathetic Dialogues 0.53 (32 overlapping labels).
Taste ratings are never decisive (0% p > 0.95), as expected for taste.

**Tree.** New hand node Self > Lifestyle > Ratings (12 domain children). Template split made 45 children: 5 for the real
Self sets (emotions in personal stories / life events, story character feelings / motives, gamble choices) and 40 on
the nine Machine nodes wave 8 overfilled (hallucination & citation had 10.7k direct; also extraction verification,
guardrails, logs & incidents, clinical notes, answer grading, toxicity, semantic lint, resume match). Meta splits for
Moral Machine scenarios and the candy, cuisine and developer-tool matchups. Descend re-walked 82,231 hint-placed
questions; 45k unhinted Reddit polls were placed with the fast path. Dedupe linked 1,255 duplicate pairs.

**Fixes.** Authored Self banks opened most lines with the trait they measure ("Manipulation: …"); the labels were
stripped from the queued banks and from 3,684 ingested questions, which were re-answered (`01-jev.md` §7). Loghub
OpenStack lines lost a file-name prefix that named the system. Candy taste pairs lost a crowd-majority "truth".

**Known issues.** Personality is 3.4% of World/Self against 9% (public item banks are exhausted; the W10 personality bank
is still in the round-trip queue). Split candidates left: dishes & ingredients 6.4k, family rules of thumb 6.2k,
everyday ethics 5.8k, self.love 5.7k, video games 5.6k, and Machine nodes at 2-4k stacking 2-3 templates. 2,110
questions sit at the root and ~2,100 at a hemisphere (fast placement found no confident branch).

## Waves 5-6: 478k → 612k (gated together 2026-09-25)
**612,246 canonical questions** (+133,839), all placed and answered; 1,635 active nodes (+67); star layout 612,737 stars in
1,600 nodes. Hemispheres at the gate: World 36.8 · Self 28.2 · Machine 35.0. The two waves overlapped (wave 6's ingest ran
during wave 5's placement so Jev never idled) and were gated as one.

| | Waves 5-6 | Rule |
|---|---|---|
| Anchored | 95,351 (**71%**) | ≥ 60% ✅ |
| Synthetic | 20,943 (16%): Self banks W5 and W6 (W6 **66%** round-trip accept) and TypeSafe-authored Machine inputs | ~15-20% guideline ✅ |

**Why Self is low at the gate:** these waves were Machine-heavy by plan (§9: fill the new Machine L1s and pull the anchored
share back after wave 4). Wave 7 is Self real data (Reddit polls to 60k, Social IQa, Social Chemistry, Moral Machine, Scruples);
with its ingest the corpus is 703,251 at World 34.1 · Self 35.4 · Machine 30.5.

**Added:** World: Stack Exchange second batch 24,320 (real asked questions, no anchor), Reddit polls 5,613, character traits
+4,000, Natural Questions yes/no 504. Self: Reddit polls 10,887 (voter-fact filter), Self banks 13,493, Young People Survey
869 and the MxMH, color-favorite, PISA, GSS, PhilPapers, Afrobarometer and GlobalOpinionQA items. Machine (74,081): LegalBench
11,820 across 7 tasks, TypeSafe-authored inputs 7,450 over 29 templates, LinkedIn job seniority and work type, CFPB complaint
product and issue, CoNLL/WNUT entity typing, ABCD customer flows, gold-news price direction, TREC-COVID pairs, SkillSpan, code
clones (BigCloneBench, POJ-104), SciCite, TREC question classes, Amazon review helpfulness, commit-message fit, SQuAD 2 spans,
evidence inference, FiNER XBRL tags, MultiWOZ domains, code-review need, WikiQA.

**Measurements:** most informative: code clones 0.54 correct while decisive 69% of the time (confidently wrong); LinkedIn
seniority 0.59; code-review need 0.60 and Amazon helpfulness 0.65, both never decisive; CFPB complaints 0.68. Saturated:
MultiWOZ domain 0.98 correct / 97% decisive (frozen). Stack Exchange titles are almost never decisive (3%), as expected for
open questions forced into closed form.

**Tree:** template split made 38 children: 10 in wave 5 (legal help areas, overruling, citation intent, clinical trial
effects, answer types, CUAD provisions, review helpfulness…) and 28 in wave 6 on the 11 nodes stacking several large
templates (machine.finance had 10.9k direct). Descend re-walked 29.5k hint-placed World/Self questions; 7,763 questions stuck
at root/hemisphere/L1 were re-walked with the beam; repair-paths clean; dedupe linked 540 duplicate pairs.

**Throughput:** requests pack up to 64 questions / ~5k tokens; the gateway is pinned to TypeSafe's own provider
(DigitalOcean returned 503s); adaptive rate backs off under 429s. TypeSafe's capacity (~850-950 successful calls/min) is the
ceiling, so placement and round trips ran near the 8 rps floor while the lane answered.

**Known issues:** the Moral Machine gender child holds 9.5k rows of one template (scenario rows, bounded only by the source);
23% of Reddit polls are hidden (biographical, demographic and political flags); everyday_ethics still has no accepted split.

## Wave 4: 373k → 478k (gated 2026-09-25)
**478,407 canonical questions** (+105,817), all placed and answered; 1,568 active nodes (+164); star layout 450,737 stars in
1,540 nodes. Hemispheres: World 40.0 · Self 30.7 · Machine 29.3.

| | Wave 4 | Rule |
|---|---|---|
| Anchored | 60,500 (**57%**) | ≥ 60% ❌ (missed by 3 points) |
| Synthetic | 6,702 (6%): Self taste bank, **84%** round-trip accept | ≤ 15% ✅ |

**Why the anchored share missed:** the wave took 30,000 Stack Exchange titles (the adapter's pool was extended to 30k by the
wave 5 sourcing agent before this wave's ingest read it) plus 4,000 chatbot first turns: real asked questions with no truth or
human data. Accepted and logged; `10-expansion.md` §8 now makes real asked questions a priority and allows the share to drift
to ~55-60%. Wave 5 is Machine- and survey-heavy to pull it back.

**Added:** World: Stack Exchange 29,995 (56 non-programming sites), fictional-character trait ratings 15,000 (each rater's
own slider rating, median n 81), 15 new GOAT categories 4,500, WildChat/hh-rlhf/oasst closed first turns 4,120. Self: Moral
Machine +10,000, Social IQa +5,000, Self taste bank 6,702. Machine (12 templates, 30,500): game-chat toxicity, Steam
recommendations, financial-tweet signals, competition-math subject and difficulty (model routing), PubMed RCT sections, MovieLens
"will this user enjoy", ESCI color extraction, QNLI answer gating, CoLA grammar, GoEmotions gratitude, clickbait, medical question pairs.

**Measurements:** most informative: MovieLens recommendations 0.71 (never decisive), math difficulty/subject 0.67, PubMed sections
0.72, CoLA 0.74, CONDA game chat 0.79. Saturated: ESCI color 0.97. Character traits are decisive 42% of the time and track the
rater majority closely on the obvious pairs.

**Tree:** template split for 3 Machine nodes; Moral Machine split by scenario type (women/men, young/old, fit/unfit, humans/pets);
character traits split into 155 per-work nodes ("Game of Thrones Characters"...); descend of 11,090 hint-placed questions; the lane
also left 34,115 unhinted Stack Exchange/WildChat questions answered but unplaced (ingest outran its place stage) — found at the
gate, placed with the fast path (hemisphere + nearest-node Choice) because the batch was > 20k; the lane now also counts unplaced
rows. Two hand nodes added for §8: Buying Decisions, Everyday Practical Questions.

**Known issues:** Jev's screen flagged about half of the Moral Machine rows where children die as sensitive, so they are hidden
from the map (still answered and measured); 1,673 real asked questions sit at the root (fast placement found no confident
hemisphere); split candidates left for a later pass: everyday_ethics, video_games, dishes_ingredients, coworkers, family
situations, psychology_neuroscience, Reading People children (all 1.6-2.2k direct).

## Wave 3: 300k → 373k (gated 2026-09-25)
**372,590 canonical questions** (+72,727), all placed and answered; 1,404 active nodes; 177,991 distinct texts; 195,737 with
ground truth; 116,391 human distributions; 783k cached Jev calls. Hemispheres: World 37.3 · Self 33.3 · Machine 29.4.

| | Wave 3 | Rule |
|---|---|---|
| Anchored | ≈ 80% (word norms, Moral Machine, humor ratings and taste pairs carry human data; ETHICS and Machine sets carry truth) | ≥ 60% ✅ |
| Synthetic | 8,729 (12%): world evaluative/perception/forecast bank 5,335 (**85%** accept), personality bank 3,394 (59%) | ≤ 15% ✅ |

**Added:** Self: Moral Machine +5,000, Humicroedit 5,000 and New Yorker caption contest 3,000 (humor with judge shares), goodreads
+2,000, ETHICS utilitarianism/justice 7,000. World: Lancaster +8,000, Glasgow norms 9,000, Brysbaert concreteness 3,000 (all with
human rating distributions), Yahoo closed titles 3,998, evaluative bank. Machine: ESCI match + pairwise, ContractNLI, PubMedQA,
fake job posts, PAWS, docstring match, financial news topics (18,000).

**Measurements:** perception rose from 0.7% to 5.3% (target 3); evaluative 5.7 → 8.1; factual 22.6 → 18.6. Word norms and humor are
almost never decisive (≤ 9%), so they measure agreement with human rating distributions rather than accuracy. Informative
Machine sets: ESCI 0.67, fake job posts 0.71, financial topics 0.76.

**Tree:** template split for 12 nodes (7 wave 3 Machine templates; humor → edited headlines + cartoon captions; utilitarianism →
Which Is More Pleasant; justice → Fair Justifications; docstring/language identification; paraphrase detection; word concreteness,
familiarity, arousal, pleasantness under Word); descend of 26,560 hint-placed questions (16k word-norm items from the World root).
Guard added: template split never adds children to the root or a hemisphere (two such nodes were created and folded back the same
hour, before any UI read them). `repair-paths` 0; star layout 347,814 stars in 1,342 nodes.

**Known issues:** everyday_ethics (~4.8k) and the Reading People children (~2k, question-type clusters) remain over the node cap;
1,870 generic word-norm items stay on the World root; Moral Machine grows to 18k in wave 5 and needs a split by scenario type first.

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
