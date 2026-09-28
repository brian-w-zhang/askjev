# taste_vs_audience_book

family: taste

## Why ask this
Books have a huge, opinionated audience. Comparing Jev's ranking with real readers' ratings shows whether a model that has read about every one of these books likes the same ones the people who actually read them do.

## The people and the data
Goodreads readers, via goodbooks-10k, a public dataset of Goodreads ratings from 2017: millions of ratings of the site's most-rated books. For each book we use the distribution of its star ratings, set on the same five levels Jev answers on.

## What Jev was asked
Every book one at a time:

> How much would you enjoy reading Shift by Hugh Howey?
> *You'd put it down after a chapter or two · You'd finish it out of duty and forget it soon after · You'd enjoy it
> once and not reread it · You'd recommend it to a friend · You'd reread it and count it among your favorite books*

Each was also asked with the answers reversed, and the two averaged. Jev never saw the Goodreads ratings.

## How we measured it
Ranks, because Jev's described levels and people's stars aren't the same scale.

## Caveats
- **Fans rate what they chose to read.** Goodreads users rate books they chose, often books they already expected to love. A devotional text or the fourth book in a romance series gets rated mostly by its fans; Jev rates everything cold. Much of the gap below comes from that.
- **Stars squeezed into five levels.** Goodreads uses 1 to 5 stars; we set each star on one of our five described levels to show them next to Jev's. We compare ranks, not levels.
- **A popular-books list from 2017.** The books are goodbooks-10k titles with at least 2,000 ratings, a popular, English-language list frozen in 2017.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
