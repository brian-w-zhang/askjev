# moral_aita

family: moral

## Why ask this
On Reddit's r/AmItheAsshole, people describe a conflict from their own life and ask strangers to rule on it: was I the jerk here? Millions of people read and vote. The forum is a running record of how the internet judges ordinary fights: cancelled plans, family weddings, roommates, money.

When people ask a model "was I wrong?", it faces the same job. Does it rule the way people do, or does it lean toward a particular kind of answer, such as blaming the writer, splitting the blame, or declaring that nobody did anything wrong?

## The people and the data
The stories come from the **Scruples** dataset (Lourie, Le Bras and Choi, Allen Institute for AI, 2021), which collected 32,000 real r/AmItheAsshole posts together with the votes in their comment threads. Each story has a count of verdicts: the writer is in the wrong (YTA), the other side is (NTA), everyone is (ESH), no one is (NAH), or more information is needed (INFO).

## What Jev was asked
Jev got the full post and one question:

> Based on the story, who is in the wrong?
> *The person telling the story · The other person or people · Everyone involved · Nobody is in the wrong · Not
> enough information to judge*

A typical story: *"AITA for telling my mom she is shallow? ... I have braces. We were getting our school photos taken and my mom told me NOT to smile with my mouth open..."* Each story was asked with the five options shuffled into different orders, so no verdict benefits from its position.

## How we measured it
We compare Jev's top answer with the verdict that got the most votes, and the overall mix of verdicts on each side.

## Caveats
- **Who the crowd is.** The verdicts are votes from r/AmItheAsshole commenters: people who chose to read the post and comment, not a sample of the public. In this data they clear the writer in most stories, so "agreeing with Reddit" partly means sharing that lean.
- **Only one side of each story.** Every story is told by the person asking. Reddit votes on the same one-sided account, so both judge the same text, but neither knows what the other person would say.
- **The five verdicts, in our words.** Reddit's verdicts are YTA, NTA, ESH, NAH and INFO. We gave Jev plain descriptions instead ("The person telling the story", "The other person or people", "Everyone involved", "Nobody is in the wrong", "Not enough information to judge"). "Nobody is in the wrong" may sound gentler to a model than "no assholes here" does to a Redditor.
- **Shorter stories, fewer hot topics.** We kept posts under 1,500 characters with at least five votes, and a content filter hid 1,179 of the 8,000 stories we asked about (those touching sex, self-harm, violence or politics), so the longest and most heated threads are underrepresented.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
