# world_ideal_day

family: world · new questions: 20

## 1. Question
Asked how it would spend an ideal day, how much time does Jev give to sleep, work, reading, TV and exercise, compared with how Americans actually spend theirs?

An ideal day is a compact self-portrait: what it would do more of, what it would drop. The gap from the diaries is the gap between aspiration and habit, the thing people report about themselves too.

## 2. Sourcing
New questions (sources/atus_day): 'On an ideal day for you, how much time would you spend <activity>?' for the same 20 activities and 9 bins. Compared with the ATUS diaries' weighted means (no human data on ideal days).

Sources: `atus_day`

## 3. Collection
20 new questions (self), each asked as written and with the bins in shuffled orders (averaged).

## 4. Scoring
Expected minutes per activity from bin midpoints; the difference from the diaries' mean; the total of Jev's ideal day in hours (a check that it adds up to about 24).

## 5. Visualization
Two stacked 24-hour bars, the diaries' average day and Jev's ideal day, colored by activity.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.971, top verdict `portrait`.

## Compared with
American Time Use Survey diary days, 2003-2016 (actual, not ideal, days)

## Limits
Ideal vs actual is not like for like; the comparison says where Jev's ideal departs from real life, not what Americans would call ideal. Activities overlap little but the bins are coarse.

Results: `data/analysis/experiments/world_ideal_day.json` (private). Code: `scripts/experiments/`.
