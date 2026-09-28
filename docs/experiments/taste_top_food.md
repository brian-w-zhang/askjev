# taste_top_food

family: taste

## Why ask this
Everyone has a food personality: sweet tooth, cheese person, spice seeker, picky eater. A model has never tasted anything, so its "favorites" can only come from what it has absorbed from how people write about eating: menus, recipes, reviews and dares.

## The people and the data
No people here: Jev against its own opinions.

## What Jev was asked
Every food one at a time, with five answers describing what you'd do:

> How much do you like the taste of plums?
> *You'd spit it out · You'd eat it only hidden in another dish · You'd eat it whenever it's served · You'd buy it for
> yourself regularly · You'd seek it out and eat it often*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated foods then played a round-robin final: 276 games of "Which would you rather eat or drink?", each asked with the two names in both orders.

## How it was measured
A food's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **A list written by another AI.** There's no public catalog of "foods you'd like", so the dishes, ingredients, cheeses and drinks were written for this project by Claude. What's on the list shapes what can win.
- **Some items sound better than others.** Most items are just names ("plums"), but a few are phrased as experiences ("being offered churros with chocolate"). A scene can sound more appealing than a bare noun, which may help those items.
- **A model can't taste.** Jev has never eaten anything. Its picks come from how food is written about: dessert and comfort food get warm prose, and fermented shark gets horror stories.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
