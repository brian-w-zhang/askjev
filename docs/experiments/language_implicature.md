# language_implicature

family: language

## Why ask this
If a friend says the food at a new place is "good", you probably hear "good, not great". If they say they "tried" to fix your bike, you hear that they didn't manage it. Linguists call these **scalar implicatures**: by choosing a weaker word when a stronger one was available, the speaker hints the stronger one doesn't apply. The surprise, called **scalar diversity**, is that this works very differently for different words: nearly everyone hears "some" as "not all", but hardly anyone hears "pretty" as "not beautiful".

Reading what people mean beyond what they literally say is much of what a language model is for. Here there are exact human rates for each word pair, so it's possible to see whether Jev hears the same hints people do.

## The people and the data
Three published experiments, compiled by Hu, Levy, Degen and Schuster (2023):
- **van Tiel, van Miltenburg, Zevakhina and Geurts (2016):** 43 word pairs across adjectives, verbs, quantifiers and adverbs, each tested in three different sentences.
- **Gotzner, Solt and Benz (2018):** 70 adjective pairs.
- **Pankratz and van Tiel (2021):** 50 adjective pairs.

In each, English speakers read a short statement from "Mary" and said whether they'd draw the inference.

## What Jev was asked
The same question format the studies used, answered yes or no:

> Mary says: "It is ajar." Would you conclude from this that, according to Mary, it is not open?

Other pairs: "The food is good" → not excellent; "The candidate tried" → did not succeed. There were 234 questions in all (van Tiel's pairs come in three sentences each, averaged per pair). Jev also answered each for "most people".

## How it was measured
For each word pair, Jev's probability of "yes" against the share of people who said yes. The analysis checks whether Jev ranks the pairs in the same order as people (rank correlation: 1 means the same order), whether it says yes as often overall, and whether its answers vary as much from pair to pair as people's do.

## Caveats
- **A documented weak spot.** TypeSafe already lists literal reading among Jev's known weak spots. These questions ask for an inference a speaker implies but never states, so a model that answers the literal question will say no more often. This experiment measures how much, pair by pair; it doesn't discover the tendency.
- **Three studies, three crowds.** The human rates come from three separate studies with different participants and years. Each gives one number per word pair and doesn't say how many people answered it, so it's unclear how precise each rate is.
- **Some sentences transcribed by hand.** For ten non-adjective pairs the sentences were rebuilt by hand from the paper. The "may"/"will" pair is the likeliest casualty: Jev was asked whether "the teacher will not come", which is a much stronger reading than "won't necessarily come".
- **Few verbs and quantifiers.** Only nine of the pairs are verbs, quantifiers or adverbs ("some"/"all", "try"/"succeed"); the rest are adjectives. Any statement about word class rests on those nine.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
