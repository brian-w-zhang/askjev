# world_trolley_countries

family: world

## Why ask this
The trolley problem comes in versions. Would you pull a lever to send a runaway trolley onto a side track, killing one worker instead of five? Most people say yes. Would you push a large man off a footbridge to stop it? Most say no, though the arithmetic is the same.

In 2020, a team led by Edmond Awad asked 70,000 people in 42 countries all three classic versions (the switch, a looped track, and the footbridge) on the Moral Machine website. The order was the same everywhere, but the levels differed: people in East Asian countries were less willing to sacrifice anyone in every version. Knowing the order is textbook knowledge; knowing the variation is knowing people.

## The people and the data
Visitors to the Moral Machine website from 42 countries with at least 200 answers to each dilemma, from the study's public data: 230,475 answers in all.

## What Jev was asked
Two kinds of questions. Per country and dilemma, the share of visitors who would sacrifice the one (in 5% steps). And the three dilemmas put to Jev itself:

> A runaway trolley is heading down the track toward five workers, who will be killed if it goes on. You can pull
> a lever to switch the trolley onto a side track, where it will kill one worker instead of the five. Would you pull
> the lever?
> *Yes, I would pull the lever · No, I would not pull the lever*

That's 129 new questions, each asked with the options shuffled and averaged, and the three personal dilemmas also asked for what Jev thinks most people would say.

## How we measured it
For each dilemma, how well Jev's country estimates order the countries (rank correlation: 1 same order, 0 no relation, negative means reversed) and how far off they are on average; whether Jev keeps the universal order (switch above loop above push) in every country; and Jev's own answer against the pooled share.

## Caveats
- **Not national samples.** The answers come from self-selected visitors to the Moral Machine website, an English-first site, not national samples. The study's authors say so too; "the share in Japan" means the share of Japanese visitors to that site.
- **Our wording.** The dilemmas were written for this project, paraphrasing the website's classic trolley pages; visitors saw the site's own text and pictures.
- **Small spread between countries.**
- **A textbook result.** The switch-versus-push contrast is one of the most taught results in moral psychology, so getting the order right is expected knowledge, not a sign of insight into people.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
