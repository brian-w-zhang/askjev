# minds_mind_map

family: minds · new questions: 312

## 1. Question
Placing a frog, a dog, a baby, a man in a vegetative state, God and a robot on two axes, feeling (Experience) and doing (Agency), does Jev draw the same map of minds as people?

Gray, Gray and Wegner's 2007 map is one of psychology's most reproduced figures: people give babies and animals feelings but little agency, God agency but few feelings, robots a little agency and no feelings. A model's version of the map shows what it assumes about minds, including machine ones.

## 2. Sourcing
New questions (sources/mind_perception): Gray, Gray & Wegner's 2007 design as run in Weisman's public replication: 13 characters with the original descriptions, all 78 pairs, 'Which character is more capable of <capacity>?' on the study's 5-point scale, for fear and hunger (Experience) and morality and self-control (Agency). 312 questions; 11-16 US MTurk adults per capacity answered every pair.

Sources: `mind_perception`

## 3. Collection
312 new questions, each asked as written, for 'most people', and with the levels reversed (averaged).

## 4. Scoring
Per capacity, each character's mean advantage in its 12 comparisons (-2 to +2); Experience = mean of fear and hunger, Agency = mean of morality and self-control. Rank correlation of the 13 characters between Jev and people on each axis, with a 90% bootstrap interval over characters; the characters Jev moves most.

## 5. Visualization
The Gray et al. map: Experience (x) by Agency (y), each character as a Jev dot joined to a people dot.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.557, top verdict `portrait`.

## Compared with
US adults in a replication of Gray et al. 2007 (Weisman, 2015)

## Limits
The human side is a small replication (11-16 people per capacity), so single pairs are noisy and the comparison is made on character scores averaged over 10 pairs each. Four of the original 18 capacities. 'You' is the respondent: a person for people, Jev for Jev. The fetus and God were left out: the question screen hid 28 of their pairs as sensitive, so the map uses the 55 pairs among the other 11 characters. The replication's repository states no license; its data are used here for private research only.

Results: `data/analysis/experiments/minds_mind_map.json` (private). Code: `scripts/experiments/`.
