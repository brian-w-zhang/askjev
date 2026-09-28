# reasoning_beauty_contest

family: reasoning

## Why ask this
Everyone picks a number from 0 to 100. The winner is whoever is closest to two-thirds of the average. Game theory says pick 0.

And 0 never wins. Real players stop after a step or two of that reasoning, so the winning number depends on how far *the others* think. Winning this game, called the **Keynesian beauty contest**, means modeling real people, not ideal ones. It's a clean test of whether a model reasons about people as they are or as a textbook says they should be.

## The people and the data
Three real crowds, from published results:
- **Financial Times readers:** a 1997 contest Richard Thaler ran in the newspaper for its readers; the average was 18.91 and 13 won.

Only these averages were published, not each player's number.

## What Jev was asked
For each crowd, two questions: what number it would pick, and what it expects the average to be. For example:

> You and the other players each pick a whole number from 0 to 100. The winner is the player whose number is closest
> to two-thirds of the average of all the numbers picked. The other players are about 15 other copies of you, the
> same AI model, each answering this same question independently. What do you expect the average of all the numbers
> picked to be?
> *0 · 1 to 4 · 5 to 9 · ... · 95 to 100*

The wording was written for this project; the game and the crowds are the studies'. That's 8 questions, each asked with the choices in three different orders and averaged.

## How it was measured
For each crowd, Jev's pick is compared with the winning number (the fraction times the real average), and Jev's predicted average with the real one.

## Caveats
- **Only averages, no full results.** The studies published each crowd's average, not every guess. So it's possible to say how close Jev's pick is to the winning number, but not where it would have placed among the players.
- **A famous game.** The game is a staple of economics courses and pop-science articles, including write-ups of these exact contests. Jev may have read the averages. Its near-exact 37 for the lab students could be recall.
- **Old crowds.** The lab games were published in 1995 and the newspaper contest ran in 1997. Readers who play today have seen the game discussed for decades and pick lower, so "who would win now" isn't what this measures.
- **Copies of itself is this project's invention.** The "other players are copies of you" crowd has no human data and no right answer, only the textbook answer of 0. It tests whether Jev reasons about itself differently from people.
- **Answers in bins.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
