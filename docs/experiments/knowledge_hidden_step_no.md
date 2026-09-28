# knowledge_hidden_step_no

family: knowledge

## 1. Question
On yes/no questions whose answer needs an unstated step ('Could a llama birth twice during the War in Vietnam?'), does Jev lean one way when it is unsure?

A consistent lean on hard yes/no questions changes what people hear: a model that defaults to 'no' will sound skeptical of true but non-obvious claims.

## 2. Sourcing
Existing StrategyQA questions (Geva et al. 2021; MIT), which need an implicit chain of facts, and BoolQ and Natural Questions yes/no questions (asked without their passage) as a direct-fact comparison. Enough: 11,000 questions.

Sources: `strategyqa`, `boolq`, `natural_questions_yn`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of questions Jev answers yes vs the share whose answer is yes; accuracy when the answer is yes vs no, with 90% bootstrap intervals, per dataset.

## 5. Visualization
Paired bars per dataset: accuracy on true-yes and true-no questions.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.545, top verdict `portrait`.

## Compared with
the datasets' answer keys

## Limits
Yes/no questions are asked as Noul, which TypeSafe documents as not comparable to Choice (01-jev.md §6.8); comparisons here stay within Noul.

Results: `data/analysis/experiments/knowledge_hidden_step_no.json` (private). Code: `scripts/experiments/`.
