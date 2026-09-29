# knowledge_nature_numbers

family: knowledge

## Why ask this
Numbers about food and animals are everyday knowledge: does a banana or a potato have more potassium, does a parrot or a dog live longer. A model might know the headline numbers (calories, protein) well and be vague about the rest (minerals, vitamins, how long an egg takes to hatch).

People ask models exactly these questions when planning meals or checking a fact, and a confident wrong answer looks the same as a right one. Keeping every comparison easy (one value at least twice the other) shows which kinds of numbers Jev has actually absorbed, rather than how well it splits hairs.

## The people and the data
No people; the answers come from two public databases. USDA FoodData Central (CC0) gives 13 nutrients per 100 grams for thousands of foods; AnAge (CC BY 3.0) gives five life-history traits for thousands of animal species: maximum lifespan, gestation, incubation, age at maturity, litter size.

## What Jev was asked
Two-option questions:

> Gram for gram, which has more vitamin C: raw garlic or jarred salsa?
> *raw garlic · jarred salsa*

Each was also asked with the two options in the other order.

## How it was measured


## Caveats
- **Fortified and processed foods.** The USDA table includes cured, fortified and processed foods (cured ham carries added vitamin C). Jev has to know those too, which is fair, but some "misses" are surprising for a reason, not ignorance.
- **Record values for animals.** AnAge lists maximum recorded values (the longest-lived individual, not the typical one), which can surprise even experts.
- **Clear-cut cases only.** Only pairs at least twice apart are scored, so every quantity is judged on easy comparisons; the gaps between quantities would likely widen on close calls.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
