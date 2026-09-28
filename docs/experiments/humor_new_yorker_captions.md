# humor_new_yorker_captions

family: humor

## Why ask this
Every week the New Yorker prints a cartoon without a caption and invites readers to write one; readers then vote on the entries. It's one of the cleanest tests of taste in jokes: the same drawing, many attempts at the same punchline, and a big crowd deciding which ones work.

If a model has any sense of humor, it should at least tell the better captions from the worse ones for the same cartoon. This checks whether Jev's "that's funny" lines up with the crowd's.

## The people and the data
The votes come from the New Yorker's public crowd-rating system, released for research by the NEXT project (Jain and colleagues, 2020): visitors to newyorker.com rated submitted captions as unfunny, somewhat funny or funny. The drawings themselves are images, so we used written descriptions of each cartoon from a later research dataset (Hessel and colleagues, 2023).

We took contests 510 to 763, and from each, 15 captions with at least 100 votes: 5 from the funniest tenth, 5 from the middle and 5 from the bottom half. That gives 2,915 captions from 224 contests, with a median of 165 votes each.

## What Jev was asked
Each caption was a separate question, with the cartoon described in words:

> How funny is this caption for the cartoon?
> *Cartoon:* There are two firefighters ready to slide down two poles at the firehouse. One of the holes where the
> poles are is square instead of round, which is not standard.
> *Caption:* "Avoid the round one...it's pointless."
> *Unfunny: the caption doesn't land for me, no smile · Somewhat funny: I get the joke and smile a little · Funny: it
> makes me laugh*

The three answers mirror the contest's own buttons. Jev also answered with the answers in reverse order, to check that the order didn't drive it.

## How we measured it
For each caption we compare Jev's average rating with the voters' average (0 for unfunny, 2 for funny) and rank correlate them, once across all captions and once inside each contest, where captions compete for the same drawing (1 would be the same order, 0 no relation). We also check how often Jev's favorite caption in a contest is the voters' favorite, against the chance of picking it at random.

## Caveats
- **Jev never saw the cartoon.** Voters looked at the drawing; Jev read a written description of it, made for a research dataset. A caption that lands because of a detail in the drawing can't land for Jev.
- **Mostly unfunny captions.** Nearly every submitted caption is unfunny to most voters, so the differences between captions are small and hard for anyone to rank. The contest's published winners aren't in this set; the captions come from the public crowd-voting data, sampled evenly from the top, middle and bottom of each contest.
- **Who the voters are.** Anyone visiting newyorker.com could vote, so the crowd is New Yorker readers who chose to play, not a sample of the public.
- **A three-step scale.** The contest asks for unfunny, somewhat funny or funny, and so did we. With so few steps, Jev's habit of picking the middle option (see "Jev picks the middle when asked what it likes") has room to flatten everything.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
