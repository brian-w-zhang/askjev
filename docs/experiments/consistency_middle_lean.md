# consistency_middle_lean

family: consistency

## 1. Question
Jev's most likely answer on a rating scale is often the middle level. Is that a habit with every scale, or does it depend on what is being rated?

The middle-lean is already known (it's in the old ledger, and people have a milder version); what isn't known is where it switches on. If it follows the subject rather than the scale, it's a stance, not a tic.

## 2. Sourcing
Every rating question with an odd number of levels (3, 5 or 7), so a middle exists: 117,000 questions, grouped by the kind of question the tree assigns (taste, personality, evaluative, values, perception, social); for 14 sources, real people's answers to the same items.

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of questions whose most likely level is the middle one, by kind, with 90% bootstrap intervals; on the items with human data, Jev's middle share next to the people's.

## 5. Visualization
Dots per kind (share at the middle), and paired bars for the sources with people's answers.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.882, top verdict `headline`.

## Compared with
Real respondents on 14 sources (captions, jokes, personality items, taste ratings, norms, sound symbolism)

## Limits
Known pattern (old ledger `middle_lean`). Scales differ in wording across sources; five-level scales dominate. Kinds come from the tree and overlap sources.

Results: `data/analysis/experiments/consistency_middle_lean.json` (private). Code: `scripts/experiments/`.
