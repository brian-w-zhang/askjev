# society_profession_honesty

family: society · new questions: 16

## 1. Question
Rating the honesty and ethical standards of nurses, pharmacists, bankers, car salespeople and a dozen other professions, does Jev see the same ladder of trust as Americans, and is it more or less generous?

Gallup has asked Americans this every year since 1976; it is the standard picture of which jobs people trust. A model that talks about professions all day carries its own picture, which may be kinder or harsher than the public's.

## 2. Sourcing
New questions (sources/gallup_honesty): Gallup's wording, 'How would you rate the honesty and ethical standards of people in this field: <profession>?', with its five answers, for 16 professions in the December 2025 poll; the human distribution is Gallup's published split.

Sources: `gallup_honesty`

## 3. Collection
16 new questions, each asked as written, for 'most Americans', and with the levels reversed (averaged).

## 4. Scoring
Per profession, the share rating it high or very high, Jev (its probability on the top two levels) vs Americans; rank correlation of the expected levels over professions; the mean gap with a 90% bootstrap interval; the professions with the largest gaps; Jev's guess for 'most Americans' scored the same way.

## 5. Visualization
Dots per profession: Americans' share rating it high or very high (diamond) and Jev's (square), sorted by Americans'.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.762, top verdict `portrait`.

## Compared with
US adults (Gallup Honesty and Ethics poll, December 2025)

## Limits
Gallup asks US adults by phone and online; 'no opinion' answers are dropped. Politics and religion are left out: members of Congress, journalists, police officers, clergy and labor union leaders. The five answers are Gallup's own degree words.

Results: `data/analysis/experiments/society_profession_honesty.json` (private). Code: `scripts/experiments/`.
