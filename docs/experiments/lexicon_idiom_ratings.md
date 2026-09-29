# lexicon_idiom_ratings

family: lexicon

## Why ask this
People read idioms using two quick judgments. Is this a phrase I know? And could it make sense word for word? "Kick the bucket" could literally happen; "rain cats and dogs" couldn't. Those two ratings predict how fast people read idioms and how easily they fall back on the literal meaning.

A model that misjudges which idioms are familiar will use rare ones as if everyone knows them, or explain common ones needlessly. And one that misjudges literal plausibility may read a figure of speech too literally, or miss a literal reading.

## The people and the data
The ratings come from **Bulkes and Tanner (2017)**, who normed 870 American English idioms with about 100 US adults per idiom and per rating: how familiar each idiom is, and how plausible it is taken literally, each on a 1-to-5 scale.

## What Jev was asked
Two questions per idiom, each with five described levels:

> How familiar is the idiom "Wear more than one hat"?
> *I have never come across it: it means nothing to me · I may have seen it once or twice, but I'm not sure what it
> means · I have come across it now and then · I hear or read it fairly often · I know it very well: it comes up all
> the time*

> Taken literally, word for word, how plausible is "Be someone's better half"?
> *Taken word for word it makes no sense at all · ... · Taken word for word it describes something ordinary and
> common*

Each was asked as written, for "most people", and with the levels reversed.

## How it was measured
For each rating, whether Jev ranks the idioms in the same order as people's averages (rank correlation: 1 means the same order, 0 no relation), with 90% intervals, and the idioms whose rank moves most.

## Caveats
- **People's side is an average only.** So only the rankings are compared, and the named idioms are those whose rank moves most.
- **The project's answer levels.** People rated on a plain 1-to-5 scale. Jev got five described levels written for this project, for familiarity in terms of how often you meet the idiom ("I hear or read it fairly often"). For a model, "how often have you met this" is a strange question; its answer may track how common the phrase is in text, not in speech.
- **The idioms come in a stiff form.** Each idiom is listed as the study lists it, often with "be" or "get" in front ("Be a close call", "Be someone's better half"). The unnatural form may make familiar idioms look less familiar to Jev.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
