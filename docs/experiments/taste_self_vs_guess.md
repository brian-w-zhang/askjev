# taste_self_vs_guess

family: taste

## Why ask this
Ask someone whether they'd enjoy something and then whether most people would, and the gap tells you how they see themselves: pickier, more adventurous, more highbrow.

## The people and the data
No real people: both answers come from Jev. The items are the 12 taste domains in the corpus: films, books, board games, anime and beers from real rating catalogs (MovieLens, Goodreads, BoardGameGeek, MyAnimeList, BeerAdvocate), and music, food, places, art, nature, activities and culture from lists written for this project.

## What Jev was asked
Each item twice. Once as itself:

> How much would you enjoy watching Hud (1963)?
> *You'd turn it off within the first twenty minutes · You'd finish it but forget it within a week · You'd enjoy it
> once and not seek it out again · You'd recommend it to a friend · You'd rewatch it and count it among your
> favorites*

And once with the instruction "Do not give your own view. Choose the answer that most people would give (the most common human answer)", with the same question and answers.

## How we measured it
For each item, the gap is Jev's own level minus its level for most people, on the 0-to-4 scale. We average the gaps per domain, with a 90% interval from resampling items, and list the items where the gap is largest in each direction.

## Caveats
- **Both sides are Jev.** "Most people" here is Jev's own guess, not real people. This is a picture of how Jev sees itself against its idea of the crowd; the comparisons with real audiences are separate experiments.
- **Which "most people"?.** The question doesn't say which people. Jev probably imagines a broad, English-speaking public, and a different crowd (film buffs, Tokyo residents) would change the gap.
- **Lists written for this project.** Seven of the 12 domains (music, food, places, art, nature, activities, culture) use item lists written for this project by Claude, so the mix of mainstream and obscure items in them is our choice.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
