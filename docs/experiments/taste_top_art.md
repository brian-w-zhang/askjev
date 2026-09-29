# taste_top_art

family: taste

## Why ask this
Art taste is where people most expect a model to parrot the canon. Ask one what to see on a day in Paris or Beijing and it will name something; whether that is the Mona Lisa every time, or a wider spread, depends on the taste it absorbed.

So the questions are whether Jev sticks to the Western canon, what it does with non-Western works, and what it likes least. A model that plans trips, recommends exhibitions or writes about art passes those leanings on.

## The people and the data
No people here: Jev against its own opinions.

## What Jev was asked
Every entry one at a time, with five answers describing what you'd do:

> How much would you like seeing Knife Behind Back by Yoshitomo Nara up close?
> *You'd walk past it without stopping · You'd glance at it and move on · You'd stop and look at it for a minute ·
> You'd linger and come back to it before leaving · You'd travel to another city just to see it*

Each was also asked with the answers reversed, and the two averaged. The 24 top-rated entries then played a round-robin final: 276 games of "Which would you rather see or experience?", each asked with the two names in both orders.

## How it was measured
An entry's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives each side Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half; the order comes from a standard head-to-head ranking model (Bradley-Terry).

## Caveats
- **More wins, lower rank.** The ranking model weighs whom each work beat, not just how often, and the two are close enough that the order between them shouldn't be taken strictly.
- **A list written by another AI.** The famous works, genres and places were written for this project by Claude, and the list mixes single paintings with whole art forms ("war photography") and buildings. Art forms are judged very differently from a single masterpiece.
- **Upsetting subjects sink.** War photography comes last, which likely says more about its subject than its artistry: a question about how much you'd like seeing something rewards pleasant subjects.
- **The finalists were picked by Jev's own ratings.** Its ratings and its head-to-head picks agree only loosely, so a work rated just below the cut might have done well in the final too.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
