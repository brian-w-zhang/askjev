# Questions: tags, mix, generators, allocation, scale

Where questions go is `02-tree.md`. This doc covers what questions exist, how many of each,
and how they're made.

## 1. Tags (the axes that aren't the tree)
| Tag | Values |
|---|---|
| `kind` (World/Self) | personality, values, taste, evaluative, social, factual, forecast, perception |
| `shape` (Machine) | classify, detect, score, route, rank, verify, extract (TypeSafe's decision shapes) |
| `primitive` | noul, choice, score |
| `frame` | self, human, human@country; n/a for Machine |
| `origin` | dataset, template, wikidata-fact, typesafe-docs, synthetic, mined, asked |

**Terms used everywhere:** a **question** is one canonical question (text + options + optional
state) and is the unit the mix is measured on. A **probe** is what actually gets sent: question ×
frame × variant (shuffle, universe transform...). An **answer** is Jev's response to one probe.
| `has_truth` / `has_human` | ground truth / human distribution present |

| Kind | Asks... | Example |
|---|---|---|
| personality | What are you like? | "I get stressed out easily." (Score) |
| values | What's right? | "Swerve and save five pedestrians, or stay and save one passenger?" |
| taste | What do you like? | "Would you rather never eat cheese or never eat chocolate?" |
| evaluative | Is X good / overrated / hard? | "Most overrated Beatles album?" |
| social | What do most people think? | "What would most people in Japan answer?" |
| factual | What's true? (ground truth) | "Is a tomato a fruit?" |
| forecast | Will X happen? | "Will a human land on Mars by 2035?" |
| perception | How does X feel or seem? | "How much do you experience 'lemon' by taste?" |

`social` overlaps with the human *frame*. Any question can be asked in the human frame, and `kind`
describes the question itself.

## 2. Target mix (% of canonical questions; variants, probes, and duplicates don't count)
| Kind / shape | Target | Floor / cap |
|---|---|---|
| personality | 9% | floor 7% |
| values | 10% | |
| taste | 15% | floor 10% |
| evaluative | 9% | |
| social | 8% | |
| factual | 15% | cap 20%; categorical only (is-a, part-of, which-of-these, misconceptions); no numbers or dates |
| forecast | 1% | |
| perception | 3% | cap 5% |
| **World + Self subtotal** | **70%** | |
| Machine (all shapes) | 30% | no per-shape quota; driven by datasets, but every shape must appear |

Result: about 43% opinion/personality, about 40% with ground truth (factual + machine labels +
resolved forecasts), and about 20% with human distributions.

**Why factual gets 15%:** ground truth is the calibration axis ("when Jev says 80%, is it right
80% of the time, per topic?"). TypeSafe publishes no calibration metrics.

## 3. Generators (how a node becomes questions)
| # | Generator | Works on | Produces | Truth / human |
|---|---|---|---|---|
| **G1** | Dataset import | any node a dataset maps to | the dataset's items | often both |
| **G2** | Menu templates | nodes with ≥3 children or entities | Choice over children: favorite, best, most overrated, most underrated, hardest, most influential, "most people's pick" | none |
| **G3** | Pairwise | top-N entity sets | "A or B?" in both orders → Bradley-Terry ranking ("Jev's GOAT list") | none |
| **G4** | Wikidata facts | entity leaves | Noul/Choice from properties: "Is X in Africa?", "Which of these is a mammal?" (categorical only) | truth |
| **G5** | Synthetic bank | concept nodes ("Sleep", "First dates") | Claude Code subagents write closed questions for the node; Jev gates them (§5) | none |
| **G6** | Entity judgments | single entities | "Is X overrated?", "How good is X?" (Score) | none |
| **G7** | Machine templates | Machine template nodes | template × real input from a labeled dataset | usually truth |
| **G8** | Asks | anywhere | questions posed by users (`07-ui.md`) | none |

**Fill order at each node:** G1 → G4/G7 → G2/G3 → G6 → G5. Real data comes first, and synthetic
questions only fill what's left.

Large menus: "most overrated among 200 children" spreads probability mass thin. Cap menus at 50
(top by sitelinks) and use G3 pairwise for rankings.

## 4. Allocation (top-down budgets)
1. Choose the total N.
2. Split N by hemisphere (35/35/30), then by L1 share (`02-tree.md` §3).
3. Below L1, each child's share of its parent's budget is:
   ```
   w(child) = 0.4 · 1/n_children          # equal floor: every branch shows up
            + 0.4 · curiosity(child)      # normalized log pageviews of the subtree (World); 1/n elsewhere
            + 0.2 · human_data(child)     # boost where datasets give human or truth data
   ```
4. At each node, split the budget by the kind mix for that L1, and fill it in generator order.
5. **Stop rule:** don't go deeper once a node's budget drops below about 5. The budget stays at that
   node, which sets depth automatically at each N.

**Enforcing the mix:**
- Kind comes from `source.yaml` for single-kind sources, and from a Jev Choice over the kinds
  for mixed sources, spot-checked.
- The screen request's `disagreement` and `reveals_self` (§8) are used as sampling weights.
  Consensus questions are down-weighted.
- High-volume sources (Lancaster, Social Chemistry, ETHICS, AITA) are only ever sampled.
- Every pipeline run prints a **mix report** (kind/shape × hemisphere × source × has_truth/has_human)
  compared against the targets.

## 5. The synthetic method (the research contribution)
**Coverage-driven, round-trip-verified generation.** It's the kind of "infinite data" job TypeSafe
describes.
1. **Coverage map:** each node's deficit = its budget minus its current count.
2. **Propose:** Claude Code subagents (never a gateway model) write candidates for the most under-filled nodes. Its input is
   the node description, examples, sibling `not_for`, target kind and primitive, and the rules
   from `01-jev.md` §7. It oversamples by about 2×.
3. **Round-trip filter:** Jev must place each candidate back at the node it was written for,
   starting from the root. If it lands elsewhere, the candidate is off-target or ambiguous, so reject it. This
   needs no human labels.
4. **Quality Nouls:** is it well-posed and closed? Does it need numbers or dates? Is it politically
   contested? Will people disagree (for opinion kinds)?
5. **Novelty:** dedupe by embeddings (cosine > 0.9 within a node) and by exact hash across the corpus.
6. **Spot check:** read 50 random questions per 10k, and revise the prompts if the reject rate is > 10%.
7. **Two modes, tagged separately:**
   - `synthetic` fills coverage and counts toward the mix.
   - `mined` **seeks jaggedness**: keep candidates whose answers flip under shuffles or universes,
     then generate near neighbors of the flippers to find where the failure starts. These feed the
     findings and are **excluded from the mix and from personality claims**.

Pitch: "an automated jaggedness miner over a coverage tree."

## 6. Content filter (every pipe)
- IAB sensitive-tier tags + a Jev Noul classifier + an explicit blocklist: elections, parties,
  named politicians, abortion, guns, immigration, LGBTQ policy, religion vs state, race
  policy, Israel/Palestine, Ukraine/Russia.
- Never show partisan or ideology subgroup splits (MFQ norms, survey party crosstabs).
- Filter sexual, abuse, and self-harm content (AITA, Scruples, Social Chemistry, WYR).
- Hide the Moral Machine "Criminal" and "Homeless" characters and the Social Status scenarios.
- Filtered items are **flagged, not deleted** (`flags`, `display_ok=false`) and can still be measured.

## 7. Scale ladder (hemisphere ratios hold at every stage)
| Stage | What it adds | Depth | Synthetic share |
|---|---|---|---|
| **10k** (the first slice, ready for findings) | Tree through L2 (~200 nodes). Core datasets: IPIP, WYR, GlobalOpinionQA, Scruples, MFQ, Moral Machine sample. NBA pairwise. Machine seed: TypeSafe doc questions over their cookbook inputs + 2-3 labeled datasets. G2 on L2 nodes | L2-L3 | < 15% |
| **100k** | Vital L3-L4 (~10k nodes) with G2/G4/G6. Remaining core datasets (Open Psychometrics, SAPA, Manifold sample, surveys × country). More machine datasets. G5 banks for Self | L4 | ~30% |
| **1M** | Vital L5 + category depth + Wikidata leaves. G3 across about 20 GOAT categories. G4 at scale. High-volume datasets (Social Chemistry, AITA, Lancaster). Machine datasets at scale | L5-L7 | ~40% |

Cost at 1M:
- **Jev:**
  - World/Self: ~700k × ~3 questions each (frames + gates) × ~100 tokens ≈ 210M tokens.
  - Machine: ~300k questions × ~500-token inputs ≈ 150M tokens.
  - Total ≈ 360M tokens ≈ **$15**.
- **Authoring (G5 + universe transforms):** done by Claude Code subagents, so there's no gateway cost.
- **Time:** about 3-4M questions at about 20 per request ≈ 2-3 hours of Jev.

## 8. Per-question metadata and the answer bundle
Metadata comes from four sources. Only a small **core** is stored per question. Everything else lives in
experiment tables, which keeps the core from bloating.

| Group | Field | How it's produced | When |
|---|---|---|---|
| **Answer** (free, from the response) | `top`, `p_top`, `margin` (top1 − top2), `entropy`, `confidence` (Choice/Score) | computed from `probabilities` | bundle |
| | `top_h`, `p_top_h` | the human-frame probe (World/Self) | bundle |
| **Jev self-assessment** (Jev judging the *question*, not its answer) | `objective`: Noul "Does this question have a single correct answer?" | screen request | screen |
| | `disagreement`: Score "How much would thoughtful people disagree?" (World/Self) | screen request | screen |
| | `ambiguous`: Noul "Is this question ambiguous or underspecified?" | screen request | screen |
| | `reveals_self`: Noul "Would someone's answer reveal their personality or values?" (World/Self) | screen request | screen |
| **Measured** (needs extra probes or data, so Jev can't just be asked) | `stability`: agreement of the top answer across 3 option shuffles | shuffle probes in the same request | bundle |
| | `frame_gap`: TVD between self and human frames | from the bundle | bundle |
| | `human_gap`: TVD vs the human distribution | needs `human_dists` | after ingest |
| | `correct`, `brier` | needs `truth` | after ingest |
| | `universe_invariance`: mean agreement with base across invariant universes (`05-experiments.md` §1) | universe probes | second pass, sampled subsets only |
| | `noise`: spread across identical repeats | repeated requests | second pass, sampled only |
| **Placement** | `node_id`, `placement_conf`, `separation`, `runner_up` | the traversal | before the bundle |

**At most two requests per question**, because quota sampling (§4) needs the self-assessment
*before* deciding which candidates get answered:
1. **Screen request** (screen stage, every candidate): content-filter Nouls, weak-spot Nouls
   (needs numbers/dates?), the kind Choice, and `m_objective`, `m_disagreement`, `m_ambiguous`,
   `m_reveals_self`. All of these are about the question, so they're cheap and batchable.
2. **Answer bundle** (ask stage, sampled questions only): `a_self` + `a_human` (World/Self) +
   `a_shuf1..3` (self frame, options shuffled). About 5 probes with the same state, all independent.

For **asks** (no sampling step), both are merged into a single request.

Meta questions carry the judged question as a data field inside their `instructions` object
(e.g. `{question: "How much would thoughtful people disagree about the answer to `subject`?",
subject: <question + options>}`), so the state stays the question's context. Machine questions
skip the frames, `m_reveals_self`, and `m_disagreement`.

**Second pass** (only where it's needed): universe probes (after LLM transforms), identical repeats (noise),
conditional follow-ups (after the answer is known), and the experiment-only answer self-check
(state = question + Jev's own answer; Noul "Is this answer reasonable?").

**Why the self-assessment is worth storing:** it enables a metacognition test (`05-experiments.md` §11).
Does Jev's own `ambiguous` predict measured instability? Does `disagreement` predict human entropy?
Does `objective` predict calibration? In other words: does Jev know where it's jagged?
