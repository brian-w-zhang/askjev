# language_hex_colors

family: language · new questions: 150

## 1. Question
Given a color as a hex code (#fffe40) and four names from the xkcd color survey, how often does Jev pick the survey's name, and does it fall for the nearest similar color?

TypeSafe documents raw hex and RGB values as a weak spot (01-jev §6 item 2). This puts a number on it with a crowd-sourced answer key, and separates 'no idea of the color' from 'right family, wrong shade'.

## 2. Sourcing
New questions (sources/xkcd_colors): 150 of the 949 colors in the xkcd color survey (CC0), each with its survey name, the nearest other survey color at least 40 RGB units away, and two far ones.

Sources: `xkcd_colors`

## 3. Collection
150 new questions, each asked with the names in three shuffled orders (averaged).

## 4. Scoring
Share where Jev's top name is the survey's (chance 25%), with a 90% bootstrap interval; share of misses that go to the near distractor (right family) vs the far ones.

## 5. Visualization
Bars: survey name, near distractor, far distractors, as shares of Jev's picks.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.868, top verdict `portrait`.

## Compared with
The xkcd color survey's names (about 222,500 people naming colors)

## Limits
Known limit, not a discovery (01-jev §6 item 2). The near distractor can be a genuinely close shade.

Results: `data/analysis/experiments/language_hex_colors.json` (private). Code: `scripts/experiments/`.
