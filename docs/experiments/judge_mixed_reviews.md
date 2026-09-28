# judge_mixed_reviews

family: judge

## Why ask this
Most real reviews are mixed: it's pretty, but thin; easy to use, but it broke after two years. How a reader weighs the gripes against the praise decides everything downstream: the summary a model writes, the ticket it routes to support, the rating it infers when there isn't one.

People have a known negativity bias; bad news weighs more than good. The question is whether Jev reads a mixed review as the writer meant it, or hears the complaints louder.

## The people and the data
Two kinds of reviews, each with the writer's own verdict:
- **Amazon:** reviews from Amazon's public multilingual review corpus (English part), balanced to 1,000 reviews per star rating, with the writer's 1 to 5 stars.
- **Steam:** English reviews of video games from Steam's public store, each with the player's own thumbs up (would recommend) or thumbs down.

## What Jev was asked
For Amazon, one question with five described levels:

> How satisfied is the reviewer in [review]?
> *The reviewer considers the purchase a failure and warns others away from it · The reviewer is let down: the
> product fell short in ways that matter to them · The reviewer is torn: the product has real upsides and real
> downsides for them · The reviewer is pleased with the product, with a minor reservation · The reviewer is
> delighted and recommends it without reservation*

For Steam, a yes/no question: does the player who wrote this review recommend the game?

## How we measured it
We line up the five levels with the five star ratings (1 star = "a failure", 3 stars = "torn", 5 stars = "delighted") and average Jev's reading for each star rating. The telling group is 3-star reviews: how many does Jev push down to "let down" or "failure", and how many up to "pleased"? On Steam, we count the mistakes in each direction.

## Caveats
- **Stars are a summary, not the answer.** A star rating is the writer's own verdict, but people use stars differently: some give 3 to anything they wouldn't buy again, some to anything that works. Jev's reading of the text can be reasonable and still differ.
- **Our five levels.** We wrote the five satisfaction levels ("let down", "torn", "pleased with a minor reservation"...) and mapped 3 stars to "torn". If writers use 3 stars for "disappointed", the level we called the answer is off, not Jev.
- **Two different sites.** Amazon reviews come from a research release with 1,000 reviews per star rating; Steam reviews are English reviews of about a thousand games, at most 8 per game. Neither is a random sample of what people write.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
