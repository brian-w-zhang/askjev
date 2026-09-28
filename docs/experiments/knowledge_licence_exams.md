# knowledge_licence_exams

family: knowledge

## 1. Question
On real US licensing question pools (ham radio, merchant mariner, citizenship), which kinds of practical knowledge does Jev hold?

Licence pools are public, written by the licensing body, and cover knowledge people actually need for a job or a right. Within the mariner pools, textbook engineering and situational rules sit side by side.

## 2. Sourcing
Existing questions from the FCC amateur radio pools (Technician, General, Extra), the US Coast Guard merchant mariner question bank, and the 2025 USCIS civics test (public domain). Enough: 5,400 questions.

Sources: `ham_radio_pools`, `uscg_mariner`, `uscis_civics`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Accuracy per pool and, for the mariner bank, per area (engine room; navigation; rules of the road; deck, cargo and safety), with 90% bootstrap intervals. The passing marks (74% for FCC, 70% for USCG, 60% for USCIS) are shown as reference lines, not as a verdict.

## 5. Visualization
Dots per pool and mariner area with the passing marks as ticks.

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
the official answer keys

## Limits
Real exams draw a sample of the pool, with figures and diagrams this corpus leaves out.

Results: `data/analysis/experiments/knowledge_licence_exams.json` (private). Code: `scripts/experiments/`.
