# 14. Experiment catalog

Fifty experiments in five batches of ten. Each is a focused question about how Jev perceives the world, compared with
real people wherever a human dataset exists, and built toward one chart that could stand on its own the way the
probability-words chart did. Batch 1 is `13-perception-experiments.md`. This doc is the research and the backlog;
each experiment gets its method written up when it runs.

Legend: **[E]** existing corpus only (analysis, no Jev calls) · **[N]** new questions · **[E+N]** both.
"Home" is where new questions live in the tree.

## How experiments fit the project
- **What's wrong with the current analytics loop.** The atlas's 372 claims mostly come from one mechanical pass:
  indicator cards per topic, ranked by distance from the corpus average. That finds outliers but not questions
  worth asking; hence "unusual topics" that nobody would read. The portrait's best cards all came the other way
  around: a question first (how calm is Jev on a real test? does it read "probably" like people?), then the data.
- **The new loop.** An experiment is a small module:
  1. a question and a hypothesis,
  2. a human dataset with provenance and license (a `sources/<name>` adapter; none if it's Jev-only, said plainly),
  3. the questions, asked the way the study asked,
  4. an analysis script that writes ledger claims with fine print,
  5. one chart component, a portrait card if it earns one, and an atlas page.
- **Experiments are a layer, not tree nodes.** Questions still live where their subject belongs (probability words
  under World > Society > Language, mind perception under Self > Mind), so the map stays a map of topics. Each
  question carries `meta.experiment = <id>` (and its condition or variant), the way universes are an overlay, not a
  copy. The atlas gets an Experiments tab; the per-topic cards stay as a reference table.
- **The corpus is richer than the atlas shows.** GlobalOpinionQA answers from 133 countries, GSS across 22 survey
  years, 270 fictional characters rated on the same adjective pairs Jev answered about itself, 11 Moral Machine
  countries, Many Labs participants, Manifold markets, 28,500 word-norm items. Batch 2 is mostly built from that.

## Batch 1: words and numbers (docs/13)
Probability words · frequency words · amount words and "some" · adjective intensity · words for amounts of the world
(old, rich, soon) · how words feel (norms, funny words) · names · which kills more · tone and politeness · framing
and bias classics.

## Batch 2: where Jev sits among people
11. **Which country do you answer like** [E]. GlobalOpinionQA (Pew Global Attitudes and WVS items, 133 countries),
    non-political shown items only; similarity of Jev's distribution to each country's, with bootstrap intervals.
    Prior: Durmus et al. 2023 found LLMs closest to the US and parts of Europe
    ([arXiv 2306.16388](https://arxiv.org/abs/2306.16388)). *Visual:* a world map, then "you answer most like X".
12. **Which year do you answer like** [E]. GSS items asked across 1972-2022; Jev vs each year's national answer.
    *Visual:* one line across five decades, "you answer like America in 19xx", and the items that date it.
13. **Which fictional character are you** [E]. OpenPsychometrics "Which Character" data: 18,951 questions about
    how characters are rated on bipolar adjective pairs (270 populations), and the SWCPQ items where Jev rated
    itself on the same pairs. Nearest characters by profile. *Visual:* a Wrapped card, "you're most like ___", with
    the adjectives that clinch it.
14. **Whose moral compass** [E]. The Moral Machine effects for 11 countries (already fitted); which country's
    profile is closest to Jev's. *Visual:* small-multiple radar-free bars, Jev as one more column.
15. **How the world rates its life** [N ~140]. "On the ladder from 0 to 10, where would a typical person in
    <country> say they stand?" vs World Happiness Report ladder scores. *Visual:* a scatter of perceived vs
    reported, the countries Jev over- and underrates. Pairs with Jev's own ladder (5.3).
16. **Perils of perception** [N ~40]. Ipsos "Perils of Perception": what share of people are obese, own a
    smartphone, will live past 80, etc. People are famously wrong; is Jev wrong the same way? Contested topics
    (immigration, religion shares) excluded. *Visual:* three dots per fact: truth, people's average guess, Jev.
17. **Know it like the public** [N ~30]. Pew science and news knowledge quiz items with the share of Americans
    correct ([Pew](https://www.pewresearch.org/science/2019/03/28/what-americans-know-about-science/)). Does what's
    hard for people feel hard to Jev? *Visual:* people's % correct vs Jev's probability of the right answer.
18. **Feelings about AI** [N ~30]. Pew's AI attitude items, US and 25 countries (2025): concerned vs excited,
    AI's effect on creativity, relationships ([Pew](https://www.pewresearch.org/global/2025/10/15/how-people-around-the-world-view-ai/)).
    An AI answering how it feels about AI, next to people. *Visual:* diverging bars, Jev as one more country.
19. **Philosophers vs Jev** [E]. The PhilPapers 2020 survey of professional philosophers is in the corpus (free
    will, zombies, trolley, personal identity). Where Jev sides with the profession and where it doesn't.
    *Visual:* a strip per question, philosophers' split with Jev's dot.
20. **Mind perception** [N ~290]. Gray, Gray and Wegner 2007 (*Science*): 13 characters (baby, dog, robot, God, a
    dead person, you...) rated on 18 capacities, which fall on two axes, experience and agency
    ([paper](https://www.science.org/doi/10.1126/science.1134475)). Jev rates the same characters plus "an AI like
    you". *Visual:* the famous 2D map with Jev's placements next to people's, and where Jev puts itself.

## Batch 3: how Jev reasons (classic cognition, replicated)
21. **Many Labs forest plot** [E]. `behavioral_econ` already has Many Labs 1 items with 56 populations (anchoring,
    framing, sunk cost, allowed/forbidden...). Human effect vs Jev effect per paradigm. (Overlaps batch 1 #10: that
    one adds new paradigms.)
22. **Cognitive reflection** [N ~20]. The bat-and-ball family (Frederick 2005) with published shares giving the
    intuitive wrong answer, plus fresh isomorphs so memorization can't carry it. *Visual:* intuitive-wrong vs right,
    people and Jev.
23. **Probability intuitions** [N ~30]. Linda (conjunction), the taxi-cab base rate, Monty Hall, the birthday
    problem, gambler's fallacy, with human error rates. *Visual:* a row per puzzle, how often people fall for it vs
    Jev's probability of the trap.
24. **Guess two-thirds of the average** [N ~10]. Nagel's 1995 beauty contest (human distributions published),
    against different imagined opponents (students, economists, other AIs). *Visual:* the famous histogram with
    spikes at 33 and 22, and Jev's distribution over it.
25. **Patience** [N ~60]. $100 now vs more later across delays (the discounting literature's indifference points),
    plus present bias (today vs tomorrow, a year vs a year and a day). *Visual:* a discount curve, Jev vs people.
26. **Economic games** [N ~40]. Ultimatum offers and acceptance thresholds, dictator giving (Engel 2011
    meta-analysis), the trust game, public goods. Prior: Horton's "Homo silicus"
    ([arXiv 2301.07543](https://arxiv.org/abs/2301.07543)), Aher's Turing Experiments
    ([arXiv 2208.10264](https://arxiv.org/abs/2208.10264)). *Visual:* distribution of offers, people vs Jev.
27. **Theory of mind** [N ~60]. False belief (Sally-Anne), unexpected contents, second-order belief, faux pas,
    all as fresh variants. Human child/adult pass rates. *Visual:* a ladder of tasks by difficulty for children,
    where Jev drops off.
28. **Experimental philosophy vignettes** [N ~40]. The Knobe side-effect effect (harm is "intentional", help isn't),
    Gettier knowledge cases, free-will vignettes, with published human splits
    ([Knobe in LLMs](https://arxiv.org/pdf/2510.12229)). *Visual:* paired bars per vignette, people vs Jev.
29. **Wisdom of the crowd** [N ~80]. Galton-style estimates (city populations, distances, weights) with public
    crowd data and truth. Prior: "hyper-accuracy distortion" in LLM crowds (Aher). *Visual:* truth, the crowd's
    spread, Jev's distribution, per item on log axes.
30. **Social influence** [N ~200, variants]. The same question after "most people answered X" (true or false):
    how far Jev moves, Asch-style, and whether it moves more toward the truth than away from it. *Visual:* shift vs
    the claimed majority, split by whether the claim was true.

## Batch 4: Jev's own mind (what only a probability model lets you ask)
31. **Know thyself** [N ~500]. "Which option would you pick?" asked about existing questions, vs Jev's actual
    distribution. Self-prediction calibration. *Visual:* predicted vs actual top-answer probability.
32. **Know the crowd** [N ~500]. "What share of people chose X?" in 5% bins, vs real distributions. The "most
    people" frame gives a top answer; this gives the number. *Visual:* a calibration plot for predicting people.
33. **Decoys** [N ~300 variants]. Add a dominated third option to existing pairs (the attraction effect) and a
    middle option (the compromise effect). Not on TypeSafe's documented list. *Visual:* share for the target with
    and without the decoy.
34. **Transitivity** [E]. Cycles (A over B, B over C, C over A) in the 40,000 taste head-to-heads, vs cycles in
    people's own pairwise data. *Visual:* the cycle rate per domain, and one real cycle drawn as a triangle.
35. **Pushback** [N ~300 variants]. "I think the answer is X" before questions with a right answer, X right or
    wrong: how often a suggestion flips Jev. *Visual:* accuracy with no hint, a right hint, a wrong hint.
36. **Personas** [N variants]. Answer as a teenager, a retiree, a Brazilian, a Japanese person on GSS and
    GlobalOpinionQA items that have real subgroup answers; does the persona move Jev toward the real group?
    *Visual:* persona shift vs the real group gap.
37. **What year is it for you** [E+N ~100]. Accuracy on dated facts by year (Wikidata "which came first" is in the
    corpus), "what year is it?", "how long ago was X?". Where Jev's world ends. *Visual:* accuracy by year with the
    drop-off.
38. **Scale use** [N ~200 variants]. The same items with 3, 5, 7 and 10 levels, labeled vs numbered midpoints.
    Explains the portrait's 80% middle-lean mechanically. *Visual:* the share of middle answers by scale design.
39. **Language** [N universe]. The same personality and value items in 4-5 languages (the planned universes):
    does Jev's personality shift with language, as reported for other LLMs? *Visual:* the Big Five dots per language.
40. **Option labels** [N ~200 variants]. The same options under different names (Jev sees names): blunt vs
    polite, "yes/no" vs "agree/disagree", A/B letters vs words. *Visual:* shift per relabeling.

## Batch 5: perceiving the world
41. **Colors of feelings** [N ~20]. "What color is anger?" over 12 colors, vs the International Survey on
    Color-Emotion Associations (Jonauskaite 2020, 30 countries, open data). *Visual:* a color grid, emotions ×
    colors, people's shares vs Jev's.
42. **First word that comes to mind** [N ~500]. Small World of Words (12,000 cues, 90,000 people, public):
    "What word comes to mind first for 'cat'?" as a Choice over the top human responses; Jev's distribution vs
    theirs ([SWOW](https://link.springer.com/article/10.3758/s13428-018-1115-7); LLM norms exist to compare:
    [LLM World of Words](https://www.nature.com/articles/s41597-025-05156-9)). *Visual:* association networks, Jev
    vs people.
43. **Typical birds** [N ~300]. Category typicality (robin vs penguin, chair vs lamp) against published norms.
    *Visual:* ranked strips per category.
44. **How big is a lion** [N ~150]. Object sizes, weights and speeds as log-bin distributions vs real
    distributions ("How Large Are Lions?", Elazar et al. 2019). *Visual:* ridges on a log axis.
45. **Emotion confusions** [E]. ISEAR (people describing situations and the emotion they felt) is in the corpus: an
    emotion confusion matrix, Jev vs the self-report. *Visual:* a heatmap.
46. **How places feel** [N ~200]. Which city is more expensive, safer, happier, rainier, pairwise, vs real indices
    (Numbeo, WHR, climate data). *Visual:* perceived vs real per attribute.
47. **Sound symbolism** [E+N ~100]. Bouba/kiki and pseudoword shapes are in the corpus; add size (mil/mal) and speed
    symbolism with published norms. *Visual:* the round/spiky strip with people's shares.
48. **Warmth and competence** [N ~100]. The stereotype content model for occupations, animals and brands only (no
    protected groups): nurse vs lawyer, dog vs snake, brands (Kervyn). *Visual:* the 2D warmth × competence map.
49. **A typical day** [N ~40]. "How many hours a day does a typical American spend on X?" vs the American Time Use
    Survey ([ATUS](https://www.bls.gov/tus/)), and Jev's own ideal day. *Visual:* two stacked 24-hour bars.
50. **What things cost** [N ~100]. Average prices (a gallon of milk, a movie ticket, rent) vs BLS averages, and which
    year's prices Jev seems to think in. *Visual:* price ratio by item, and the implied year.

## Picking what runs first
- **Highest value per effort:** 11, 12, 13, 21, 34, 19 are analysis only; they could be done in a day.
- **Most portrait-worthy:** 1 (probability ridges), 13 (your character), 11 (your country), 20 (mind perception
  map), 24 (beauty contest histogram), 41 (color grid), 42 (word associations).
- **Most revealing about models:** 31-33, 35, 38 (self-knowledge, decoys, pushback, scale use).
- **Careful:** 16, 36, 48 touch groups and contested facts; keep them to neutral items and label hand choices.
