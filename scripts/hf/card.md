---
license: {{license}}
language:
- en
pretty_name: askjev
size_categories:
- 1M<n<10M
task_categories:
- question-answering
- text-classification
tags:
- jev
- typesafe
- model-behavior
- calibration
- human-comparison
- closed-questions
configs:
{{configs}}
---

# askjev

About a million closed questions (yes/no, pick one, rate on a scale), each placed on a topic tree and answered by
**Jev**, TypeSafe AI's System One model, several times under different framings. Alongside the answers are the
annotations about each question (is it objective? ambiguous? does the answer survive a shuffle? how far is Jev from
people?), the tree itself, real human answer distributions where they exist, and 192 experiments built on top.

It's for understanding Jev: what it can do, what its defaults are, and where its judgments are uneven. **It is not a
benchmark.** There's no aggregate score and nothing here ranks models. The numbers are indicators, meant to be read
per topic and per question.

The questions come from about 270 public sources, templates over public data (Wikidata, World Bank, MovieLens titles…),
and questions written for the project (drafted with Claude Opus 5.5). Every row says where it came
from and under what license.

## Terms

- **node**: a topic in the tree (`tree`), in three hemispheres: **world** (facts and opinions about the world),
  **self** (the answerer's own defaults, taste and values), **machine** (Jev's real jobs: classify, verify, route…).
- **question**: one canonical question (text + options + optional `state`, the input it's about), attached to one
  node. Questions are never tree nodes.
- **probe**: what was actually sent: question × frame × variant.
  - frame `self`: asked as written; `human`: "what would most people answer?"; `none`: machine questions, no frame.
  - variant `base`: options in the original order; `shuffle`: options reordered (`variant_params.i`, three per
    question); `reversed_levels`: a Score scale flipped end to end.
- **answer**: Jev's response to one probe, a probability over the options.
- Question types (`primitive`): **noul** (yes/no, one probability), **choice** (one of N options), **score**
  (a level on a described scale).

## Tables

| config | rows | what |
|---|---|---|
| `questions` | {{n_questions}} | the questions: text, options, state, node, kind, source, license, truth when known |
| `answers` | {{n_answers}} | one row per probe: frame, variant, option order, Jev's distribution, confidence |
| `question_meta` | {{n_question_meta}} | indicators about each question (below) |
| `tree` | {{n_tree}} | the topic tree: path, label, description, what a node is not for, examples |
| `placements` | {{n_placements}} | how Jev placed each question on the tree, with confidence and the runner-up |
| `human_dists` | {{n_human_dists}} | observed human answer distributions (surveys, polls, ratings), with population and n |
| `experiments` | {{n_experiments}} | experiments: the question, method, result, limits, the question ids used, write-up |
| `calls_sample` | {{n_calls_sample}} | a few raw gateway calls per job, exactly as sent and returned |

```python
from datasets import load_dataset
q = load_dataset("brian-w-zhang/askjev", "questions", split="train")
a = load_dataset("brian-w-zhang/askjev", "answers", split="train")
```

JSON-valued fields (`options`, `state`, `truth`, `meta`, `distribution`, `option_order`, `variant_params`,
`path_probs`, experiment `chart`/`take`/`evaluation`) are stored as JSON strings; `json.loads` them.

### `question_meta` indicators

| field | meaning |
|---|---|
| `top`, `p_top`, `margin`, `entropy`, `confidence` | Jev's as-asked answer: top option, its probability, gap to second, spread, and the API's confidence |
| `top_h`, `p_top_h` | the same for the "most people" frame |
| `objective`, `disagreement`, `ambiguous`, `reveals_self` | Jev judging the question itself: single right answer? would thoughtful people disagree? underspecified? would an answer reveal someone's values? |
| `stability` | agreement of the top answer across three option shuffles |
| `frame_gap` | total variation distance between the self and "most people" answers |
| `human_gap` | total variation distance from the observed human distribution |
| `correct`, `brier` | against ground truth, where there is one |
| `placement_conf`, `separation` | how sure the tree placement was (separation near 1× means two topics were equally good) |
| `universe_invariance`, `noise` | measured on sampled subsets only; mostly empty |

## How it was collected

- Jev (`typesafe-ai/jev`) through the Vercel AI Gateway, September 2026. The served model is recorded on every
  answer (`model_served`). Every request was cached by hash and sent once; the first response is canonical.
- Jev has no temperature or seed. Measured repeat noise: Noul std about 0.01, Choice top-probability std about 0.02;
  near-tie choices can flip. Treat differences smaller than that as noise.
- Questions were placed on the tree by Jev walking it from the root, choosing among each node's children.
- Questions that flagged as contested politics or sensitive are **not included** in any table.

## What's withheld, and why

The dataset is released non-commercially (CC BY-NC-SA 4.0) because several sources are. Most rows ship in full.
Two exceptions, where the source's terms don't allow redistribution:

- **Yahoo Answers** (`source` = `yahoo_closed`, `yahoo_topics`): the words from Yahoo are blank
  (`redistribution` = `text_withheld`; `text` for yahoo_closed, `state` for yahoo_topics). Everything else about
  those questions ships: node, options, Jev's answers, indicators. `restore_ref` names the row in
  [`community-datasets/yahoo_answers_topics`](https://huggingface.co/datasets/community-datasets/yahoo_answers_topics),
  and `restore_yahoo.py` in this repo fills the words back in.
- **MovieLens and Last.fm** human ratings: those `human_dists` rows are left out
  (`questions.human_data_withheld` marks the questions). The questions and Jev's answers ship.

Reddit poll questions and Quora questions ship in full, with attribution, as is common for research datasets built
from those archives. If you wrote something here and want it removed, open a discussion on this repo and it will be.

Per-row licenses are in `questions.license`; cite the original sources listed there when you use their rows.

## Limits

- One model, one month. Jev is served, not pinned, and may change.
- The mix of questions is designed (quotas per kind and topic), not a sample of what people ask.
- Some `human_dists` compare Jev with a population that answered a slightly different wording.
- Indicators are per question. A topic's average hides what's inside it.

## Citation

```bibtex
@misc{zhang2026askjev,
  author = {Brian Zhang},
  title  = {askjev: a million closed questions answered by Jev},
  year   = {2026},
  howpublished = {\url{https://huggingface.co/datasets/brian-w-zhang/askjev}}
}
```
