# lexicon_emoji_sentiment

family: lexicon · new questions: 300

## 1. Question
Told only that a tweet contains a given emoji, how positive does Jev think the tweet is, compared with how annotators actually labeled the tweets that contain it?

Emoji carry a lot of the tone of online text, and some are used against their face value (😂 in complaints, 🙏 in pleas). A model that reads emoji by their picture will misjudge the tone of real posts.

## 2. Sourcing
New questions (sources/emoji_sentiment): 'A tweet contains the emoji X. Knowing only that, is the tweet more likely negative, neutral or positive?' for the 300 emojis found in 50+ labeled tweets of the Emoji Sentiment Ranking (Kralj Novak et al. 2015, 1.6 million tweets labeled by 83 annotators, CC BY-SA 4.0).

Sources: `emoji_sentiment`

## 3. Collection
300 new questions, each asked as written, for 'most people', and with the options in shuffled orders (averaged).

## 4. Scoring
Sentiment score = share positive minus share negative, for Jev's distribution and for the tweets' labels; rank correlation over emojis with a 90% bootstrap interval; how often Jev's most likely label is the tweets' most common one; the share Jev puts on neutral vs the tweets; the emojis read most differently.

## 5. Visualization
A scatter: the tweets' sentiment score (x) vs Jev's (y), one dot per emoji, the largest gaps labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 4.441, top verdict `portrait`.

## Compared with
Tweets labeled by 83 annotators in 13 European languages (Kralj Novak et al. 2015)

## Limits
The annotators labeled whole tweets, not the emoji; Jev sees only the emoji. Tweets are from 2013-2015 and in 13 languages.

Results: `data/analysis/experiments/lexicon_emoji_sentiment.json` (private). Code: `scripts/experiments/`.
