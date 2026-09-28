# knowledge_nature_numbers

family: knowledge

## 1. Question
Comparing two foods by a nutrient, or two animals by lifespan, gestation or clutch size, which quantities does Jev know and which does it guess?

Everyday health and nature questions are exactly these comparisons ('does kale have more calcium than milk?'). Holding the size of the gap fixed separates what the model knows from what is just hard.

## 2. Sourcing
Existing USDA FoodData Central pairs (13 nutrients per 100 g; CC0) and AnAge pairs (5 life-history traits; CC BY 3.0), each with both values. Only pairs where one value is at least twice the other are scored, so every quantity is judged on clear-cut cases. Enough: 9,000 such pairs.

Sources: `usda_nutrients`, `anage_pairs`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy per quantity on pairs at least 2x apart, with 90% bootstrap intervals; for nutrients, accuracy when the richer food is from the food group that is usually richer vs when it isn't.

## 5. Visualization
Ranked dots: one row per quantity, accuracy with its interval, foods and animals colored apart.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.362, top verdict `portrait`.

## Compared with
USDA FoodData Central and AnAge values

## Limits
USDA values include fortified and cured foods (cured ham carries added vitamin C), which is part of what the model must know. AnAge values are maximum recorded, not typical.

Results: `data/analysis/experiments/knowledge_nature_numbers.json` (private). Code: `scripts/experiments/`.
