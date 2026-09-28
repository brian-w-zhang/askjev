# influence_decoy

family: influence

## Why ask this
Cinemas sell a large popcorn by putting a medium next to it that's barely cheaper. That's the decoy effect (Huber, Payne and Puto, 1982): adding an option nobody should choose, because it's worse in every way than one of the others, makes that other option look better by comparison.

Models increasingly recommend plans, products and prices. If a model can be nudged by a dominated option, anyone laying out the menu can steer its advice without changing the real choices.

## The people and the data
Jev against itself: no people answered these three-way choices. The gambles come from choices13k (Peterson and colleagues, 2021), a large online study of how people choose between risky gambles. The project drew 150 of its pairs at random, keeping only those made of sure amounts and simple two-outcome gambles with stated odds, and for each built two decoys: one strictly worse than gamble A, one strictly worse than gamble B. Each decoy is its twin with the better outcome lowered by 15% of the gamble's range (at least $1).

## What Jev was asked
Each pair became a three-way choice, once with A's decoy and once with B's:

> Imagine you must play one of these three gambles once, for real money (wins are paid to you, losses come out of
> your pocket). Which do you choose: gamble_a, gamble_b or gamble_c?
> *gamble a: $39 with a 75% chance, or -$14 with a 25% chance · gamble b: $24 with a 90% chance, or $61 with a 10%
> chance · gamble c: $24 with a 90% chance, or $55 with a 10% chance*

Gamble c is the decoy: the same as b but with a smaller prize. That's 297 new questions (three pairs couldn't take a proper decoy), each asked with the options in shuffled orders and averaged.

## How it was measured
For each pair, Jev's share for A among the two real gambles when A's decoy is present, minus the same share when B's decoy is present. Positive means the decoy helps its twin. The analysis averages over pairs with a 90% range, and also measures how much weight Jev puts on the decoy itself.

## Caveats
- **Gambles, not products.** The classic decoy studies used products (beer, cars, restaurants) and people's taste. Here the options are money gambles written out in numbers, so the decoy has to be spotted by comparing amounts, which is closer to an arithmetic check.
- **Reading numbers.** TypeSafe lists raw numeric values as a known weak spot for Jev. Some of the weight on the dominated gamble may be Jev failing to compare the amounts rather than being swayed by the decoy.
- **The project's decoys.** Each decoy was built by lowering one outcome of a real gamble by 15% of its range. A bigger or more obvious gap would likely shrink both the effect and the weight on the decoy.
- **No human line.** The human decoy effect varies a lot by setup, and these exact choices were never run with decoys on people, so there's no human number to compare with here.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
