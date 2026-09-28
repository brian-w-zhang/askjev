# work_function_call_checks

family: work

## 1. Question
Checking whether a proposed function call does what the user asked, which kinds of mistakes does Jev catch: the wrong function, a missing argument, a wrong value, or two arguments swapped?

Agents call tools; a cheap verifier in front of the call is an obvious safety net. Its blind spot is where the net has a hole.

## 2. Sourcing
Existing verify-the-call questions built from xLAM function-calling data: half the calls are the dataset's correct ones, half have one perturbation of a known kind.

Sources: `function_calls`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Share of each perturbation kind Jev rejects, and the share of correct calls it accepts, with 90% intervals.

## 5. Visualization
Bars: the share caught per kind of mistake, and correct calls accepted.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.384, top verdict `portrait`.

## Compared with
the dataset's correct calls and the known perturbation

## Limits
Only 45 swapped-argument calls survived the build (swaps need two arguments of the same type), so that bar is the least certain.

Results: `data/analysis/experiments/work_function_call_checks.json` (private). Code: `scripts/experiments/`.
