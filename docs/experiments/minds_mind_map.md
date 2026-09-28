# minds_mind_map

family: minds

## Why ask this
Does a frog have a mind? A robot? A baby? In 2007, Gray, Gray and Wegner asked people to compare characters two at a time and found that people see minds along **two** separate dimensions: **experience** (can it feel fear, hunger, pain?) and **agency** (can it plan, tell right from wrong, control itself?). Babies and dogs are high on feeling, low on acting. Robots are low on feeling, with a little agency. That two-axis map became one of psychology's most reproduced figures.

A model that talks about animals, patients, the dead and machines carries its own version of this map. Where it puts each character, and where it puts itself, shows what it assumes about minds.

## The people and the data
The original data isn't public, so we use a public replication (Weisman, 2015, on GitHub) that ran the same design with US adults recruited online: 11 to 16 people per capacity compared every pair of 13 characters, using the original character descriptions. It asks about four capacities: feeling afraid and feeling hungry (experience), and telling right from wrong and self-control (agency).

The characters include a five-month-old baby, a five-year-old girl, an adult man and woman, a man in a persistent vegetative state, a woman who recently died, a frog, a family dog, a young chimpanzee, a sociable robot named Kismet, and "you".

## What Jev was asked
Every pair of characters, for each capacity, with the study's five answers:

> Which character is more capable of feeling hungry?
> Charlie: Charlie is a 3-year-old Springer spaniel and a beloved member of the Graham family.
> Gerald Schiff: Gerald Schiff has been in a persistent vegetative state (PVS) for the past six months. [...]
> *Charlie: much more capable · Charlie: slightly more capable · Both equally capable · Gerald Schiff: slightly more
> capable · Gerald Schiff: much more capable*

That's 312 questions across all 13 characters; the 220 among the 11 characters shown here are the ones analyzed. Each was also asked with the answers reversed, which also swaps which character comes first, and we average the two.

## How we measured it
For each character and capacity, its average advantage over the others, from -2 (always "much less capable") to +2 (always "much more"). Feeling is the average of fear and hunger; acting is the average of morality and self-control. We compare Jev's ranking of the characters with people's on each axis (a rank correlation: 1 means the same order).

## Caveats
- **A small human sample.** The people's map comes from a public replication with 11 to 16 US online participants per capacity. Single comparisons are noisy; the character scores average about ten comparisons each, which is steadier.
- **No license on the data.** The replication's data is posted publicly but with no license stated, so it's used here for private research only. The original 2007 data isn't public.
- **Two characters missing.** The fetus and God were in the study but most of their comparisons were hidden by the content filter that keeps sensitive questions off the site, so this map uses 11 of 13 characters. God's spot, high on acting and low on feeling, is one of the original map's most famous features, and it's absent here.
- **Four capacities, not eighteen.** The original asked about 18 capacities; the replication used four (fear, hunger, morality, self-control). Two questions per axis make each axis sensitive to the exact wording.
- **"You" means different things.** One character is "you, the one answering". For people that's a human; for Jev it's Jev. See "Where Jev puts itself among minds".

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
