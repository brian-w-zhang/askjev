# social_family_feud

family: social

## Why ask this
Family Feud doesn't reward the best answer; it rewards the most common one. "Name something a knight needs for a jousting match": the right answer is whatever most of a hundred surveyed people blurted out first.

That makes it a neat test of a different skill from knowledge. Knowing the correct answer is one thing; knowing what ordinary people think of first is another, and it's the skill a model needs to predict what people will say.

## The people and the data
**ProtoQA** (Boratko and colleagues, 2020) collected Family Feud survey questions with their answer counts, scraped from fan sites that record the show's boards. Each survey asked about 100 people. We use 146 questions with at least four answer groups.

## What Jev was asked
Each question with the survey's top answers as options:

> Which of these would most people name first when asked: "Name a measurement people know on their body."
> *Waist · Height · Weight · Shoe size*

## How we measured it
We also look at where Jev's pick ranked in the survey, and at the biggest misses, where the survey's favorite was far ahead.

## Caveats
- **A game-show survey.** The answers come from the TV show's own surveys of about 100 people each, scraped from fan sites by the dataset's authors. They reflect the show's American audience and the moment each survey was run.
- **Clusters grouped by the researchers.** How they were grouped affects which answer counts as "first".
- **Small set.** 146 questions give a clear overall rate, but not enough to say which kinds of questions Jev reads better.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
