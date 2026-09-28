# humor_new_yorker_captions

family: humor

## 1. Question
Rating captions entered in the New Yorker Cartoon Caption Contest, does Jev find funny the ones the contest's voters found funny?

The caption contest is the purest test of taste in jokes: same cartoon, a dozen captions, hundreds of voters each. If a model has a sense of humor, it should at least tell the better captions from the worse.

## 2. Sourcing
Existing questions ('How funny is this caption for the cartoon?', three levels: unfunny, somewhat funny, funny), with the cartoon described in words and the caption attached; each has the voters' unfunny / somewhat / funny split from the NEXT crowd-rating data (median 165 votes per caption). Enough: 2,915 captions from 224 contests.

Sources: `caption_contest`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Rank correlation between Jev's robust level and the voters' mean level, over all captions and within each contest (captions are only comparable against the same cartoon); how often the voters' favorite caption in a contest is also Jev's favorite, against the chance rate of 1 in the number of captions.

## 5. Visualization
A scatter of voters' mean level (x) against Jev's (y), one dot per caption, with the per-contest correlations as a strip below.

## 6. Evaluation
Jev's verdict (evaluator v3): **keep**, head-to-head strength 3.379, top verdict `headline`.

## Compared with
New Yorker Caption Contest voters (NEXT crowd ratings, about 165 votes per caption)

## Limits
Jev reads a text description of the cartoon, not the drawing; voters saw the drawing. Most submitted captions are unfunny to voters, so differences are small; the contest's published winners are not in this set.

Results: `data/analysis/experiments/humor_new_yorker_captions.json` (private). Code: `scripts/experiments/`.
