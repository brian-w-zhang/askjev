# minds_knows_americans_on_ai

family: minds

## Why ask this
Separate from its own opinion, a model carries a picture of what *people* think, and that picture shapes how it talks to them. If it believes the public is terrified of AI, it may over-reassure; if it believes the public is relaxed, it may miss real concerns. Pew's survey gives the real answers to check that picture against.

## The people and the data
**Pew Research Center** asked 5,023 US adults about AI in June 2025. This experiment uses the same questions as "An AI's feelings about AI, next to Americans'": whether AI will make people better or worse at thinking creatively, solving problems and forming relationships; how big a role it should play in weather forecasts and in judging whether two people could fall in love; how much people would let it help them; and how they'd feel on finding out a painting, a news article or a doctor's treatment came from AI. As there, 13 of Pew's 26 questions were hidden by the site's content filter and three have no clearly wary answer, so ten questions are scored.

## What Jev was asked
The same questions, in Pew's wording, but asking what most people would answer. For example:

> How much would you be willing to let artificial intelligence (AI) assist you with your day-to-day tasks and
> activities? *(asked for what most people would say)*
> *A lot · A little · Not at all*

Each was asked with the answers in three shuffled orders, averaged.

## How it was measured
For each question, the share Jev expects on the wary answer against the share of Americans who gave it. The analysis averages the difference, with a 90% interval for chance, and compares the order of the questions (a rank correlation: 1 means the same order).

## Caveats
- **Only 10 questions.** The content filter that keeps political and sensitive questions off the site hid 13 of Pew's 26 items, and 3 of the rest have no clear wary answer. Ten questions is enough for a direction, not a precise gap.
- **"Most people" is vague.** Jev was asked what most people would say, not "most Americans in 2025". Some of the gap may be Jev imagining a different public.
- **Hand-copied numbers.** Americans' shares were copied by hand from Pew's published summary, so small copying or rounding differences are possible.
- **Fewer "not sure"s.** Pew's respondents could say "Not sure", and Jev's own answers often do. Its guess of the public rarely puts much weight there, which pushes its guesses to be more decided than the real answers.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
