# work_routing_misses

family: work

## Why ask this
Routing is one of the most common jobs a model like Jev does: read a customer's message and send it to the right team, flow or tool. It's the task TypeSafe itself leads with.

What matters isn't only how often the router is right, but how it's wrong. A message sent to a neighboring intent ("order a card" vs "get a card") costs little; one sent to an unrelated team costs a lot. And if the right answer is usually the router's second choice, a simple fallback (show both, or ask) recovers most misses.

## The people and the data
The menus range from 7 to 77 options.

Each message's right intent comes from its dataset: labeled by crowd workers (the airline tweets), chosen by the person who wrote the message for it (the Dolly instructions, the ABCD chats), or the product a complaint was filed under.

## What Jev was asked
Each message was one pick-one question, with every intent written out with a one-line description. For example:

> What is the customer asking the bank about in this message?
> *Message: "Where is the card PIN?"*
> *Options (77): age limit: the minimum age to open or use an account · change PIN: changing the card PIN · ATM
> support: which ATMs the card works at · … · get a physical card …*

## How it was measured
For each dataset: the share of messages Jev routes right; among its misses, the share where the right intent was its second choice; and the most common confusions. Across the 13 datasets, the analysis compares menu length with the share right (rank correlation: 1 means longer menus always do better, -1 always worse, 0 no relation).

## Caveats
- **Some intents overlap by design.** Many "misses" are between intents a person would also hesitate over. The datasets' labels treat these as wrong, so the share right is a floor.
- **Clean benchmark messages.** Most of these datasets use short, tidy messages collected or written for research. Real customer messages are longer, messier and often ask two things at once.
- **Different menus, different difficulty.** Some datasets have crisp, separate intents (travel domains, music vs weather); others blur (task types like "brainstorming" vs "open question"). Comparing datasets mixes menu length with how distinct the intents are.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
