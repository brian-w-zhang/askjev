# social_mild_emotions

family: social

## 1. Question
When a feeling comes in a strong and a mild word (furious or angry, terrified or afraid, devastated or sad), which one does Jev use?

Picking the milder word is a quiet form of downplaying. If Jev turns fury into anger and terror into fear, its summaries of how people feel will read calmer than the people wrote them.

## 2. Sourcing
Existing EmpatheticDialogues questions: a short situation written by someone feeling one of 32 named emotions, and Jev picks one of the 32. Three pairs of the same feeling at two strengths are in the list. Enough: about 90 stories per label.

Sources: `empathetic_dialogues`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
For each pair, the share of stories written under the strong word that Jev calls by the mild one, and the reverse; plus, over all 32 labels, how often Jev uses each word relative to how often writers did. 90% bootstrap intervals over stories.

## 5. Visualization
Paired bars per pair: strong read as mild vs mild read as strong; a ranked strip of the words Jev uses least relative to writers.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.693, top verdict `portrait`.

## Compared with
The writers' own labels (the label they were asked to write about)

## Limits
Writers chose a label before writing, so a story under 'furious' may read as plain anger. The comparison is Jev's pick vs the prompt label, not vs other readers.

Results: `data/analysis/experiments/social_mild_emotions.json` (private). Code: `scripts/experiments/`.
