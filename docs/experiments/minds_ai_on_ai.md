# minds_ai_on_ai

family: minds · new questions: 26

## 1. Question
Asked Pew's questions about AI (is it more worrying than exciting, should it help develop medicines, would you like a song less if AI made it), is Jev warier of AI than Americans or less?

Americans are wary of AI and getting warier. A model answering about its own kind could defend it, echo the public's worry, or hedge; which one, and where, is a direct look at how it has been taught to talk about itself.

## 2. Sourcing
New questions (sources/ai_attitudes): 22 of the 26 non-political items from Pew Research Center's June 2025 survey of 5,023 US adults (outlook, trust, AI's effect on people's abilities, where AI should play a role, how it feels to find out something was made by AI), asked in Pew's wording with Pew's answers, 'Not sure' included where Pew offered it.

Sources: `ai_attitudes`

## 3. Collection
26 new questions, each asked as written, for 'most people', and with the options in three shuffled orders (averaged).

## 4. Scoring
Per item, the share on the wary answer(s) (e.g. 'more concerned than excited', 'like the painting less', 'AI should play no role') for Jev and for Americans; the mean difference with a 90% bootstrap interval over items; the items where they differ most.

## 5. Visualization
Paired dots, one row per item: Americans' wary share and Jev's, with Jev's guess of Americans.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.707, top verdict `portrait`.

## Compared with
US adults (Pew American Trends Panel, June 2025, N=5,023)

## Limits
Pew's questions ask 'you'; for Jev, 'you' is an AI answering about AI, which is the point but also means some items read differently. Shares transcribed from Pew's topline. The question screen hid 13 of the 26 items (among them the overall concern, risk and benefit ratings), so the comparison rests on 10 scored items.

Results: `data/analysis/experiments/minds_ai_on_ai.json` (private). Code: `scripts/experiments/`.
