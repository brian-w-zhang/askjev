# Datasets: every source, with a verdict

> **What is actually ingested** (counts, licenses, truth/human coverage) is generated in `docs/corpus.md`
> (`scripts/corpus_report.py`). WVS/ESS/GSS microdata and PhilPapers are not ingested yet; Moral Machine is queued for wave 2.

**License posture: private project** (`00-vision.md`). Non-commercial and unclear-license data is
usable. Sources are **excluded** only where the terms ban AI/ML *use* or scraping: YouGov,
Kalshi, either.io. If the project ever goes public, re-review everything, using the License column.
Record the license on every item.

**Verdicts:** **Core** = in the 10k slice · **Use** = ingest fully · **Sample** = capped subset ·
**Maybe** = later · **Skip**. "Not yet researched" = the license and details are unchecked.

Licenses marked (v) were read at the source on 2026-09-24. Not legal advice.

## Self: personality
| Dataset | What | Size | Human data | Kind | License | Verdict |
|---|---|---|---|---|---|---|
| **IPIP item pool** | "I am the life of the party"-style statements | 3,320 items | none alone | personality | Public domain (v) | **Core** |
| **Open Psychometrics raw data** | ~45 instruments: Big Five, HEXACO, 16PF, Dark Triad, NPI, RIASEC, DASS... | ~2-5k items, 1M+ respondents | full per-item distributions | personality | none stated on the data page | **Use** (100k); drop RWAS (political) |
| **SAPA Project** (Harvard Dataverse) | SPI-135 + IPIP items | ~700 items | full distributions | personality | CC0 (v) | **Use**; skip ICAR (cognitive) |
| **Johnson IPIP-NEO-120/300** (OSF tbmh5) | Big Five facets | 120 / 300 items | full distributions | personality | items PD; data unstated | **Use** |
| **OEJTS** | MBTI-style bipolar pairs | 48 items | none | personality | CC BY-NC-SA 4.0 (v) | **Use** ("Jev's MBTI type") |
| **Global Preferences Survey** | risk, patience, altruism, trust, 76 countries | ~12 items | per country | personality | not yet researched | **Maybe → likely Use** |

## Self: values and morality
| Dataset | What | Size | Human data | Kind | License | Verdict |
|---|---|---|---|---|---|---|
| **Moral Machine** (OSF 3hvt2) | self-driving dilemmas | 40M decisions, 233 countries | per-country choice shares | values | none set on OSF | **Core** (sample); code renders scenarios as text |
| **Scruples Dilemmas** | "Which is less ethical, A or B?" | 10k pairs (+40k) | 5 annotator votes | values | Apache-2.0 repo | **Core** |
| **MFQ-30 / MFQ-2** | moral foundations | 30 / 36 items | published norms | values | "All rights reserved" | **Core** (private OK); item-level only, never partisan norms |
| **Awad 2020 trolley** (OSF qxjvh) | 3 trolley variants | 70k people, 42 countries | per country | values | none set | **Use** |
| **Scruples Anecdotes** | AITA posts + verdict counts | 32k | verdict counts | values | Apache-2.0 repo (Reddit text) | **Use** |
| **MoralExceptQA** | "Is it OK to break this rule here?" | ~150 | % accept | values | none in repo | **Use** |
| **AITA datasets** (HF) | raw r/AmItheAsshole + verdict | 100k-1M | verdict (sometimes votes) | values | Reddit content | **Sample** (~20k) |
| **ETHICS** | acceptable / unacceptable scenarios | ~130k | binary labels | values (near-factual) | MIT | **Sample** (~5k, as a control) |
| **Social Chemistry 101** | rules of thumb | ~290k | worker "% agree" bucket | social | CC BY-SA 4.0 (v) | **Sample** (~20k); human frame only |
| **PhilPapers Survey 2020** | ~100 philosophy questions, ~1,800 philosophers | ~100 | expert distributions | values | not yet researched | **likely Core** for Mind & Philosophy |
| **DailyDilemmas** | GPT-written value conflicts | 1,360 | none | values | CC BY 4.0 (v) | **Maybe** |
| **Moral Stories** | norm → moral / immoral action | 12k | none | values | MIT | **Skip** (answer obvious by construction) |

