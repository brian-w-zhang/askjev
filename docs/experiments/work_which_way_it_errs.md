# work_which_way_it_errs

family: work

## Why ask this
A checker that's right 85% of the time can still be dangerous if all its mistakes go one way. One that waves bad work through needs a person reviewing its passes; one that cries wolf buries people in false alarms. Before you put a model in charge of a check, you want to know which way it leans.

Jev is used for exactly these checks (is this answer supported, is this log line trouble, do these two records match), so this study measured its lean across dozens of them.

## The people and the data
- **Is this work good enough?** A helpful review, a correct math answer, a genuine hotel review, a tool call made correctly, a coding agent that finished its task.
- **Is every claim supported?** A summary backed by its article, a chatbot reply with no invented facts, a docstring that fits its code.
- **Are these a match?** Two methods that do the same job, two records for the same person, a passage that answers a question.
- **Is something wrong here?** A log line that needs an admin, a toxic comment, a phishing email, a security bug.

The right answers come from each dataset's creators: crowd annotators, experts, the systems that produced the logs, or the people who wrote the fakes.

## What Jev was asked
Each check was a yes/no question over a real input (the wording below is lightly shortened). For example, for hotel reviews:

> Was this review written by a guest who actually stayed at the hotel? *(the review text follows)*

Or for code:

> Do these two Java methods implement the same functionality? *(both methods follow)*

## How it was measured
For each task, the **lean**: the share of items Jev passes (or flags, for "something wrong") minus the share the right answers pass (or flag). Zero means no lean. The lean is averaged within each kind, with a range showing how much it could vary by chance.

## Caveats
- **A chosen grouping.** The four kinds of question (good enough, supported, a match, something wrong) are a hand grouping of 46 tasks made for this project. A different grouping could blur or sharpen the pattern; the per-task leans don't depend on it.
- **Some checks are hard for people too.** The fake hotel reviews were written by paid crowd workers to fool readers, and in the original study human judges were close to chance at spotting them. Jev's miss there is a hard task, not only a lenient one.
- **Math is a known weak spot.** Checking whether a math answer is right leans on arithmetic, which TypeSafe documents as a Jev limit. It's shown for completeness, not as a discovery.
- **How the wrong answers were made.** Several datasets built their "bad" cases by hand or by rule: math answers nudged by a digit, fake reviews written to order. A lean can partly reflect how obvious those constructed errors are.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
