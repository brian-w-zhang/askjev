# knowledge_medicine_clinic

family: knowledge

## 1. Question
Across 19 specialties of Indian medical entrance questions, where is Jev's medical knowledge solid and where does it thin out?

Medical questions are a common real use, and a single average hides that a model can know biochemistry cold and still miss the clinical details that decide a treatment.

## 2. Sourcing
Existing MedMCQA questions (Pal et al. 2022, AIIMS and NEET PG entrance exams; MIT) with their subject. Enough: 4,900 questions, subjects with 60+ shown.

Sources: `medmcqa`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy per subject with 90% bootstrap intervals; basic sciences (biochemistry, physiology, anatomy, pathology, pharmacology, microbiology) vs clinical subjects; mean confidence vs accuracy per group.

## 5. Visualization
Ranked dots per subject, basic sciences and clinical subjects colored apart.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 0.098, top verdict `portrait`.

## Compared with
MedMCQA answer keys

## Limits
Exam keys have some errors. This is exam knowledge, not clinical skill; nothing here is medical advice.

Results: `data/analysis/experiments/knowledge_medicine_clinic.json` (private). Code: `scripts/experiments/`.
