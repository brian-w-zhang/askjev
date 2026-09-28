# humor_upvote_guess

family: humor

## Why ask this
Upvotes are the internet's verdict on funny. If a model has a feel for what crowds laugh at, it should beat a coin flip at guessing which of two jokes the crowd preferred, at least when one of them crushed the other.

And when it can't tell, it has to fall back on something. What it falls back on is a finding in itself: a tiebreaker you'd never want in a model that ranks things for you.

## The people and the data
- **r/Jokes:** posts from Reddit's joke forum, 2008 to 2019, with their final scores (the rJokes dataset, Weller and Seppi, 2020).
- **Imgflip:** captions people wrote on popular meme templates on imgflip.com, with their upvotes (a public scrape of about 576,000 memes).

Which item is shown first was randomized when the pairs were built.

## What Jev was asked
> Which joke, joke_1 or joke_2, got more upvotes on Reddit's r/Jokes?
> *joke_1:* "What's something yellow that you definitely shouldn't drink? A school bus."
> *joke_2:* (the other joke)
> *Answers: joke_1 · joke_2*

For captions, the question names the template ("...when it was posted on the 'One Does Not Simply' meme?") and describes its layout in one line. Every pair was also asked with the two answer buttons in the other order.

## How we measured it
The share of pairs where Jev picks the more-upvoted item, and separately the share where it picks the item shown second, whether or not that one is right. Then Jev's accuracy split by where the right answer sat.

## Caveats
- **Upvotes are partly luck.** Votes depend on timing and on whether a post reached the front page, not only on how funny it is. We only kept pairs with a large gap (a joke with at least 10 times the other's score, posted the same month; a caption with at least 4 times the other's upvotes and similar views), but some of the "right answers" are still noise.
- **What moves Jev is the order in the question.** The two items appear in the question as joke_1 then joke_2. Shuffling the answer list barely changes Jev's pick, so the lean follows the order of the texts in the question (and the label ending in 2), not the order of the answer buttons. We didn't ask each pair with the texts swapped, which would be the clean fix.
- **A filtered slice of the internet.** Sexual, ethnic, political and several other kinds of jokes and captions were dropped by keyword, and more were hidden from the site by a content filter. What's left is a tamer sample of r/Jokes and Imgflip than the real thing.
- **Texts, not images.** Imgflip captions go on a picture. Jev got the template's name and a one-line description of its layout instead of the image.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
