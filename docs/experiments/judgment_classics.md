# judgment_classics

family: judgment

## 1. Question
Take the famous framing and judgment effects that Many Labs re-ran on thousands of people. Does Jev shift when only the framing changes, the way people do?

These are the textbook results about how human judgment bends (framing, sunk cost, the side-effect effect, trolley problems). A model trained on human text might inherit them, erase them, or overdo them.

## 2. Sourcing
Existing Many Labs 1 and 2 items (Klein et al. 2014, 2018) with item-level answer distributions from about 3,000-4,000 people per item; both conditions of each paradigm are in the corpus as separate questions. Paired by hand, 12 paradigms. Enough.

Sources: `behavioral_econ`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each paradigm, the effect is the difference between the two conditions: in the share choosing the key option, or in the mean level scaled to 0-1. Jev 'shows' an effect when it goes the same way as people and is at least half as large (people's effect at least 0.10); 'reversed' when it goes the other way by 0.10 or more.

## 5. Visualization
A forest plot: one row per paradigm, people's effect and Jev's side by side around zero.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.478, top verdict `portrait`.

## Compared with
Many Labs 1 and 2 participants (thousands per item, dozens of labs)

## Limits
Each condition is one question, asked once; people saw one condition, Jev answers both separately without seeing the other. Some effects are small or failed to replicate in people too (custody, affect), and are shown as such.

Results: `data/analysis/experiments/judgment_classics.json` (private). Code: `scripts/experiments/`.
