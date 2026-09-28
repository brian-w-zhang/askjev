# polls_reddit

family: polls

## Why ask this
r/polls is a Reddit community where people post simple questions with a few answers and everyone votes: bath or shower, cats or dogs, favorite season, would you give up your phone for a million dollars. It's the largest open record of everyday preferences with real vote counts attached.

A model that talks to millions of people carries a picture of "most people" around with it. Guessing poll winners across tens of thousands of polls shows where that picture is detailed and where it's thin.

## The people and the data
Native Reddit polls from r/polls, posted from 2020 to 2024 and collected from Arctic Shift, a public Reddit archive, each with its archived vote counts. The voters are whoever was browsing the subreddit: mostly young, online and English-speaking.

## What Jev was asked
Each poll exactly as posted, with its options, asked two ways: what Jev itself would pick, and what it thinks most people would say. For example:

> Do you prefer swimming in salt water or fresh water?
> *salt water · fresh water*

279 people voted on that one: 77% fresh water.

## How it was measured
Jev's guess of what most people would say is checked for whether it names the option that got the most votes. Because polls have different numbers of options, Jev's hit rate is compared with what a random guess would get (one divided by the number of options). The same is done per topic, for topics with at least 40 polls.

## Caveats
- **Reddit is not "most people".** The voters are r/polls users: mostly young, online and English-speaking, and they vote on whatever reaches the front of the subreddit. Jev was asked what "most people" would say, which is a different crowd.
- **Joke options and small polls.** Reddit polls often include a joke answer or a "see results" option (the latter was dropped), and only polls with 100 or more votes were kept, so a few percentage points of any poll are noise.
- **Topics are the project's grouping.** Each poll was placed in a topic of the project's question map automatically; a poll can land in a topic that fits it only loosely, and topics with fewer than 40 polls aren't compared.
- **Politics left out.** A content filter hides political and sensitive polls from the site, and they aren't counted here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
