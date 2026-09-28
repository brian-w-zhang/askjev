# humor_upvote_guess

family: humor

## 1. Question
Shown two jokes from r/Jokes, or two captions on the same Imgflip meme, can Jev tell which one got more upvotes, and what does it do when it can't?

Upvotes are the internet's verdict on funny. A model that can't read that verdict falls back on something, and what it falls back on is itself a finding about how it chooses.

## 2. Sourcing
Existing pair questions ('Which joke, `joke_1` or `joke_2`, got more upvotes...'), each with the true answer from the post scores; which item is shown first was randomized when the pairs were built. Enough: 2,301 joke pairs and 2,655 caption pairs.

Sources: `rjokes_pairs`, `imgflip_captions`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of pairs where Jev's pick is the more-upvoted one, with 90% bootstrap intervals; share of pairs where it picks the item shown second, whichever is right; accuracy by Jev's confidence.

## 5. Visualization
Paired bars per set: accuracy when the right answer was shown first vs second, with 50% marked.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Reddit r/Jokes and Imgflip upvote counts

## Limits
Upvotes depend on timing and luck as well as quality. Reordering the answer options in the question doesn't change Jev's answer here; the lean is toward the item shown second in the text, which also carries the label ending in 2.

Results: `data/analysis/experiments/humor_upvote_guess.json` (private). Code: `scripts/experiments/`.
