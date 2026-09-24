# Experiments: finding jaggedness

Each experiment is a perturbation that shouldn't change a coherent judge's answer, or should
change it in a predictable way, measured across many items and reported **per tree node and
per kind/shape**, never as one overall number. The results feed the node indicators
(`02-tree.md` §1). `mined` questions feed findings but never personality claims.

Notation: `P(o | q, f, v)` = Jev's probability of option `o` for question `q`, frame `f`, variant `v`.

## 0. Baseline hygiene (run first)
- **Gateway shape:** confirm that `typesafe-ai/jev` via AI Gateway returns full `probabilities`,
  `confidence`, and the served version (`01-jev.md` §1).
- **Determinism:** send the identical request 20× and measure the spread. This is the noise floor
  every effect must beat. Repeats use an explicit `repeat_idx` in the request hash.
- **Batch invariance:** the same question alone vs batched with unrelated questions. TypeSafe says
  answers are identical; verify on our data.
- **Version:** log the served version on every call. Re-run a fixed 1k-item canary set whenever it
  changes, and never compare answers across versions.

## 1. Universes (systematic rewording)
A **universe** is a named, systematic transformation applied to a sample of the corpus. It's an
**overlay on the one tree, not a copy**: the same nodes, the same question ids, and different probe
text. Universes never add questions to the tree.

| Family | Example universes | How it's made | Expected relation to base |
|---|---|---|---|
| Length/register | `terse` ("few word do trick"), `verbose` (yapping), `formal`, `casual-slang`, `old-english`, `legalese`, `child-level` | LLM | **invariant** |
| Lexical noise | `synonyms`, `typos`, `lowercase-no-punct` | LLM or code | **invariant** |
| Form | `statement-form` (a Noul as a statement; the docs say to test both), `option-descriptions-added`, `option-labels-c0` | LLM or code | **invariant** |
| Language | `french`, `spanish`, `chinese` | LLM | invariant (TypeSafe says English is best, so expect drift and quantify it) |
| Random paraphrase | `paraphrase-1..k` | LLM | **invariant**; this is the old paraphrase experiment |
| Negation | `negated` (Noul only) | LLM | **should flip**: P → 1 − P (documented jaggedness #8, so quantify it only) |
| Leading | `leading` ("Many experts say A. ..."), `pressure` ("this really matters") | LLM | ideally invariant; measures suggestibility |
| Persona | `asked-by-child`, `asked-by-expert` | LLM | exploratory |

Each universe is versioned with its exact transform prompt or code. Frames (self/human) and option
shuffles stay in the answer bundle for *every* question, so they're not universes.

**Validity gate** (per transformed question):
- An LLM check ("same meaning, same options?"), plus a person spot-checking 30 per universe.
- Jev's own equivalence Noul ("Do these two ask the same thing?") is recorded too, but *not* used as
  the gate, because that would be circular. It's a finding in its own right: if Jev says two questions are
  equivalent but answers them differently, that's an incoherence.

Options keep stable ids across universes (only their text is transformed), so distributions compare
option by option.

**Scope:** a stratified sample (e.g. 5k questions across nodes and kinds) per universe, not the full
corpus. Jev cost is trivial; the LLM transforms dominate.

**Metrics per universe × node:** drift (TVD vs base), flip rate (argmax change), Score band shift, and,
for should-flip universes, the violation rate. They're stored in `universe_stats` and shown as the
sunburst recolored per universe.

**Output:** "which *kind* of rewording breaks Jev, and where". For example: stable in `terse` everywhere,
but `old-english` breaks Values & Morality.

## 2. Option order and labels
- k random option permutations. Option names as real text vs `c0..cN` names with the text in
  descriptions (names are sent to the model, so neither is neutral).
- Metrics: position bias (P(first option) when content is randomized), TVD across permutations.
- It's cheap (no LLM), so it runs on every item as the default stability signal.

## 3. Symmetry
TypeSafe documents P(q) + P(not q) ≠ 1 (`01-jev.md` §6 #8). **Quantify it by node and kind; don't
claim it as a discovery.**
- Pairwise "A or B?" asked in both orders: `P(A | A,B) + P(A | B,A)` ≈ 1?
- Noul "Is A better than B?" vs "Is B better than A?"

## 4. Transitivity and rankings
G3 pairwise sets (NBA first: top 50, both orders, 2,450 calls). Count preference cycles vs a
random baseline. Fit Bradley-Terry → "Jev's GOAT list" with uncertainty. A poor fit is itself a
finding. TypeSafe claims pairwise reranking but never demonstrates it.

## 5. Context effects (decoy / IIA)
A vs B, then A vs B vs a dominated decoy C. Does P(A)/P(B) move? Add an irrelevant option D and
check whether the ratio holds (Luce). Humans violate this; does Jev, and in the same direction?
Report effect-size distributions across many triples.

## 6. Frame gap
The same item as "Which do you prefer?" vs "Which would most people choose?" Where do the two diverge?
This separates Jev's defaults from the population it models.

## 7. Jev vs humans
Overlay Jev's human-frame distribution on real human data (surveys × country, Open Psychometrics
norms, WYR votes, Moral Machine by country, Scruples votes). Metrics: TVD / Jensen-Shannon; Score
band agreement. Slice by country where available.

## 8. Calibration (ground truth)
Reliability curves and Brier score **per L1 / L2 node and per Machine shape** on factual items (G4,
TruthfulQA, trivia), machine datasets, and resolved Manifold markets (Jev vs market vs outcome).
Framed as "where Jev's confidence means what it says", never as a leaderboard. This fills a gap:
TypeSafe publishes no calibration metrics.

## 9. Cross-primitive and scale consistency
- The same underlying judgment as a Noul ("Is X good?"), a Score ("How good is X?"), and a pairwise
  Choice. Noul vs yes/no Choice is already documented, so focus on **Score ordering vs pairwise
  Choice**, which isn't.
- The same question as a 5-level vs 7-level vs 10-level Score: is the median band consistent?

## 10. Tree routing
- Known-path taxonomies (CPC, Shopify, MeSH, SIC): accuracy by depth.
- Subtree-sample option values vs opaque `c0..cN` keys (the docs disagree on which to use).
- Placement stability across universes: questions whose transformed versions land in different L1s.

## 11. Metacognition: does Jev know where it's jagged?
Correlate Jev's self-assessment (`03-questions.md` §8: `ambiguous`, `disagreement`, `objective`)
with measured values (shuffle stability, universe invariance, human entropy, calibration), per node and per kind.
For a subset, also run the answer self-check (Noul "Is this answer reasonable?" over Jev's own answer)
and compare it with correctness. If self-assessment predicts failure, it can drive routing and review
thresholds, which is directly useful to TypeSafe's customers.

## Finding format
```
Finding: <one line>
Where: <nodes / kinds / shapes>, N items
Effect: <magnitude with CI>
Noise floor: <from exp. 0>
Repro: <exact request JSON + served model version>
Human / truth comparison: <if any>
Hypothesis: <why, and what a general fix might look like>
```
