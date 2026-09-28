# influence_crowd_share

family: influence

## Why ask this
Most of what this project learns about Jev's picture of people comes from asking what "most people" would say. That tells you which option it thinks wins, not how lopsided it thinks the vote is.

## The people and the data
Real vote shares from two places: 150 Reddit polls from r/polls with at least 300 votes each, and 150 would-you-rather dilemmas from either.io, some with millions of votes. Both crowds are self-selected: people who chose to click on a poll, not a sample of the public.

## What Jev was asked
> People were asked: "Would you rather be responsible for saving the world and nobody knows or be responsible for
> destroying the world and EVERYBODY knows?" The options were "save it"; "destroy it". What share of them chose
> "save it"?
> *0% · 5% · 10% · ... · 100%*

## How it was measured
For each option, the middle of Jev's answer against the real share: the average distance in points, how well Jev orders the options by share (a rank correlation: 1 same order, 0 no relation), and how steeply its guess rises with the real share. Two baselines: always guessing an even split, and using Jev's own "most people" probability for the option as if it were a share.

## Caveats
- **Who voted.** The shares are those of r/polls voters and either.io visitors, self-selected online audiences. Jev was told "people were asked", not who they were, so part of its error may be picturing a different crowd.
- **Bins.**
- **One option per poll.** Each poll contributes one randomly chosen option, so a poll's other options aren't checked for adding up.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
