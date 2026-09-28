# reading_politeness

family: reading

## Why ask this
Tone is a large part of how people react to a message. A request can be granted or refused on its phrasing alone. A model that writes, rewrites and summarizes messages all day should hear politeness the way people do: the "please" and "thanks" that soften, the direct "you" and bare questions that don't.

## The people and the data
The Stanford Politeness Corpus (Danescu-Niculescu-Mizil and colleagues, 2013) collected requests Wikipedia editors wrote to each other on their talk pages and had five crowd workers on Amazon Mechanical Turk rate each one, from very impolite (1) to very polite (25). We took 500 of the 4,353 rated requests, 100 from each fifth of the politeness range, so polite and rude requests are equally represented.

## What Jev was asked
Each request on its own, with five described levels:

> One Wikipedia editor wrote the request *(below)* to another editor on their talk page. How polite is it?
> *"I noticed, that for users warned before, Huggle still uses level 1 warning. Is there anything I can do?"*
> *Rude: the other editor would feel insulted or attacked by it · Curt or pushy: noticeably impolite, though not
> insulting · Neutral: a plain request, neither polite nor impolite · Polite: considerate and courteous · Very
> polite: warm, gracious and deferential*

Each question was also asked with the levels in reverse order, and the two answers averaged.

## How we measured it
Jev's average level for each request against the raters' average score, ranked and compared (a rank correlation: 1 means the same order). As a yardstick, how well one rater's score matches the other four's average. Then the average and spread of Jev's ratings against the raters', and the requests where they differ most.

## Caveats
- **Not a fair ceiling.** Jev is compared with the average of five raters, while "one rater against the rest" compares one person with four. An average is steadier than any one person, so Jev's lead over a single rater is partly built in.
- **One kind of writing.** The requests are Wikipedia editors writing to each other on talk pages, a specific register full of editing jargon. Politeness at work, in texts or in customer service could read differently.
- **Our wording of the levels.** Raters used a 1 to 25 slider with only its ends described. Jev's five levels ("Curt or pushy: noticeably impolite, though not insulting" ...) were written for this project, and we cut the raters' scale into five even bands to compare.
- **Hidden requests.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
