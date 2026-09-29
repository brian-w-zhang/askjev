# knowledge_medicine_clinic

family: knowledge

## Why ask this
People ask models about a toothache, an eye drop or a drug interaction every day. Medicine is where they most want a model to be right, and where a confident wrong answer does the most harm.

A single exam average hides where the knowledge is. Splitting a large medical exam by subject shows whether Jev is solid on the science underneath and thinner on the specialties, and whether its confidence drops where its accuracy does.

## The people and the data
MedMCQA (Pal et al. 2022; Apache 2.0 on its Hugging Face release) collects multiple-choice questions from India's AIIMS and NEET PG postgraduate medical entrance exams, the tests doctors take to enter specialist training, each tagged with a subject and an answer key.

## What Jev was asked
Each question with its four options:

> Which of the following is main cause of pain during pulpal injury progression?
> *Decrease pressure · Arteriolar dilatation · Decreased threshold of nerve fibres to pain · Increased vascular
> permeability*

Each was also asked with the options in shuffled orders.

## How it was measured
The share right per subject, with 90% intervals, and grouped into basic science (anatomy, physiology, pathology, pharmacology, microbiology and similar) and clinical subjects.

## Caveats
- **Exam keys have errors.** MedMCQA's answer keys come from exam prep material and contain some mistakes, which make Jev look worse on the subjects where keys are shakiest.
- **Indian exams, Indian practice.** These are questions from India's postgraduate medical entrance exams (AIIMS and NEET PG). Some clinical answers follow Indian guidelines and textbooks, which can differ from other countries' practice.
- **Exam knowledge, not clinical skill.** Picking an option on an exam is not diagnosing a patient. Nothing here is medical advice.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
