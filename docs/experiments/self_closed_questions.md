# self_closed_questions

family: self

## Why ask this
People ask models yes/no questions all day, many with no settled answer: "Will this ever work?", "Can I fix this myself?", "Was that a mistake?". On questions like these the model's answer is a lean, not a looked-up fact.

If the way a question starts predicts that lean, then asking "can it happen?" instead of "will it happen?" changes the answer someone walks away with. That's a habit worth knowing before trusting a model's yes or no.

## The people and the data
The questions are real, written by people in four public places: Stack Exchange (56 non-programming sites such as travel, cooking and English usage), Quora, Yahoo Answers, and the first messages people sent to chatbots (WildChat and a few similar public collections).

## What Jev was asked
Each question exactly as the person wrote it, as a yes/no question:

> Do pilots use flaps during take-off?
> Will the USC Trojans make it a 3-Peat in College Football?
> Can you say "two groups of people stared at each other"?

## How it was measured
Also the share where Jev sits within 10 points of 50/50.

## Caveats
- **No answer key.** These are real questions with no verified answers, so there's no way to tell whether "Will...?" questions really deserve more no's. What this measures is Jev's default, not its accuracy.
- **The word travels with the topic.** "Will...?" questions are about the future and "Can...?" questions are often about what's possible, so the opening word and the subject come together. This shows a pattern, not its cause; paired rewordings of the same question separate the two (see "'Could you?' gets a yes that 'Would you?' doesn't").
- **Filtered questions.** Questions were kept only if they stand alone as one clear yes/no question: no personal pronouns, no homework math, nothing needing context or dated. Religion and politics sites were left out, and a content filter hides political and sensitive questions from the site.
- **Mostly Stack Exchange.** About two thirds of the questions come from Stack Exchange's non-programming sites (travel, cooking, English usage, DIY...), so its topics weigh most.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
