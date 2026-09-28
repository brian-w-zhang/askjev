# lexicon_emoji_sentiment

family: lexicon

## Why ask this
Emoji carry much of the tone of online writing, and they don't always mean what their picture shows. A 😂 can end a complaint, a 🙏 can plead, a 🔥 can praise a sandwich. A model that reads emoji by their face value will misjudge the tone of real posts, in moderation, customer messages or sentiment analysis.

Here is a clean test: a large set of real tweets whose tone was labeled by people, grouped by the emoji they contain. Jev is asked to guess the tone from the emoji alone and compare.

## The people and the data
The **Emoji Sentiment Ranking** (Kralj Novak and colleagues, 2015) comes from 1.6 million tweets in 13 European languages, collected in 2013-2015, whose tone was labeled negative, neutral or positive by 83 human annotators. For each emoji, the share of negative, neutral and positive tweets containing it is its "sentiment" in real use.

## What Jev was asked
> A tweet contains the emoji ⛔. Knowing only that, is the tweet more likely negative, neutral or positive?
> *The tweet is negative · The tweet is neutral · The tweet is positive*

## How it was measured
Each emoji gets a tone score, the share positive minus the share negative, for Jev's answer and for the tweets. The analysis compares them as a ranking (rank correlation: 1 means the same order), checks how often Jev's most likely label is the tweets' most common one, and lists the emojis read most differently.

## Caveats
- **Tweets from another era, mostly not in English.** The tweets were collected in 2013-2015 in 13 European languages. Emoji meanings drift fast: 🔥 and 💯 were only starting their careers as all-purpose hype, and a ⛔ in a 2014 tweet in Slovenian may not mean what it means in an English post today.
- **The annotators rated the tweet, not the emoji.** Each tweet was labeled as a whole, so a tweet's tone includes its words. Jev only saw the emoji. The tweets' score is how emojis were used, not what they "mean".
- **Popular emojis only.** Only the 300 emojis that appear in at least 50 labeled tweets were kept; the rest (669 more) have too few tweets for a reliable score.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
