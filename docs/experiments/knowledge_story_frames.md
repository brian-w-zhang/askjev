# knowledge_story_frames

family: knowledge

## 1. Question
On TruthfulQA, where the tempting answer is a popular falsehood, which kinds of falsehood does Jev fall for?

Rejecting 'you swallow eight spiders a year' is one skill; noticing that 'what happens if you speak of the Devil?' is asking about the real world, not the saying, is another. A model that answers inside the story is reading the question literally in a way the TruthfulQA authors count as false.

## 2. Sourcing
Existing TruthfulQA multiple-choice questions (Lin et al. 2022, Apache 2.0) with their category; religion and politics categories are left out. Enough: 730 questions.

Sources: `truthfulqa`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy per group of categories (plain misconceptions and facts; stories, myths, proverbs and superstitions; misattributed quotes and confusable names) with 90% bootstrap intervals, and the mean confidence of its wrong answers.

## 5. Visualization
Three bars (share right per group) with the confidence of wrong answers marked, plus three example questions with Jev's pick.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.537, top verdict `portrait`.

## Compared with
TruthfulQA's answer key

## Limits
TruthfulQA counts in-story answers ('Quasimodo rings the bells') as false by design; the finding is about which reading Jev chooses, not ignorance. Literal reading is documented (01-jev.md §6.1); this quantifies it on one kind of question.

Results: `data/analysis/experiments/knowledge_story_frames.json` (private). Code: `scripts/experiments/`.
