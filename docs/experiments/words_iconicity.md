# words_iconicity

family: words

## Why ask this
Some words sound like what they mean: "buzz", "moo", "whoosh". That's **iconicity**, and it's not limited to animal noises: in rating studies, people hear a hint of meaning in many ordinary words, such as "blah" or "flee".

A model that only reads text has never heard a word. Whether it still senses these links, or only knows the obvious sound-effect words, says something about what text carries.

## The people and the data
Winter and colleagues (2023) asked people to rate thousands of English words for iconicity on a 1-to-7 scale, from "not iconic at all" to "very iconic". The individual ratings are public. We use 2,488 common words, spread across the range of ratings, each rated by about 10 to 17 people.

## What Jev was asked
One question per word, with seven described answers written for this project:

> How much does the word "whoosh" sound like what it means?
> *Any other sound would do as well: nothing in how it sounds connects to what it means · You can find a link
> between its sound and its meaning only by straining for one · One sound in it hints at its meaning, but you would
> notice only if someone pointed it out · Its sound suits its meaning, the way a short word suits something small,
> without imitating it · Its sound clearly fits its meaning, like a rough-sounding word for something rough · Part of
> it imitates what it means, such as a noise, a motion or a texture · Saying it imitates what it means, like "buzz",
> "hiss" or "boom"*

Each was also asked with the levels reversed, and we average the two.

## How we measured it
Jev's rating of each word next to people's average: the overall ranking (a rank correlation: 1 means the same order), the average level on each side, how many words each puts at the bottom, and the words with the biggest gaps.

## Caveats
- **Our level wording.** People rated on a 1-to-7 scale labeled only from "not iconic at all" to "very iconic", after instructions. Our wording may push Jev lower than people's plain scale pushes them.
- **Few raters per word.** Each word has about 10 to 17 ratings, so single words are noisy.
- **Reading, not hearing.** Jev never hears a word; it answers from what text says about words. Iconicity is partly about sound itself, which text only describes.
- **No license on the data.** The ratings are posted publicly with the study but carry no explicit data license; they're used for private research only.
- **The three best examples were removed.** "Buzz", "hiss" and "boom" aren't asked, because our top level uses them as its examples.
- **Hand-picked words.** "Blah" and "flee" in the headline were picked by hand from the largest gaps among words the raters agreed on.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
