# polls_reddit

family: polls

## Why ask this
r/polls is a Reddit community where people post simple questions with a few answers and everyone votes: bath or shower, cats or dogs, favorite season, would you give up your phone for a million dollars. It's the largest open record of everyday preferences with real vote counts attached.

A model that talks to millions of people carries a picture of "most people" around with it. Guessing poll winners across tens of thousands of topics shows where that picture is detailed and where it's thin.

## The people and the data
Native Reddit polls from r/polls, collected from a public Reddit archive for 2020 to 2024, each with its archived vote counts.

## What Jev was asked
Each poll exactly as posted, with its options, asked two ways: what Jev itself would pick, and what it thinks most people would say. For example:

> Do you prefer swimming in salt water or fresh water?
> *salt water · fresh water*

279 people voted on that one: 77% fresh water.

## How we measured it
We take Jev's guess of what most people would say and check whether it names the option that got the most votes. Because polls have different numbers of options, we compare Jev's hit rate with what a random guess would get (one divided by the number of options). We do the same per topic, for topics with at least 40 polls.

## Caveats
- **Reddit is not "most people".** The voters are r/polls users: mostly young, online and English-speaking, and they vote on whatever reaches the front of the subreddit. Jev was asked what "most people" would say, which is a different crowd.
- **Joke options and small polls.** Reddit polls often include a joke answer or a "see results" option (we dropped the latter), and we kept polls with 100 or more votes, so a few percentage points of any poll are noise.
- **Topics are our grouping.** Each poll was placed in a topic of our question map automatically; a poll can land in a topic that fits it only loosely, and topics with fewer than 40 polls aren't compared.
- **Politics left out.** A content filter hides political and sensitive polls from the site, and they aren't counted here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
