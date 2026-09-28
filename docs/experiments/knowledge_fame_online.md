# knowledge_fame_online

family: knowledge

## Why ask this
Fame is a fact about people's attention, not about the thing itself. A model trained on text has seen the famous far more often than the obscure, so it should know fame well. Where it doesn't, its picture of what people care about is thin or out of date. Comparing historical figures with internet phenomena shows where that picture holds.

## The people and the data
Fame comes from two public sources. Pantheon (CC BY-SA 4.0) scores historical figures and athletes by how many language editions of Wikipedia cover them and how often they're read. For internet phenomena, we use English Wikipedia page views from 2023 to 2025 for memes listed in Wikidata (CC0).

## What Jev was asked
Two-option questions:

> Which internet meme is better known: "Benadryl challenge" or "Videobombing"?
> *Videobombing · Benadryl challenge: Internet challenge*

Each was also asked with the two options in the other order.

## How we measured it


## Caveats
- **Page views are a stand-in for fame.** Fame here is English Wikipedia page views (for memes) and the Pantheon popularity index (for historical figures). Both favor recent, English-language interest; a meme famous in Japan can look obscure.
- **Politicians left out.** Pairs flagged as political were excluded, which removes many of the most famous historical figures.
- **A moving target.** Meme fame is measured over 2023 to 2025. What Jev learned may reflect an earlier internet, when a different meme was on top.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
