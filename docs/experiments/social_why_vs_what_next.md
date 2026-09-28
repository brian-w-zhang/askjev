# social_why_vs_what_next

family: social

## 1. Question
On 30,000 everyday social situations, does Jev read people's motives, their feelings, or what will happen next best?

Explaining an action after the fact and predicting its consequences are different skills; the gap says which way Jev's social sense points.

## 2. Sourcing
Existing Social IQa questions (Sap et al. 2019): a one-line situation and a question of one of about ten types (why did X do this, what does X need to do before, how would X feel, what will happen to X...), three answers, one marked right by crowd workers. Enough: 29,500 questions.

Sources: `social_iqa`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The share Jev gets right per question type, with 90% bootstrap intervals; grouped into looking back (motives, what was needed before), feelings and descriptions, and looking ahead (what happens next, what they will want next). Also Jev's stated probability against how often it is right.

## 5. Visualization
Dots per question type with intervals, ordered, colored by looking back / feelings / looking ahead.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.08, top verdict `portrait`.

## Compared with
Social IQa's crowd-validated answers (people agreed with the marked answer about 87% of the time in the original study)

## Limits
Answers are crowd-written, and some wrong answers are plausible; differences between types are a few points, so read them as a direction, not a gap in kind.

Results: `data/analysis/experiments/social_why_vs_what_next.json` (private). Code: `scripts/experiments/`.
