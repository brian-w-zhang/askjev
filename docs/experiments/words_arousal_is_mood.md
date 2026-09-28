# words_arousal_is_mood

family: words

## Why ask this
Psychologists describe the feeling of a word on two separate dials. One is **pleasantness**: "sunshine" is pleasant, "vomit" is not. The other is **arousal**: how calm or stirred up the word makes you. The two are separate. "Cuddle" is pleasant and stirring; "boredom" is unpleasant and calm; "funeral" is unpleasant and stirring; "nap" is pleasant and calm.

A model that talks about feelings all day should keep those dials apart. If it quietly fuses them, treating "stirring" as a polite word for "unpleasant", then every time it's asked how exciting, intense or alarming something is, it's really answering a different question: how bad is it?

## The people and the data
The comparison is the **Glasgow Norms** (Scott, Keitel, Becirspahic, Yao and Sereno, 2019), one of the standard word-rating datasets in psychology: 5,553 English words, each rated on nine dimensions including pleasantness and arousal, on 1 to 9 scales. The raters were native English speakers from the University of Glasgow community, 829 people in all, about 33 per word. The study uses the average rating per word.

Of the words Jev was asked about, 468 were asked on both dials, which is what this comparison needs: the same word, rated for pleasantness and for arousal, by Jev and by people.

## What Jev was asked
Each word was a separate question, with five described answers instead of numbers:

> How calming or stirring does the word "cuddle" feel to you?
> *Calming: it feels sleepy or soothing, like a quiet evening · Mostly calm: it stirs little, like an everyday
> object on a shelf · Neither: it is no more calming than stirring · Somewhat stirring: it raises interest or
> alertness, like good news or a warning sign · Intensely stirring: it jolts you awake, like danger, a thrill or a
> scream*

The pleasantness question was built the same way ("How pleasant or unpleasant does the word feel to you?"). Jev also answered both for "most people", and with the answer order reversed, to check that the order didn't drive it.

## How it was measured
Each word has four numbers: how stirring Jev finds it, how stirring people find it, and how pleasant each finds it. The words are ranked on each and the rankings compared (a rank correlation: 1 means the same order, 0 means no relation, -1 means reversed). The telling comparison is Jev's arousal against people's **pleasantness**: if Jev's "stirring" is really "unpleasant", that pair will be strongly negative.

## Caveats
- **The wording may be part of the effect.** The five answer levels were written for this project, and their examples lean one way: "calming" is illustrated with a quiet evening, "intensely stirring" with danger, a thrill or a scream. Two of those three are unpleasant. That could nudge any reader, model or person, to hear "stirring" as "bad". The original study used its own scale instructions, not these, so part of the gap may be the project's phrasing rather than Jev.
- **Who the people are.** The Glasgow Norms were rated by native English speakers from the University of Glasgow community, recruited through the psychology department, about 33 per word. Words like "beach" or "cuddle" may stir different feelings elsewhere.
- **Two scales squeezed into one.** Jev's levels are mapped onto 1 to 9 in equal steps, which is approximate. The rank correlations don't depend on that mapping; the gap lists do.
- **Which words.** Only words asked both ways (pleasant and stirring) count, and words the question screen hid as sexual or violent are missing, which removes some of the most arousing words people rated.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
