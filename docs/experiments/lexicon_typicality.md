# lexicon_typicality

family: lexicon

## Why ask this
Not all members of a category are equal. A robin is a better example of a bird than a penguin; an apple is a better fruit than an olive. Psychologists call this **typicality**, and it shapes how people learn words, draw conclusions and pick examples. Abstract categories have it too: joy is a better example of an emotion than boredom.

A model that ranks members differently from people will reason about categories differently: it will pick odd examples, or treat a borderline case as central.

## The people and the data
The ratings come from the **category norms** of Banks, Wingfield and Connell (2023). UK adults recruited online rated, from 1 ("very poor example") to 5 ("very good example"), how good an example each member was of its category, with at least a dozen raters per item.

## What Jev was asked
> How good an example of a social relationship is mother?
> *A very poor example: most people wouldn't think of it as one at all · A poor example: it belongs, but only at the
> edge of the category · A middling example: clearly in the category but not what people picture · A good example:
> one of the first few people would think of · A very good example: the textbook case people picture first*

Each member was asked as written, for "most people", and with the five levels reversed.

## How it was measured
Whether Jev ranks the members in the same order as people's averages (a rank correlation: 1 means the same order), overall and separately for concrete and abstract categories, with 90% intervals. Then the members whose rank moves most between the two.

## Caveats
- **People's side is an average only.** The study published only the average rating per item, from at least 12 adults each, so the comparison is of rankings, not full answers. With a dozen raters, individual averages are noisy.
- **The answer levels.** People rated on a plain 1-to-5 scale from "very poor example" to "very good example". Five described levels were written between those ends ("one of the first few people would think of", "the textbook case people picture first"). Tying typicality to what people "picture first" may push Jev toward the most famous members.
- **Two different scales.** Jev's answers sit on a 0-4 scale and people's on 1-5, so only the rankings are comparable; the named examples are the members whose rank moves most.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
