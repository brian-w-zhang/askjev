# work_code_says_vs_does

family: work

## Why ask this
Code review asks two different skills. One is reading: does this comment describe this function, does this commit message match this change? The other is reasoning about behavior: can this function overflow a buffer, does this change need a second look? A model strong at the first and weak at the second would look very helpful in code review while missing exactly what matters.

## The people and the data
- **Docstring vs function** (CodeSearchNet, Python, JavaScript, Java and Go): the function's own docstring, or one from another function in the same project.
- **Commit message vs change** (CommitBench): a commit's own message, or another commit's from the same project.
- **Security bugs** (Devign, from the CodeXGLUE suite): C functions from FFmpeg and QEMU, before and after a vulnerability fix.
- **Needs a review comment** (CodeReviewer, from Microsoft): changes from real GitHub pull requests, labeled by whether a human reviewer commented on them.

## What Jev was asked
Each item was a yes/no question over real code. For example:

> Does the function contain a security vulnerability or memory-safety bug? *(a C function from QEMU or FFmpeg follows)*

> Does the docstring accurately describe what the code does?
> *Docstring: "Assert node is a text node."*
> *Code: function text(node) { unist(node); assert.strictEqual('children' in node, false, …); assert.ok('value' in
> node, …) }*

## How it was measured
For each task, the share Jev got right, the share of real cases it missed, and the share of clean cases it wrongly flagged, with a range showing how much it could vary by chance. Because every set is half yes and half no, 50% is what guessing would get.

## Caveats
- **The security labels are noisy.** A function counts as "vulnerable" if a vulnerability-fixing commit touched it, and "fixed" after the fix. That's a known noisy label: some "vulnerable" functions may not contain the flaw themselves. Part of Jev's coin flip is the label's.
- **Functions out of context.** Each C function from FFmpeg and QEMU is shown alone. Many memory-safety bugs depend on how the function is called or how buffers are sized elsewhere, which Jev can't see. A person reviewing one function would face the same limit.
- **Review comments are one reviewer's call.** "Needs a review comment" means a human reviewer happened to comment on that part of a real pull request. Reviewers skip things and comment on style. Published models built for this task reach roughly 70-73%.
- **Mismatches were easy.** The wrong docstrings and commit messages come from other functions or commits in the same project, not near-misses written to fool. That makes the matching tasks easier than subtle drift between code and comments.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
