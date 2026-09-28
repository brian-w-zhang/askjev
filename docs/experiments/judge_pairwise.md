# judge_pairwise

family: judge

## 1. Question
Shown two AI assistant answers to the same request, does Jev pick the one human judges picked, and is it swayed by length or position more than they are?

Models are routinely used to judge other models. The known worries are a preference for longer answers and for whichever answer comes first or second; the useful question is whether that goes beyond what human judges already do.

## 2. Sourcing
Existing HelpSteer2 preference pairs (3 annotators each) and MT-Bench human judgments (experts and authors). Enough: about 2,300 pairs with a clear human preference. Answer lengths come from the full stored text.

Sources: `helpsteer2`, `mt_bench_human`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Agreement with the human preference (ties dropped); the share of choices going to the longer answer, binned by the length ratio, for Jev and for the judges; the share going to the first answer; agreement when the judges were unanimous vs split.

## 5. Visualization
Binned dots: length ratio of the first to the second answer (x) against the share choosing the first (y), Jev and human judges as two lines.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
HelpSteer2 annotators and MT-Bench expert judges

## Limits
Each pair is asked once, in the dataset's order; a swapped-order check needs new calls. MT-Bench conversations can be longer than Jev's 32k context allows in rare cases.

Results: `data/analysis/experiments/judge_pairwise.json` (private). Code: `scripts/experiments/`.
