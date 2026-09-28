# polls_colors

family: polls

## Why ask this
Blue is the world's favorite color in almost every survey ever run. A favorite color is a tiny question, but it's a clean test of something bigger: does a model's taste just mirror the most common human answer, or does it have preferences of its own? Colors are also a case where there is no right answer to lean on, only taste.

## The people and the data
Two open datasets on favorite colors:
- A **2010 US online survey** by sociologist Philip N. Cohen, where 2,103 people picked their favorite from seven color swatches (purple, blue, green, yellow, orange, red and pink) or wrote in another.
- A **2021 study by Jonauskaite and colleagues** in Switzerland, where 323 adults named their favorite color in their own words, sorted into 13 categories.

Nobody in either study compared two colors directly. The 72 head-to-heads between 13 colors are built from single favorites: among people whose favorite was one of the two, what share chose each? A pair counts only if a survey has at least 20 such people, and uses whichever survey has more. Because the US survey offered only seven colors, every pair involving black, white, grey, brown, turquoise or yellow green rests on the Swiss study alone.

## What Jev was asked
Each pair of colors, by name:

> Which color do you like better: orange or yellow?
> *orange · yellow*

## How it was measured


## Caveats
- **Two small surveys pooled.** The people's side combines a 2010 US online survey and a 2021 Swiss study with 323 participants. Each pair uses whichever survey had more people answering it, so the "people" here are a mix of two very different samples.
- **Named, not shown.** Jev read color names; the US survey showed color swatches and the Swiss study asked people to name a favorite in their own words, later sorted into categories. "Turquoise" as a word and as a swatch aren't the same thing.
- **A small set.** Thirteen colors and 72 pairs are enough to see the big picture, not to rank the middle confidently.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
