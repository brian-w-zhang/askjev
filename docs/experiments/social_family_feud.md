# social_family_feud

family: social

## 1. Question
Given the answers a Family Feud survey got ('Name something a knight needs for a jousting match'), does Jev pick the one most people said first?

Family Feud rewards the most common answer, not the best one. Guessing it takes a model of ordinary people's first thoughts, which is different from knowing the right answer.

## 2. Sourcing
Existing ProtoQA questions (Boratko et al. 2020, scraped Family Feud surveys of about 100 people): 'Which of these would most people name first' with the survey's answer clusters as options and their counts as the human distribution. Enough for a clear rate, not for subgroups: 146 questions.

Sources: `protoqa`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
How often Jev's top pick is the survey's number one answer, against the chance rate (1 over the number of options); the rank of Jev's pick in the survey; the biggest misses, where the survey's favorite was far ahead. 90% bootstrap interval over questions.

## 5. Visualization
A bar of where Jev's pick ranked in the survey (1st to 6th), with the chance line; a list of the biggest misses.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.96, top verdict `portrait`.

## Compared with
Family Feud survey respondents (about 100 per question)

## Limits
146 questions; answer clusters were grouped by ProtoQA's authors. The show's surveys are American.

Results: `data/analysis/experiments/social_family_feud.json` (private). Code: `scripts/experiments/`.
