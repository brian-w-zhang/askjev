# work_what_jobs_are_like

family: work · new questions: 495

## 1. Question
How often does a nurse deal with angry people, a web developer face deadlines, a roofer work in the weather? Does Jev know what jobs are like, compared with what the people doing them report?

Models are asked about careers constantly. O*NET asks incumbent workers directly, so the gap between Jev and them is the gap between a job's reputation and its reality.

## 2. Sourcing
New questions (sources/onet_context): 12 O*NET Work Context items (angry people, conflict, weather, deadlines, public speaking, email, disease, sitting, freedom to decide, cost of mistakes, automation, competition) for 46 well-known occupations, with O*NET's own five answers; the human distribution is the share of surveyed workers choosing each (O*NET 29.0, CC BY 4.0).

Sources: `onet_context`

## 3. Collection
495 new questions (rows O*NET marks as unreliable are left out), each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Per item, rank correlation across occupations between Jev's expected level and the workers' mean level, and the mean gap (Jev minus workers) with a 90% bootstrap interval over occupations; the occupation-item pairs with the largest gaps.

## 5. Visualization
A dot plot, one row per item: the mean gap with its interval, and the rank correlation as a label.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.508, top verdict `portrait`.

## Compared with
US workers in each occupation (O*NET 29.0 incumbent surveys)

## Limits
O*NET answers come from samples of incumbents (median a few dozen per occupation); Jev answers about a typical member of the occupation.

Results: `data/analysis/experiments/work_what_jobs_are_like.json` (private). Code: `scripts/experiments/`.
