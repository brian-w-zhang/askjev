# choices_ai_poetry

family: choices · new questions: 70

## 1. Question
Given poems by Chaucer, Shakespeare, Byron, Whitman, Dickinson and others, mixed with ChatGPT poems written in their style, does Jev tell which are human better than the 1,634 people who took the same test, and does it fall for the same ones?

In Porter & Machery's study people did worse than chance: the AI poems, plainer and more regular, read as human, and the real ones, stranger, read as machine-made. A model is an interesting judge of its own kind.

## 2. Sourcing
New questions (sources/ai_poetry): the study's wording and poems for the seven poets whose real poems are in the public domain (Chaucer, Shakespeare, Samuel Butler, Byron, Whitman, Dickinson, early Eliot), 5 human and 5 AI poems each, with the study's split of answers per poem (about 160 people each).

Sources: `ai_poetry`

## 3. Collection
70 new questions, each asked as written, for 'most people', and with the two options in both orders (averaged).

## 4. Scoring
Share of poems where Jev's more likely answer is right, vs the crowd's majority and vs the average person (the share of people right per poem); the share saying 'human' for real vs AI poems, for Jev and people; per poet.

## 5. Visualization
Paired bars: the share of poems called human, for real poems and for AI poems, people vs Jev.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 6.305, top verdict `headline`.

## Compared with
US adults in Porter & Machery 2024, Study 1 (about 160 judgments per poem)

## Limits
Only public-domain poets are used, so the modern poets where people did worst (by the paper's account) are not in this set. The AI poems came from ChatGPT 3.5 in 2023; Jev may have seen the real poems in training, which helps it recognize them: read the result as recognizing famous poems plus spotting 2023-era ChatGPT style, not as a pure test of judgment. Line breaks were lost in the study's text export; poems are shown as running text to Jev.

Results: `data/analysis/experiments/choices_ai_poetry.json` (private). Code: `scripts/experiments/`.
