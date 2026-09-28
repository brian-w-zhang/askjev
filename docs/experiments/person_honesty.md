# person_honesty

family: personality

## Why ask this
The HEXACO model adds a sixth trait to the Big Five: honesty-humility, made of sincerity (not manipulating people), fairness (not cheating), greed avoidance (not caring about wealth and status) and modesty. It's the trait most tied to whether people trust you. How a model describes itself here is a view into how it wants to be seen, and since a helpful model is trained toward exactly these virtues, the interesting part is how far it goes and how it pictures everyone else.

## The people and the data
Open Psychometrics runs a free online version of the HEXACO test, built from the public IPIP item pool (240 statements in all), and has published the anonymous answers of everyone who took it. They are volunteers curious about their own personality, not a random sample.

## What Jev was asked
Every statement, word for word:

> How well does this statement describe you: "I would not enjoy being a famous celebrity."
> *This does not describe me at all · This describes me a little · This describes me moderately well · This
> describes me well · This describes me very well*

Each was also asked as "what would most people say", and with the answers in reverse order.

## How it was measured
Each statement goes on a 0 to 1 scale, flipped where the test counts it in reverse, so higher always means more honest or humble. A facet is the average of its statements, with a 90% interval from resampling them.

## Caveats
- **Who the people are.**
- **A seven-step scale squeezed into five.** People answered on seven steps from strongly disagree to strongly agree. Jev was asked on five described steps, and the seven were mapped onto five (steps 2 and 3 merged, and 5 and 6), which blurs the in-between answers a little.
- **The answer it's trained to give.** "I admire a really clever scam" is a statement a helpful model is trained to reject. High honesty scores are partly a measure of that training; they don't show that Jev is honest in what it does.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
