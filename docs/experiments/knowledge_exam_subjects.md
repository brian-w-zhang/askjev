# knowledge_exam_subjects

family: knowledge

## 1. Question
Across MMLU's school and university subjects, grade-school science and everyday common sense, where is Jev reliably right, where does it dip, and does it know when it's on weak ground?

A model that is equally good everywhere is easy to trust; one with hidden dips isn't. Laying the same kind of question out subject by subject shows the shape of what Jev knows, the jaggedness, rather than one average.

## 2. Sourcing
Existing multiple-choice questions with answer keys: MMLU (57 subjects from high school to professional level), ARC (grade-school science, easy and challenge sets), SciQ, OpenBookQA, CommonsenseQA, HotpotQA comparison questions and HEAD-QA (Spanish health-profession exams, in English). Questions whose answers are numbers or calculations were left out when the corpus was built. Enough: about 33,000 questions, 40 or more in each subject shown.

Sources: `mmlu`, `arc`, `sciq`, `openbookqa`, `commonsense_qa`, `hotpot_compare`, `head_qa`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy per subject (Jev's most likely option equals the key) with 90% bootstrap intervals; Jev's average confidence in its pick on the questions it gets wrong vs right; the rank correlation between a subject's accuracy and Jev's average confidence there (does it know where it's weak).

## 5. Visualization
Dots per subject with intervals, the lowest subjects and the grade-school sets for contrast.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
The answer keys (and, where a paper reports one, people's accuracy on the same set)

## Limits
Exam keys have errors, and some subjects have more than others (see the caveats); these are famous public sets that Jev may have seen in training. Indicators of shape, not a score.

Results: `data/analysis/experiments/knowledge_exam_subjects.json` (private). Code: `scripts/experiments/`.
