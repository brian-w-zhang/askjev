# work_agent_patches

family: work

## 1. Question
Reading a coding agent's full trace on a real GitHub issue, can Jev tell whether the agent actually fixed it?

Judging agent runs is a growing use for small models (triage before tests run). Telling a crash from a submission is easy; telling a correct patch from a plausible wrong one is the job.

## 2. Sourcing
Existing questions from SWE-agent trajectories on SWE-bench issues (Llama-based agents), half resolved and half not, with the run's exit status in the data.

Sources: `swe_trajectories`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share right overall, and split by exit status: runs that ended by running out of room or giving up vs runs that submitted a patch, where Jev must judge the patch itself.

## 5. Visualization
Bars: the share right on each kind of run.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.054, top verdict `portrait`.

## Compared with
SWE-bench's own test results (resolved or not)

## Limits
Traces are long; the table keeps the first part of each (large irrelevant state is a documented weak spot, 01-jev §6 item 5).

Results: `data/analysis/experiments/work_agent_patches.json` (private). Code: `scripts/experiments/`.
