# work_icd_coding_rules

family: work

## Why ask this
Medical coding turns a diagnosis into a code from ICD-10, the classification hospitals and insurers use for billing and statistics. It's a common job for AI, and it follows rules that aren't purely medical. The clearest example: how an injury happened (a fall from a ladder, a car crash, a dog bite) is coded in its own chapter, **external causes**, separate from the injury itself (a fractured wrist goes in the injury chapter).

A model that reasons from the medicine will file "fell from a ladder" with the injury. A coder won't. That's a clean test of whether Jev knows the domain's conventions or just the domain.

## The people and the data
No people: the answer key is the code book itself.

## What Jev was asked
Each code was one pick-one question with the chapters' official titles:

> Which ICD-10-CM chapter does the diagnosis belong to?
> *Diagnosis: "Driver of bus injured in collision with unspecified motor vehicles in traffic accident, initial
> encounter"*
> *Options: the 21 chapter titles, from "Certain infectious and parasitic diseases" to "External causes of
> morbidity" and "Factors influencing health status and contact with health services"*

## How it was measured
The share of codes Jev places in the right chapter, chapter by chapter, and the most common wrong chapter for each.

## Caveats
- **Descriptions only.** Jev saw each code's official one-line description, not a patient record. Real coding starts from clinical notes, where the circumstances of an injury may be spelled out or missing.
- **The chapter names are what Jev had.** A human coder learns that "how it happened" has its own chapter; from the titles alone that rule isn't obvious.
- **About 95 codes per chapter.** Each chapter is represented by about 95 codes, spread across its categories. Per-chapter shares are rough to a few points.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
