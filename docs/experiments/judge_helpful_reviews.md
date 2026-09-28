# judge_helpful_reviews

family: judge

## Why ask this
Online stores let shoppers vote on whether a review was helpful, and use the votes to decide which reviews to show first. It's one of the largest real records of people judging whether a piece of writing is useful.

If a model is going to sort or summarize reviews, its sense of "helpful" matters. A judge that finds everything helpful is a poor filter: it can't tell the review that explains the product from the one that just vents.

## The people and the data
Amazon reviews collected by researchers at UC San Diego (He and McAuley, 2016, reviews up to 2014), from seven categories including toys, groceries, baby products and tools. Each review carries its "Was this review helpful?" votes. The project kept 2,500 reviews with at least 10 votes (about 15 is typical) and a clear verdict: at least 85% of voters calling it helpful, or at most 40%. 60% of them were voted helpful.

## What Jev was asked
The review with its product category, star rating and title, then:

> Is [review] helpful to a shopper deciding whether to buy the product?
> *Yes: The review gives shoppers information that helps them decide · No: The review does not help shoppers
> decide*

For example, a 3-star review of a toy spaceship that reads, in full, "Loved the ship and its scale to the other ships I have. Miniature is a 6!!!!! Flight stand is a 3. Game system is a 3" got no helpful votes from 13 shoppers.

## How it was measured
A rank correlation (1 = same order, 0 = no relation) checks whether Jev at least orders reviews the way the votes do.

## Caveats
- **What the votes measure.** "Was this review helpful?" votes pile up on reviews that are shown early and often, and shoppers may vote "no" to disagree with a review rather than to say it's useless. So the votes are a noisy stand-in for usefulness.
- **Only well-voted, clear-cut reviews.** Reviews were kept with 10 or more votes and a clear verdict (85% or more helpful, or 40% or less), in seven product categories from 2014. Borderline reviews, and quiet ones nobody voted on, aren't here.
- **Jev sees the star rating.** Jev was shown the product category, the reviewer's star rating and title along with the text, which a shopper also sees. That's fair, but it means Jev isn't judging the text alone.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
