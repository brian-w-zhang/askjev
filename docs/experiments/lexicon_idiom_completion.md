# lexicon_idiom_completion

family: lexicon

## Why ask this
Idioms are phrases whose meaning isn't the sum of their words, and they wear down with use. Many people finish "a bad apple in the ___" with "bunch" rather than "barrel", or "let off ___" with "easy" rather than "lightly". Which ending people produce shows which idioms are still alive in their standard form and which have drifted.

A model trained on vast amounts of edited text might know the dictionary form better than people remember it, or it might follow the drift in how people actually talk. Which one tells you whether it writes like a style guide or like a person.

## The people and the data
The idioms and completions come from **Bulkes and Tanner (2017)**, who normed 870 American English idioms with about 100 US adults per task.

## What Jev was asked
> Finish this idiom with one word: "Be let off ___"
> *easy · here · work · early · easily · lightly · another word*

The options were the idiom's own word and the other words at least two people wrote, plus "another word".

## How it was measured
How often Jev's top pick is the idiom's own last word, against the share of people who wrote it, overall and for the least, middle and most familiar thirds of idioms (familiarity from the same study). Then, on the idioms where most people wrote a different word, whether Jev goes with the idiom or with the crowd.

## Caveats
- **The idioms come in a stiff form.** The study lists each idiom in a standard form, often with "be" or "get" in front: "Be a happy ___", "Be let off ___". Out of context, "Be a happy ___" invites "day" as naturally as "medium", so some of the crowd's "drift" is the fragment, not forgetting.
- **Picking is easier than writing.** Seeing the right word on a short list makes it much easier to find.
- **American idioms, American readers.** The 870 idioms are American English, rated by about 100 US adults each. British or other idioms, and readers elsewhere, might go differently.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
