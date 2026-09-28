# work_agent_patches

family: work

## Why ask this
Coding agents now attempt real bug fixes on their own: read the issue, explore the code, write a patch, submit. Running the tests to check each attempt is slow and expensive, so a natural job for a small, fast model is triage: read the agent's trace and say whether it probably fixed the issue.

Two different skills hide in that job. Telling a run that crashed or gave up from one that finished is easy: the trace says so. Telling a correct patch from a plausible wrong one is the hard part, and the only part that saves time.

## The people and the data
There are no human raters. The data are **SWE-agent trajectories** on real GitHub issues from open-source Python projects, in the style of the SWE-bench benchmark. Each trace records an agent (SWE-agent, driven by Llama-based models at 8, 70 and 405 billion parameters) working on one issue: the commands it ran, what it saw, and the patch it ended with. The label says whether that final patch passed the tests that check the fix.

## What Jev was asked
Each trace was one yes/no question:

> Did the agent in the trace complete the task it was given?
> *The agent's final change actually resolves the issue it was asked to fix · The agent gave up, ran out of room, or
> submitted a change that does not resolve the issue*
> *(the trace follows: the GitHub issue, then the agent's final steps and what it saw)*

## How it was measured
The share Jev got right, split by how the run ended: runs that submitted a patch, where Jev has to judge the patch, and runs that ended any other way, where the trace itself gives the answer away.

## Caveats
- **Jev saw a shortened trace.** Agent traces run for pages. Judging a patch it can only partly see is hard for anyone; this measures triage from a summary-length view.
- **One kind of agent.** All runs come from SWE-agent driven by Llama-based models of three sizes. Traces from other agents look different, and so do their failure modes.
- **The tests decide "fixed".** A run counts as fixed if its patch passed the benchmark's tests. Some patches that pass are still poor, and some good patches fail on test details, so the labels themselves aren't perfect judgments of quality.
- **A long-context weak spot.** Picking the relevant parts out of a long, noisy input is a limit TypeSafe documents for Jev; the trace is exactly that kind of input.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
