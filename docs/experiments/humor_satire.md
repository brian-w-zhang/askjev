# humor_satire

family: humor

## Why ask this
Satire works by reporting the absurd with a straight face. A reader who takes words at face value will miss some of it, and the headlines that fool them show which jokes are too deadpan to spot without knowing the source. It's also a practical skill: a model that summarizes the news should know when a story is a joke.

## The people and the data
The News Headlines Dataset for Sarcasm Detection (Misra, 2019) pairs headlines from The Onion, a satirical news site, with headlines from HuffPost, a real news site. There are no human judges: the label is simply where the headline was published.

## What Jev was asked
Each headline was a yes/no question, with both answers described:

> Is headline sarcastic?
> *(with the headline attached)* "local man dies following short battle with gas leak explosion"
> *Yes: the headline is satire: it mocks its subject by reporting something absurd or ironic as if it were news*
> *No: the headline straightforwardly reports or promotes a real story*

## How it was measured
Two error rates: the share of Onion headlines Jev calls straight news, and the share of real headlines it calls satire, each with a range for chance variation. Then Jev's accuracy when it's very sure (more than 90% on one side).

## Caveats
- **A known weak spot.** Reading the words rather than the intent is on TypeSafe's own list of Jev's limits. This experiment puts a number on it for satire; it isn't a new discovery.
- **Source stands in for sarcasm.** The labels come from where a headline was published, not from anyone judging it: every Onion headline counts as satire and every HuffPost headline as straight news. Some HuffPost headlines are wry on purpose ("let them eat cake!"), so a few of Jev's "mistakes" are fair calls.
- **No outlet, no capitals.** Jev saw each headline alone, lowercased as the dataset released it, with no outlet name or link. People reading the Onion know it's the Onion.
- **Dated, and filtered.** The headlines are from roughly 2014 to 2018. Political ones were flagged and hidden from the site by a content filter, which removes some of both outlets' output.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
