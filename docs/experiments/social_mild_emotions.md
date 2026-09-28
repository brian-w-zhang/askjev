# social_mild_emotions

family: social

## Why ask this
Feelings come in strengths. Furious is more than angry, terrified is more than afraid, devastated is more than sad. When a reader picks the milder word, it quietly turns the volume down on what the person said.

That matters for any model that summarizes feedback, triages messages or writes back to people: if it hears fury as annoyance and terror as worry, its summaries will read calmer than the people who wrote them.

## The people and the data
**EmpatheticDialogues**, a dataset from Facebook AI researchers: crowd workers were each given one of 32 emotion words and wrote a short situation from their own life in which they felt it. Three of the 32 come in a strong and a mild version of the same feeling: furious and angry, terrified and afraid, devastated and sad.

## What Jev was asked
The situation, and all 32 words to choose from:

> Someone wrote [situation] about a time in their own life. Which emotion were they feeling?
> *sad · angry · proud · afraid · caring · guilty · joyful · ... · furious · ... · terrified · devastated · ...*
> (32 words in all)

For example, someone wrote under "furious": "I won tickets to a concert and when we got there, they were supposed to have the tickets at the box office and they didn't so the refused us no matter how much proof we gave that we won.

## How we measured it
For each pair, how many stories written for the strong word Jev calls by the mild one, and how many written for the mild word it calls by the strong one. Across all 32 words, we also compare how often Jev uses each word with how often writers were given it.

## Caveats
- **A story written to a word.** Each writer was handed an emotion word and asked to describe a time they felt it. A story written for "furious" may genuinely read as plain anger; the label is the prompt, not a measurement of intensity.
- **No other readers to compare.** We compare Jev with the word the writer was given, not with how other people would label the same story. Other readers might soften these stories too.
- **Many near-synonyms.** With that many close options, any reader will spread its answers; what matters is that Jev's errors all go one direction.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
