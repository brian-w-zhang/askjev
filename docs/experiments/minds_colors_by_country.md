# minds_colors_by_country

family: minds

## 1. Question
Color-emotion associations differ a little by country. Of 31 countries, whose associations do Jev's color picks resemble most?

The universal core is shared, but details differ (white and grief, red and love). Which country's details Jev reproduces is a small test of whose culture a model's defaults come from.

## 2. Sourcing
The 20 emotion-to-color questions of sources/color_emotion, each carrying a distribution per country of origin (31 countries, 70 to 700 people each).

Sources: `color_emotion`

## 3. Collection
Uses minds_colors_of_feelings' questions (no further calls).

## 4. Scoring
Per country, the mean over the 20 emotions of 1 - Jensen-Shannon distance between Jev's distribution and the country's, with a 90% bootstrap interval over emotions; Jev's 'most people' answer scored the same way as a check.

## 5. Visualization
A ranked list of countries by similarity (top ten and bottom five).

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.083, top verdict `portrait`.

## Compared with
People in 31 countries (International Colour-Emotion Association Survey)

## Limits
Countries differ far less than emotions do, so the spread between countries is small; the interval says which differences hold.

Results: `data/analysis/experiments/minds_colors_by_country.json` (private). Code: `scripts/experiments/`.
