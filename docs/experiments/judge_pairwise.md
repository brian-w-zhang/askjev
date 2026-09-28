# judge_pairwise

family: judge

## Why ask this
Models are routinely used to grade other models: which of two chatbot answers is better? It's cheap and fast, and the worry is always the same. Model judges are said to prefer the longer answer, and to prefer whichever answer comes first (or second) regardless of quality.

The fair question isn't whether Jev has those leans, but whether it has them **more than human judges do**. People like longer answers too. If Jev's taste for length matches theirs, it's a faithful stand-in; if it's stronger, it's an extra bias.

## The people and the data
Two public sets of human judgments on pairs of AI answers:
- **HelpSteer2 (NVIDIA):** real user prompts, mostly from shared ChatGPT conversations, each answered twice by models, with 3 to 5 hired annotators saying which answer is better.
- **MT-Bench:** multi-turn conversations with six models, judged pair by pair by experts and the benchmark's authors.

## What Jev was asked
The whole conversation and both answers, then:

> Which of the two AI assistant responses, [response 1] or [response 2], is the better reply to the user's
> [prompt]?
> *The first response is the better reply · The second response is the better reply*

MT-Bench pairs were asked the same way, with two full conversations side by side.

## How we measured it
First, how often Jev picks the answer the judges picked. Then the length question: we group pairs by how much longer the first answer is than the second, and in each group compare how often Jev and the judges chose the first answer. If both rise together as the first answer gets longer, they share the same lean.

## Caveats
- **Answers in a fixed order.** The two answers always appear in the order the dataset gives them.
- **Who the judges are.** HelpSteer2's judges are annotators hired through Scale AI, 3 to 5 per pair; MT-Bench's are experts and the paper's own authors. Both groups judge AI answers for a living or for research, not as everyday users.
- **Clear preferences only.** Pairs where the judges tied or had no majority are left out, so this is agreement on pairs people could decide.
- **The answers are from other models.** Every answer being judged was written by an AI model. Jev may recognize the style of models like itself, which a human judge wouldn't.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
