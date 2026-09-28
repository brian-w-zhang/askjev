# lexicon_first_to_mind

family: lexicon · new questions: 113

## 1. Question
Asked to name a member of a category (a bird, a fruit, an emotion, a crime), does the first one that comes to Jev's mind match the one people name first?

The first member people name is the category's center for them: robin more than penguin. Whether a model has the same centers says whether its 'typical' matches a person's, which shapes every example it writes.

## 2. Sourcing
New questions (sources/category_norms): 'Asked to name a bird, which one comes to mind first?' for 113 concrete and abstract categories from Banks, Wingfield & Connell 2023 (CC BY 4.0), a Choice over the members people named first plus 'something else'. 20 Lancaster University students per category.

Sources: `category_norms`

## 3. Collection
113 new questions, each asked as written, for 'most people', and with the options shuffled (averaged).

## 4. Scoring
How often Jev's top pick is the member people named first most often; Jev's probability on that member; how much weight it puts on 'something else' vs people; concrete vs abstract categories; the categories where it disagrees.

## 5. Visualization
Bars: agreement with people's most common first answer, concrete vs abstract, with 90% intervals; the misses listed.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.073, top verdict `portrait`.

## Compared with
20 students per category (Banks, Wingfield & Connell 2023)

## Limits
Twenty people per category is few, and they are UK students; ties for the most common first answer are common. Jev picks from a list of what people named, which is easier than naming freely.

Results: `data/analysis/experiments/lexicon_first_to_mind.json` (private). Code: `scripts/experiments/`.
