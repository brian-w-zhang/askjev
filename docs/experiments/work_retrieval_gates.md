# work_retrieval_gates

family: work

## Why ask this
Systems that answer questions from documents usually retrieve a pile of passages and then decide which ones go into the expensive model's context. A cheap model as the gate is a natural fit.

Its two kinds of error cost differently. Letting in useless passages wastes context and can distract. Throwing out a useful one can make the right answer impossible, especially for questions that chain two facts: to answer "which company owns the supermarket chain where she worked?", the paragraph naming the chain matters even though it doesn't contain the answer.

## The people and the data
- **MS MARCO:** real web search queries (from Microsoft) with passages retrieved from web pages; the passage a human annotator used for the answer is marked useful.
- **HotpotQA:** questions that need two facts from two Wikipedia paragraphs, mixed with distractor paragraphs on the same topic.
- **QNLI:** a question and a single Wikipedia sentence that does or doesn't answer it.

## What Jev was asked
Each item was a yes/no question over a passage and a question. For HotpotQA (MS MARCO and QNLI ask "does the passage contain an answer to the query?"):

> Should the passage go into the context for answering the question?
> *The passage states a fact that is needed to answer the question · The passage may be on a related topic, but
> nothing in it is needed to answer the question*
> *(the question and the passage follow, for example a paragraph about Golub Corporation, the parent company of Price
> Chopper Supermarkets)*

That paragraph is one of the two a question needs; Jev leaned toward leaving it out.

## How it was measured
For each dataset, two error rates: the share of useful passages Jev rejects, and the share of useless passages it lets in.

## Caveats
- **Web search labels are partial.** In MS MARCO, a passage is marked useful if the human annotator used it to write the answer. Other passages that also answer the query are marked not useful, so some of Jev's "let in" errors are passages that do help.
- **"Needed" is subtle for two-step questions.** A HotpotQA question often needs a "bridge" paragraph that names an entity without stating the answer. A guess, not measured here, is that Jev reads "needed" as "contains the answer" and throws those out.
- **Question wording.** For HotpotQA the question asked whether the passage states a fact needed to answer the question. A wording that mentioned intermediate steps might change the result.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
