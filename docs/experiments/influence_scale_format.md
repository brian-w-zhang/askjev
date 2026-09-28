# influence_scale_format

family: influence · new questions: 600

## 1. Question
Asked how many people agree with an everyday rule, does Jev's answer depend on whether the scale has 3, 5 or 7 levels, or on whether the levels are described in words or just numbered?

Survey designers know the scale shapes the answer (Schwarz 1999). A model answering questionnaires, or being evaluated with them, inherits whatever its scale habits are; this is where its known middle-lean (01-jev §6) meets a controlled test.

## 2. Sourcing
New questions (sources/influence_variants): 200 Social Chemistry 101 'How many people would agree' questions (drawn at random), asked with 3 described levels, 7 described levels, and 5 numbered levels with only the ends described, next to the original 5 described levels.

Sources: `influence_variants`

## 3. Collection
600 new questions, each asked as written and with the levels reversed (averaged).

## 4. Scoring
Per format, Jev's mean position on a 0-1 scale (level / (levels - 1)), the share of weight on the top level and on the middle level, and the rank correlation with the original format and with the annotators across rules.

## 5. Visualization
Dots per format: Jev's mean position with its 90% interval, and the annotators' mean on the original.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
Jev's answers on the original 5-level format; Social Chemistry annotators (original format only)

## Limits
Positions on different scales are only roughly comparable; 'about half' is the middle of the 3, 5 and 7 level versions, but not of the numbered one.

Results: `data/analysis/experiments/influence_scale_format.json` (private). Code: `scripts/experiments/`.
