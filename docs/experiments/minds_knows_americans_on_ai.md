# minds_knows_americans_on_ai

family: minds

## 1. Question
Asked what most people would answer to Pew's AI questions, does Jev get Americans' wariness right, or does it paint them as keener (or warier) than they are?

Separate from its own view, a model's picture of public opinion about AI shapes how it talks to people about AI. The Pew toplines give the real answer.

## 2. Sourcing
New questions (sources/ai_attitudes): 22 of the 26 non-political items from Pew Research Center's June 2025 survey of 5,023 US adults (outlook, trust, AI's effect on people's abilities, where AI should play a role, how it feels to find out something was made by AI), asked in Pew's wording with Pew's answers, 'Not sure' included where Pew offered it.

Sources: `ai_attitudes`

## 3. Collection
The 'most people' answers to the same 26 new questions (no extra calls).

## 4. Scoring
Per item, the wary share in Jev's 'most people' answer vs Americans'; mean difference with a 90% bootstrap interval over items; rank correlation over items; the biggest misreadings.

## 5. Visualization
Paired dots per item: Americans' wary share and Jev's guess of it.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.15, top verdict `portrait`.

## Compared with
US adults (Pew American Trends Panel, June 2025, N=5,023)

## Limits
Pew's questions ask 'you'; for Jev, 'you' is an AI answering about AI, which is the point but also means some items read differently. Shares transcribed from Pew's topline. The question screen hid 13 of the 26 items (among them the overall concern, risk and benefit ratings), so the comparison rests on 10 scored items.

Results: `data/analysis/experiments/minds_knows_americans_on_ai.json` (private). Code: `scripts/experiments/`.
