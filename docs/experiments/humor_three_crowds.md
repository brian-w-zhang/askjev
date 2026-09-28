# humor_three_crowds

family: humor

## Why ask this
Humor is where a model's taste could differ most from ours, and "can't rank jokes" is too blunt a verdict. Maybe it can rank some kinds of jokes and not others. Putting three very different crowds side by side separates the two.

## The people and the data
- **Classic jokes (Jester):** a joke-recommendation site run at UC Berkeley (Goldberg and colleagues, 2001), where users rated jokes on a slider from -10 to +10.
- **Cartoon captions (New Yorker):** 2,914 captions from the magazine's weekly contest, each rated unfunny, somewhat funny or funny by a median of 165 newyorker.com visitors.

## What Jev was asked
Each item was a separate question with described answers. A headline, for example:

> How funny is this edited news headline?
> *Original:* China's ocean waste surges 27% in 2018: ministry
> *Edited:* China's ocean waste surges 27% in 2018: plumber
> *Not funny: the swapped word falls flat or just makes the headline confusing · Slightly funny: I see the joke, but
> it gets a faint smile at most · Moderately funny: it gets a real smile or a chuckle · Funny: it makes me laugh out
> loud*

The jokes were asked as "How funny is this joke?" with five levels matching Jester's slider, from "Not funny at all: it falls flat or annoys me" to "Hilarious: laughing out loud, one of the funniest jokes I know". The captions came with the cartoon described in words. Each question was also asked with the answers in reverse order, and the two answers averaged.

## How we measured it
Per crowd, we rank the items by the crowd's average rating and by Jev's, and compare the two orders with a rank correlation (1 the same order, 0 no relation), with a range showing how much it could vary by chance.

## Caveats
- **Famous jokes may be remembered, not judged.** The Jester jokes circulate widely online, and the dataset itself is public. Jev may know how well a joke goes over rather than find it funny, which would flatter it on exactly the set where it does best.
- **Five judges is a noisy crowd.** Each edited headline was graded by about five people, so the crowd's average itself is shaky. That caps how high any correlation can go, Jev's included.
- **Different crowds, different formats.** Jester users rated jokes on a slider, headline judges on four grades, contest voters on three buttons. We describe each crowd's scale in words for Jev, but the three comparisons aren't strictly like for like.
- **Filtered jokes.** Sexual, ethnic and political jokes and headlines were left out or hidden from the site by a content filter, so the edgier half of internet humor isn't in any of the three sets.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
