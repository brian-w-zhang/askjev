# recall_mental_map_west

family: recall

## Why ask this
People store places in a hierarchy (city inside state inside country) and reason from the top down. So they place Reno east of Los Angeles, because Nevada is east of California, when Reno is actually farther west. The psychologists Stevens and Coupe described this in 1978.

A model that reasons the same way will be confidently wrong exactly where the shortcut fails, and people use models for quick geography all the time: which airport is closer, which way a road runs, what time zone a city is in. This experiment asked whether Jev takes the state shortcut, and found something else steering it.

## The people and the data
The truth comes from coordinates in GeoNames, an open geographic database. There are no human answers to these pairs; the human side is the published pattern.

## What Jev was asked
> Which city is farther west: Chicago, Illinois or Mobile, Alabama?
> *Answers: Chicago, Illinois · Mobile, Alabama*

The answer buttons were asked in both orders and averaged. The order of the two cities in the question sentence stayed as it was built.

## How it was measured
The share of pairs Jev gets right, split two ways: by whether the state misleads (balanced so each group has as many "western city first" pairs as "western city second"), and by whether the western city is named first or second in the question.

## Caveats
- **The question's word order never changed.** Each pair was asked with the two cities in one fixed order in the question sentence ("Chicago, Illinois or Mobile, Alabama"). The answer buttons were also swapped, which barely moved Jev. Asking each pair both ways round in the sentence itself is the obvious next test.
- **No human answers to these pairs.** People's classic mistake here, judging by the state instead of the city (Reno feels east of Los Angeles because Nevada is east of California; Stevens and Coupe, 1978), comes from the literature. No one answered these exact pairs.
- **"The state misleads" is a proxy.** A pair counts as misleading when the city in the more western state, by the average longitude of that state's cities, is actually the eastern one. That's a rough stand-in for where a state sits in someone's head.
- **A data error in the city list.** Cities were chosen as US places over 150,000 people in the GeoNames database, but at least one entry (Meads, Kentucky, listed with 288,649 people) is a small community, so the list includes a few places nobody would call well-known.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