## Self: taste and preference
| Dataset | What | Size | Human data | Kind | License | Verdict |
|---|---|---|---|---|---|---|
| **Would-you-rather** (Kaggle charlieray668 = HF tasksource/wouldyourather) | two-option dilemmas with votes | 2,722 | absolute votes | taste | "CC0" claimed, but scraped from either.io | **Core** (private use; we didn't scrape it); filter sexual items |
| **Jester** | jokes rated −10..+10 | 100-150 jokes, 4M ratings | rating distributions | taste | research use | **Use** |
| **MovieLens** | movie ratings | 25M+ | rating distributions | taste | not yet researched (GroupLens terms) | **Maybe → likely Use** (a human anchor for film GOAT) |
| **AskReddit titles** | real "favorite / would you" prompts | large | none | taste | Reddit content | **Maybe**: seed topics for G5 and the coverage test |

## World: surveys (what people think, by country)
| Dataset | What | Size | Human data | License | Verdict |
|---|---|---|---|---|---|
| **GlobalOpinionQA** (Anthropic) | Pew GAS + WVS, pre-formatted multiple choice | 2,556 Qs | per-country distributions | CC BY-NC-SA 4.0 (v) | **Core** (start here) |
| **World Values Survey** | values: family, work, religion, trust, happiness | ~290 Qs/wave × 7, ~100 countries | respondent-level | non-redistribution (research use OK) | **Use**; politics filter (~30%) |
| **European Social Survey** | incl. Schwartz values (PVQ-21) | ~250 Qs/round × 11 | respondent-level | CC BY-NC-SA 4.0 (v) | **Use** |
| **Eurobarometer** Volume A xlsx | EU attitudes: science, AI, food, animals, well-being | ~100 Qs/wave × 100+ | per-country distributions | CC BY 4.0 (v) | **Sample** (Special EB topics; many items are awareness or EU policy) |
| **GSS** (NORC) | US attitudes since 1972 | ~6k variables | respondent-level | citation T&C | **Sample** (non-political modules) |
| **OpinionQA** (Pew ATP) | US opinion questions | 1,498 Qs | individual responses | Pew terms | **Sample** (lifestyle, tech, science items) |
| **ProtoQA** dev/test | "Name something people..." | ~1k × 100 answers | answer-cluster counts | CC BY 4.0 | **Use** |
| Afrobarometer / Arab Barometer / Latinobarómetro | regional values | varies | respondent-level | not yet researched | **Maybe** |
| SubPOP | subgroup opinions | 3.3k | per subgroup | gated, research only | **Skip** (value is partisan splits) |
| YouGov | | | | **bans AI/ML use** | **Skip** |

## World: factual (ground truth) and forecasting
| Dataset | What | Size | Truth | License | Verdict |
|---|---|---|---|---|---|
| **Wikidata facts** (G4) | categorical property checks | unlimited | ✅ | CC0 | **Core** |
| **TruthfulQA** (MC) | common misconceptions | ~800 | ✅ | not yet researched (Apache-2.0 believed) | **Use** |
| **OpenTriviaDB** | categorized trivia | ~4k | ✅ | not yet researched (CC BY-SA believed) | **Use** |
| **BoolQ / Natural Questions** | real Google queries (BoolQ is yes/no) | 16k / 300k | ✅ | not yet researched | **Sample** (the curiosity signal) |
| **Manifold** | prediction markets + resolutions | 100k+ | ✅ resolved + market prob | non-commercial dumps; API allowed (500/min) | **Sample** (~10k resolved, non-political, no date-dependence) |
| Metaculus | forecasting | ~20k | community prediction gated | view-only license | **Maybe** |
| Polymarket / Kalshi | | | | Kalshi **bans ML**; Polymarket mostly political | **Skip** |

## World: perception norms
| Dataset | What | Size | Human data | License | Verdict |
|---|---|---|---|---|---|
| **Lancaster Sensorimotor Norms** | "How much do you experience X by smell/sight/touch?" | 40k words × 11 dims | mean/SD | CC BY 4.0 (v) | **Sample** (capped by the perception cap) |
| Warriner valence/arousal | "How pleasant is 'X'?" | 14k words | mean/SD | not yet researched | **Maybe** (pick one word-norm set) |
| Brysbaert, Glasgow, ChaosNLI, SocialIQA, CommonsenseQA, Project Implicit | | | | | **Skip** |

## Machine: seeds and labeled datasets
**Seed (Core):** about 150 example questions from TypeSafe's docs and cookbooks, with their states
(digest §B: support triage, phishing decomposition, tool-call verification, guardrails,
insurance, moderation, extraction verification, RAG gating, citation check, date extraction...).
`origin = typesafe-docs`.

**TypeSafe cookbook datasets (Core; the digest §C has links and reported results):**
| Dataset | Use case (Machine L1) | Shape |
|---|---|---|
| CLERC legal citation retrieval (jhu-clsp/CLERC) | Search & Retrieval, Legal | rank |
| SEC 10-K Item 1 + SIC codes | Documents & Analytics | classify (hierarchical) |
| CPC patents, Shopify taxonomy, MeSH | Documents & Analytics; also tree-routing validation | classify (hierarchical) |
| GroNLP winemag reviews | Documents & Analytics (feature extraction) | score |
| Magellan Beer entity pairs | Documents & Analytics (entity resolution) | verify |
| NousResearch Hermes skills + requests | AI Systems & Agents (skill selection) | route |
| TrustAIRLab in-the-wild jailbreak prompts | AI Systems & Agents (guardrails) | detect |
| scrapegraphai-100k extractions | AI Systems & Agents (extraction verification) | verify |

**Labeled text-classification datasets (not yet researched; pick per Machine L2 to fill budgets):**
intent routing (Banking77, CLINC150), spam (SMS Spam Collection), toxicity (Jigsaw),
prompt injection and jailbreak sets, contract clauses (CUAD), claim verification (SciFact),
emotion (GoEmotions), systematic-review screening sets, product categorization, fake reviews,
resume-to-role, support tickets. The Hugging Face hub has thousands more. Selection criteria: real
inputs, trustworthy labels, and a clean mapping to one Machine L2 and one shape. Synthetic inputs
are a last resort, because their labels are just LLM opinions.

## Expansion sources (wave 1, 2026-09-24/25)
Added by the expansion (`10-expansion.md`); counts, truth and human coverage are in `docs/corpus.md`, per-wave numbers in
`docs/expansion-log.md`. **Verdict key for this table:** **Scale** = keep growing it · **Hold** = keep, don't grow
(template cap, weak signal, or noisy labels) · **Saturated** = Jev ≥ 95% correct and ≥ 60% decisive, stop growing.

| Source | Hemisphere / node | n | Anchor | Jev correct | Verdict |
|---|---|---|---|---|---|
| civil_comments (toxicity + harm kind) | Machine T&S toxicity | 4,500 | truth + rater share | 0.73 | **Scale** (informative) |
| halueval (QA, dialogue, summary grounding) | Machine AI answer grounding | 4,500 | truth | 0.76 | **Scale** |
| clinc150 (domain, in-scope) | Machine support routing | 3,500 | truth | 0.88 | Hold (template cap) |
| pii_detect | Machine personal data | 3,000 | truth | 0.92 | Hold (synthetic LLM texts; Ai4Privacy license: individuals only) |
| function_calls (ToolACE verify + pick) | Machine tool calls | 3,000 | truth | 0.96 | **Saturated** |
| arxiv_screen | Machine paper screening | 3,000 | truth | 0.91 | Hold |
| massive_en | Machine commands | 2,500 | truth | 0.90 | Hold |
| ledgar | Machine contract provisions | 2,500 | truth | 0.95 | Hold (near-saturated) |
| github_issues | Machine issue triage | 2,500 | truth | 0.73 | Hold (template cap; noisy labels) |
| phishing_email | Machine spam/phishing | 2,500 | truth | 0.97 | Hold |
| yahoo_topics, ag_news, dbpedia14 | Machine taxonomy | 5,000 | truth | 0.74 / 0.89 / 0.99 | Hold; dbpedia14 **Saturated** |
| skill_select (MetaTool) | Machine skill selection | 1,468 | truth | 0.87 | Hold (dataset exhausted) |
| resume_match | Machine resume categories | 1,000 | truth (noisy) | 0.61 | Hold (labels are filing categories) |
| mmlu | World factual (57 subjects) | 9,763 | truth | 0.93 | Hold (pool used) |
| arc, sciq, openbookqa | World science | 13,267 | truth | 0.99 / 0.97 / 0.95 | **Saturated** |
| strategyqa | World factual (implicit reasoning) | 2,000 | truth | 0.76 | Hold (dataset exhausted) |
| boolq (remainder) | World factual | +3,143 | truth | 0.79 | Hold (pool exhausted) |
| wikidata_g4 (8 fact + 7 comparison templates) | World places, people, science | 16,395 | truth | 0.96 | **Saturated** |
| quora_closed | World + Self, real asked | 5,549 | none | — | **Scale** (world side) |
| social_iqa | Self social | 10,000 | truth | 0.85 | Hold (social over target) |
| movielens / goodreads / boardgame / anime / music / beer pairs | Self taste | 25,000 | co-rater human share | — | Hold at the template cap; beer capped at 2,000 (obscure items) |
| moral_stories | Self values | 3,000 | truth | 0.91 | Hold (values over target) |
| scruples dilemmas (top-up) | Self values | +1,400 | n=10 votes | — | Hold |
| moralchoice | Self values | 1,366 | truth (low-ambiguity) | 1.00 | **Saturated** (low-ambiguity half) |
| daily_dilemmas | Self values | 1,360 | none | — | Hold (dataset exhausted) |
| ipip (full pool) | Self personality | +2,466 | none | — | Hold (pool exhausted) |
| openpsych (SWCPQ word pairs) | Self personality | +340 | human (n≈300k) | — | Hold |
| icar_sapa (EPQ-R) | Self personality | 80 | human | — | Hold |
| g5_w1 banks (lifestyle/love, mind/personality, world thin) | Self + World thin nodes | round-trip filtered | none | — | accept 71% / 49% / see log |

**Skipped:** recipe pairs (no public Food.com copy with recipe ids; ratings mostly ties), video-game pairs (no clean per-user
preference), SciERC (no public labeled copy), xLAM function calling (gated).

## Structure sources (the tree, not questions)
| Source | Role | License |
|---|---|---|
| **Wikipedia Vital Articles L1-L5** | World backbone (`02-tree.md` §5) | CC BY-SA 4.0 |
| **Wikipedia category dumps** | extra depth for selected World branches | CC BY-SA 4.0 |
| **Wikidata** | leaf entities, GOAT sets, G4 facts | CC0 |
| **Wikipedia Pageviews API** | curiosity weight | open |
| **IAB Content Taxonomy 3.1** | sensitive-topic tags + coverage checklist only | CC BY 3.0 (v) |

Tested Wikidata query (NBA players by sitelinks). Limits: 60 s timeout, 5 parallel queries per IP,
a User-Agent is required. **Correction (2026-09-24 build):** `rdfs:label` with `en` still returned no label for
LeBron James and Kevin Durant; the adapter takes labels from the Wikidata entity API with `en` then `mul`. WDQS
timed out and returned 502 and 429 during the build, so `sources/nba` falls back to the public QLever mirror (qlever.dev):
```sparql
SELECT ?item ?label ?sitelinks WHERE {
  ?item wdt:P106 wd:Q3665646 ; wdt:P118 wd:Q155223 ; wikibase:sitelinks ?sitelinks .
  OPTIONAL { ?item rdfs:label ?label FILTER(LANG(?label)="en") }
} ORDER BY DESC(?sitelinks) LIMIT 500
```

## Open actions
- [ ] Research the "not yet researched" licenses before ingesting each source
- [ ] Pick the Machine labeled datasets per L2
- [ ] Pick the Eurobarometer waves (Special EB: science, AI, food, animal welfare, well-being)
- [ ] Decide on the Moral Machine sampling unit (distinct scenario configurations)
