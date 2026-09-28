# knowledge_close_calls

family: knowledge

## Why ask this
Knowing that the Main is a German river is one skill; knowing it's longer than another river is another. The first is a label, the second a magnitude. How close two sizes can be before a model starts guessing, and whether its confidence drops as the call gets closer, says how finely it has stored the numbers behind the facts.

## The people and the data
No people: the answers come from Wikidata, the free knowledge base behind Wikipedia.

## What Jev was asked
Category facts are multiple choice; comparisons are two options:

> Which stadium has the larger seating capacity: Estadio de los Juegos Mediterraneos or St Mary's Stadium?
> *St Mary's Stadium · Estadio de los Juegos Mediterraneos*

Each was also asked with the options in a different order.

## How we measured it
For the comparisons we compute how many times larger the bigger value is, group the pairs by that ratio, and check how often Jev picks the bigger one, and how sure it is, in each group.

## Caveats
- **Wikidata's numbers.** City populations, stadium capacities and river lengths in Wikidata can be stale or disputed; on the closest calls, a wrong key is enough to flip the answer.
- **Same kind only.** Comparisons pair two things of the same kind (two cities, two rivers). Mixed comparisons weren't asked.
- **Numbers are a known weak spot.** TypeSafe documents that Jev is weak with raw numbers. Here the numbers aren't given, they're recalled, so this measures memory of magnitudes rather than arithmetic.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
