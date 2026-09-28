# knowledge_medicine_clinic

family: knowledge

## Why ask this
Medicine is where people most want a model to be right, and where confident wrong answers do the most harm. Splitting a large medical exam by subject shows where Jev's knowledge is solid (the science underneath) and where it thins (the specialties), and whether its confidence tracks that.

## The people and the data


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
