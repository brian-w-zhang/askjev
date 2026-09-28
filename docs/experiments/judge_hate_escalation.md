# judge_hate_escalation

family: judge

## 1. Question
Sorting social media posts into normal, offensive, or hate speech, does Jev put them on the same rung as the annotators?

The difference between offensive and hateful is the hard part of content moderation, and where the policy decisions live. A model that reads rudeness as hate will over-enforce in a specific direction.

## 2. Sourcing
Existing HateXplain posts (three annotators each, majority label), plus two cross-checks: Davidson et al. 2017 tweets whose annotators said 'neither', and DynaHate statements labeled implicit animosity. Enough: about 1,400 items. Harm-screened posts are not shown.

Sources: `hatexplain`, `hate_speech_offensive`, `dynahate`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
A 3x3 table of the annotators' majority label against Jev's most likely label; the share moved up a rung, down a rung, or kept; 90% bootstrap interval on the share moved up.

## 5. Visualization
A heat table: annotators' rung (rows) by Jev's rung (columns), with the step-up cells highlighted.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
HateXplain MTurk annotators (majority of 3); Davidson et al. CrowdFlower annotators; DynaHate labels

## Limits
The three-way labels come from each dataset's definitions, reworded as Jev options. Ties among three annotators are dropped.

Results: `data/analysis/experiments/judge_hate_escalation.json` (private). Code: `scripts/experiments/`.
