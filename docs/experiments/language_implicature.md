# language_implicature

family: language · new questions: 234

## 1. Question
When someone says the food is 'good', do you conclude they think it's not excellent? People draw that inference for some word pairs and not others; does Jev draw it for the same ones?

'Scalar diversity' is one of the best-documented facts in pragmatics: 'some' almost always implies 'not all', 'pretty' almost never implies 'not beautiful'. Reading what people mean beyond what they say is what a language model is for, and here there are exact human rates per word pair.

## 2. Sourcing
New questions (sources/scalar_implicature): 'Mary says: "The food is good." Would you conclude from this that, according to Mary, the food is not excellent?' for 43 scales from van Tiel et al. 2016 (three sentences each, as in the study), 70 from Gotzner et al. 2018 and 50 from Pankratz & van Tiel 2021, each with the study's share of people who said yes.

Sources: `scalar_implicature`

## 3. Collection
234 new yes/no questions, each asked as written and for 'most people'.

## 4. Scoring
Per scale (van Tiel's three sentences averaged), Jev's probability of yes vs people's rate: rank correlation with a 90% bootstrap interval, mean level, and spread across scales (does Jev show the diversity, or one rate for everything?). By word class (adjectives vs verbs and quantifiers). The scales with the biggest gaps. Jev's 'most people' answer is scored the same way.

## 5. Visualization
A scatter: people's rate (x) vs Jev's probability (y), one dot per scale, colored by study, diagonal, with the largest gaps labeled.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.303, top verdict `portrait`.

## Compared with
Participants in van Tiel et al. 2016, Gotzner et al. 2018 and Pankratz & van Tiel 2021

## Limits
Rates were collected in different studies with different participant pools; each is one number per scale. van Tiel's three sentences share one human rate. The question asks for an inference that people may draw but not endorse, and Jev answers the literal question (a documented tendency, 01-jev §6 item 1).

Results: `data/analysis/experiments/language_implicature.json` (private). Code: `scripts/experiments/`.
