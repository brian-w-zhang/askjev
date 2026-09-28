# world_typical_day

family: world · new questions: 20

## 1. Question
Pick an American at random on a random day: how long did they sleep, work, watch TV, exercise? Does Jev's picture of that day match 181,000 time diaries?

Time-use diaries are the least flattering mirror of daily life: most people don't work on a given day, most don't exercise, and TV takes more time than anything but sleep and work. A model's picture of 'a day' shows whether it knows the diary or the brochure.

## 2. Sourcing
New questions (sources/atus_day): for 20 activities, 'Pick an American aged 15 or older at random, on a random day of the year. How much time did they spend <activity> that day?' in 9 bins (none to 10+ hours). The human distribution is the weighted share of ATUS diary days (2003-2016) in each bin.

Sources: `atus_day`

## 3. Collection
20 new questions, each asked as written and with the bins in shuffled orders (averaged).

## 4. Scoring
Per activity: Jev's share on 'none' vs the diaries' (how often the activity doesn't happen at all), expected minutes from bin midpoints vs the diaries' weighted mean, and similarity of the distributions; the activities Jev most over- and under-states.

## 5. Visualization
Paired rows per activity: minutes per day, diaries (ink) and Jev (magenta), with the share of days at zero.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.115, top verdict `portrait`.

## Compared with
American Time Use Survey diary days, 2003-2016 (BLS; weighted)

## Limits
The diaries end in 2016; screen time has grown since. Bin midpoints make minute estimates rough; the zero shares are exact. Diary categories are narrow: 'relaxing and thinking' (ATUS 120301) and 'phone calls, mail and email' (16) count only time coded as that main activity, which Jev's broader reading can't know.

Results: `data/analysis/experiments/world_typical_day.json` (private). Code: `scripts/experiments/`.
