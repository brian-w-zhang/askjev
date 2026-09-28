# The Jev self-evaluator

Jev decides whether each experiment clears the bar. The evaluator is `scripts/experiments/evaluate.py`; its outputs
are private (`data/analysis/experiments/_eval_*.json`). Version **v4**.

## What Jev is asked
Each experiment becomes a **card**: title, question, result, evidence (n, interval), what it's compared with, how it
was sourced, the chart in one line. No ids, nothing a reader wouldn't see.

1. **Verdict** (Choice, 10 options written as situations): wrong · trivial · duplicate · noise · muddled · needs data
   · solid but dull · atlas · portrait · headline. Each maps to a value (0, 1, 1, 2, 3, 4, 5, 6, 8, 10).
2. **Interest** (Score, 10 levels): from "a reader would skip past it" to "a reader would be talking about it tonight".
3. **Checks** (yes/no): real human baseline? surprising? jargon? readable once?
4. **Head-to-heads** (Choice between two cards, both orders): "Which one teaches a curious general reader something
   more surprising and specific about how the model behaves, clearly stated and backed by a real comparison?"
   Bradley-Terry strengths from these rank every experiment.

## How the outcome is decided (code)
The head-to-head strength decides, on a fixed scale set by the gold set (below). Every pool includes the 60 gold
items as anchors. Strengths are shifted so the **12 new-style gold cards** sit where they sat in the gold tournament
(v4; see "Running it on the experiments").
- **cut:** Jev's top verdict is `wrong` or `duplicate`, or strength < −3.0
- **rework:** top verdict `muddled` or `needs_data` and strength < 0 (one improvement pass, then re-evaluated)
- **keep** (portrait candidate): strength ≥ 0
- **atlas:** everything else

## How it was tuned
**Gold set:** 60 experiments labeled by Claude against Brian's bar (no slop; surprising over big; a real human
baseline; readable once): 48 old findings sampled across every section, and 12 cards in the new format written from
real portrait results. Labels: 13 keep, 28 atlas, 5 rework, 14 cut.

| Version | What changed | Exact agreement | Within one step | Rank correlation |
|---|---|---|---|---|
| v1 | verdict + interest + fair/baseline/artifact/plain checks, fixed thresholds | 25/60 | 38/60 | interest 0.47 |
| v2 | checks replaced (surprise, jargon); thresholds refit | 29/60 | 39/60 | – |
| v3 (pairs) | head-to-heads, generic "more interesting" | 38/60 in-sample, 55% held out | 48/60 | 0.54 |
| v3 | head-to-heads with Brian's bar spelled out | – | – | 0.58 |
| **v4** | v3, re-run after the corrected WHO-5 gold card; scale anchored on the new-style gold cards | – | – | **0.56** |

What the tuning showed:
- **The absolute answers are weak.** Interest scores bunch between 3 and 6.5 of 10; the yes/no checks hover near 0.5
  whatever the card says, except the human-baseline check (0.23 for cards the gold set cuts, about 0.7 otherwise).
  Absolute verdicts can't tell "an unusual topic on a metric" from a real result: jargon cards got `portrait`.
- **Comparisons work.** Jev commits when it compares. The head-to-head ranking puts all seven strong new-format cards
  first; its misses are old findings written tersely (a personality-type result, the middle-level habit) and Jev-only fun (the
  skunk), which the bar deliberately discounts.
- **Stable:** the absolute outcome was identical for 60/60 cards with the verdict options reordered; head-to-heads are
  asked in both orders so position bias cancels.
- **Held out:** thresholds fit on half the gold set and tested on the other half agree exactly 55% of the time
  (always guessing "atlas" would get 47%); the value is the ranking, and Brian picks from the top.

## The evaluator of the evaluator: do Jev's words match its numbers?
Asked what interest level each verdict word corresponds to, Jev spreads them across the scale in the right order:

| Verdict | Stated interest (1-10) | Mean interest when it actually gave that verdict |
|---|---|---|
| noise | 1.87 | 4.12 |
| duplicate | 2.38 | – |
| needs data | 2.86 | 6.20 (n=1) |
| solid but dull | 2.99 | 4.30 |
| atlas | 3.42 | 3.15 |
| muddled | 3.77 | – |
| portrait | 5.68 | 4.89 |
| headline | 8.45 | 5.15 |

Its words are bolder than its numbers: "headline" means 8.5 to Jev in the abstract, but the experiments it calls
headlines get 5.2. The same middle-of-the-scale habit the portrait shows (80% of ratings at the middle level),
turned on its own judgments, and the reason the evaluator ranks by comparisons instead of trusting the score.

## Baseline: the old 372 findings
Run through the same pool: **8 keep, 255 atlas, 109 cut** (v3); **9 keep, 254 atlas, 109 cut** under v4. The keeps are the Moral Machine comparisons and the Big Five
percentiles; the cuts are corpus counts, embedding themes and topic-indicator cards. The old findings have many
near-duplicate rows (nine Moral Machine lines), which the experiments merge into one each.

## Running it on the experiments
**The absolute line didn't hold for the new pool.** With v3's anchoring (all 60 gold items), 154 of the first 155
experiments came out `keep`: every experiment card is written like the new-style gold cards (question, evidence, what
it's compared with) and the terse old findings lose nearly every head-to-head to a detailed card, so the shift lifted
everything over the line. That is the same preference for detail the portrait sees in Jev's answers, turned on its
own judging. v4 shifts on the 12 new-style gold cards only (gold keeps average 1.1 on that scale, gold atlases −1.4,
so the keep line at 0 sits between them). It still keeps most: **134 keep, 17 atlas** of 151, and **175 keep, 17 atlas** of the final 192. Read the outcome as a
floor (nothing here is noise or a duplicate by Jev's judgment) and the **rank** as the signal: the atlas sorts by it,
and the portrait candidates are its top, at most two per family.

**Claude's sampled audit** (the other half of the meta-evaluation): the bottom 30 and the top 30 by strength were read
against their result files.
- The bottom agreed with the audit: three personality scales with no gap that clears the noise and a career code equal
  to the quiz-takers' average were cut (listed in `README.md`), the type letters and the favorites lists sit in the
  atlas.
- The audit found two bugs Jev couldn't see: the taste finals matched options to items by position, but options come
  back from the table key-sorted, which turned consistent choices into "22% of triads loop" (really 2%); and bootstrap
  intervals depended on the order experiments ran in, so re-running changed cards and reset their verdicts. Both are
  fixed; two full runs now give identical cards, and the corrected taste experiment
  (`taste_choices_vs_ratings`) replaced the wrong one. A self-evaluator ranks what it's shown; it can't check the
  numbers under a card, so the audit stays part of the loop.
