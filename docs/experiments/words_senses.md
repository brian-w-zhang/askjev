# words_senses

family: words

## Why ask this
How do you know a "mustache"? Mostly by seeing it. "Thunder"? By hearing. "Velvet"? By touch. The **Lancaster Sensorimotor Norms** asked people how much they experience tens of thousands of words through each sense, and the answers describe how grounded words are in the body: for most concrete words, sight dominates.

A model has no senses. It knows words from text, where the look of things is rarely described because everyone can see it. Which sense it misjudges most is a clue to what text leaves out.

## The people and the data
The Lancaster Sensorimotor Norms (Lynott and colleagues, 2020) cover 39,707 English words, rated by online participants in the US and UK, recruited through Mechanical Turk and Prolific, on how much they experience each word through sight, hearing, touch, taste and smell, on a scale from 0 (not at all) to 5 (greatly). The study uses about 1,980 concrete, common words per sense. A second set of questions uses the same norms to ask which single sense dominates a word, where one clearly does.

## What Jev was asked
One question per word and sense, with five described answers written for this project:

> How much do you experience "mustache" by seeing?
> *Not at all: seeing plays no part in experiencing it · Slightly: its sight comes up only now and then, as a minor
> detail · Moderately: its sight is one noticeable part of experiencing it, alongside others · Strongly: its sight
> is one of the main ways I experience it · Greatly: seeing is central to experiencing it; its sight is what it is
> mostly about*

Plus 1,131 questions like "Through which sense do you mostly experience ...?", with sight, hearing, touch, taste, smell and body sensation as the options. Each was also asked with the answers reversed or shuffled, and averaged.

## How it was measured
For each sense, Jev's average rating on the 0 to 5 scale next to people's, and how closely the two rankings of words agree (a rank correlation: 1 means the same order). For the dominant-sense questions, how often Jev names the sense the norms say dominates.

## Caveats
- **A mapped scale.** Jev's levels are mapped onto 0 to 5 evenly. The sight gap is too large to be a mapping artifact, and the rankings, which don't use the mapping, point the same way.
- **"You" is a model.** The question asks "how much do you experience" the word. Jev has no senses; it may be answering how much the word's meaning is about seeing, which is a different question from how people experience it.
- **The level wording.** The levels describe sight as "one of the main ways I experience it" or "what it is mostly about". Jev may reserve those for words that are about seeing (colors, views) rather than things people mostly know by looking at them.
- **Averages only.** The norms publish averages per word, not each rater's answer, so the comparison uses averages.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
