# polls_fandoms

family: polls

## Why ask this
Every fandom has inside opinions: the best arc, the worst contestant, the album real fans rank first. Those opinions are niche knowledge that shows up in a model's training data very unevenly, heavy for some communities and nearly absent for others.

So a simple test tells you something about Jev's cultural coverage: in which communities can it guess what the fans voted for, and where does it do no better than picking at random?

## The people and the data
Native Reddit polls, the kind where a member posts a question and the community clicks an option, from 35 hobby and fan subreddits (anime, games, rap artists, TV shows, tabletop games, sneakers, mechanical keyboards and more). They were collected from Arctic Shift, a public Reddit archive, for 2020 to 2024, each with its final vote counts. Only polls with at least 50 votes were kept (the median has 272). Polls flagged as political were dropped, and so were polls tied to a particular season, episode, chapter or upcoming release, and forecasts like "who will win", though a filter can't catch every poll about recent events.

## What Jev was asked
Each poll as posted, with its options, asking what most people would say. For example, from a Kingdom Hearts fan community:

> Which Kingdom Hearts handheld game do you think was the best?
> *recoded ds · 358 2 days ds · birth by sleep psp · dream drop distance 3ds*

(Poll options were stored as short labels, so Jev saw them in this plain form.)

## How it was measured
For each community, how often Jev's guess names the option that got the most votes, against what a random guess would get (one divided by the number of options).

## Caveats
- **Some polls are about things after Jev's training.** Fan polls about a new episode, season or album can concern events Jev never read about, and those are unwinnable. This probably hurts fast-moving communities (a reality show, an active artist) most.
- **Communities differ in size and style.** Only polls with 50 or more votes were kept; hobby polls are smaller than general ones (the median is 272 votes), so a single poll can be decided by a few dozen fans.
- **Each community is its own crowd.** Fans of a series vote as insiders, often against the general reputation. That's the point of the test, but it means "guessing wrong" here can mean "guessing what outsiders think".

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
