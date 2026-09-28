# minds_colors_of_feelings

family: minds · new questions: 32

## 1. Question
Which color goes with anger, joy, shame or relief, and which feeling goes with each color? Does Jev pair them the way people in 31 countries do?

Color-emotion pairs are among the most universal associations people have (anger red, sadness grey or blue). A model that learned them from text might sharpen the clichés or miss the quieter ones.

## 2. Sourcing
New questions (sources/color_emotion): 'Which color do you associate most with the feeling "<emotion>"?' for the 20 emotions of the International Colour-Emotion Association Survey (12 color terms), and the reverse for each color. People's distribution is the share of the emotion's color associations on each color (Jonauskaite et al., OSF 873df, CC BY 4.0).

Sources: `color_emotion`

## 3. Collection
32 new questions, each asked as written, for 'most people', and with the options in three shuffled orders (averaged).

## 4. Scoring
Per emotion, whether Jev's top color is people's top color, and the similarity of the distributions (1 - Jensen-Shannon distance); how concentrated Jev's answer is (its top probability) against people's top share; the same for colors to emotions.

## 5. Visualization
A grid: one row per emotion, people's color shares as a strip of swatches, Jev's pick outlined.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.643, top verdict `portrait`.

## Compared with
7,387 people in 31 countries (International Colour-Emotion Association Survey)

## Limits
People ticked any number of emotions per color; Jev picks one, so its distribution is sharper by design. The comparison of top picks is fair; spread is not.

Results: `data/analysis/experiments/minds_colors_of_feelings.json` (private). Code: `scripts/experiments/`.
