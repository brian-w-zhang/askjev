# Vision

## One line
A tree that has a place for every closed question a human or a program could ask
(yes/no, pick one, rate on a scale), filled with a balanced sample of real
questions answered by Jev, TypeSafe AI's System One model. It's for
**understanding Jev**: what it can do, what its defaults ("personality") are, and
where its judgments are jagged.

## What it is, and what it isn't
- **Not a benchmark, not a leaderboard.** There's no aggregate score for Jev. Every
  node shows *indicators* (stability, calibration, human gap, frame gap, placement
  confidence, defaults); see `02-tree.md` §1.
- **Capabilities + personality + jaggedness.** Machine-side questions show how Jev
  behaves on its real use cases. Self-side questions show its defaults. World-side
  questions show breadth, and with ground truth, calibration by topic.
- **Findings are the substance, the map is the packaging.** The deliverable that
  matters is 3-5 concrete, reproducible jaggedness findings. The tree and the
  sunburst make 100k-1M answers browsable and make the findings visceral.

## Three layers, in order of importance
1. **Jaggedness findings.** Controlled perturbations (rewording universes, option
   shuffle, order swap, decoys, self vs human frame) plus ground truth and human
   data. See `05-experiments.md`.
2. **The map.** Three hemispheres (World / Self / Machine), 28 L1 roots, and Jev
   traversal for placement, search, and growth. See `02-tree.md`.
3. **Asking new questions.** Anyone with access can pose a Noul, Choice, or Score
   question. Jev places it on the tree, answers it in both frames, and stress-tests it.
   Private for now (`07-ui.md`).

## Audience and visibility
- **Private.** Only Brian and the TypeSafe team see it. That's why non-commercial
  and unclear-license datasets are usable (`04-datasets.md`). Going public would
  need TypeSafe's OK (including for the "Jev" name, MCA §16.4) and a license
  re-review.
- **Primary audience: TypeSafe** (Diogo Almeida, Sasha Sheng, Erik Gafni). The goal
  is to become their first intern. The artifact should read as "work you'd hire
  someone to do, already done." In the Latent Space interview Diogo says they're
  hiring "infinite data people" to find jaggedness and fix it surgically, and
  that's this project. Outreach plan: `resources/references/notion/become-typesafe-first-intern.md`.

## Why Jev
- It returns calibrated distributions, not text, so "how confident, how stable,
  how human" is measurable per question.
- $0.042 per 1M input tokens with free output: 1M questions costs tens of dollars. The
  design is bounded by ideas, not budget ("one power user's for loop").
- Code is the consumer. The pipeline is a for loop, and Jev stays in the background.

## Framing rules (non-negotiable)
- **Indicators, never grades.** No single score, no ranking against other models.
- **Defaults, not preferences.** "Jev's personality" results are reported as defaults,
  and only claimed if they survive paraphrasing. `mined` questions (selected for
  instability) never count toward personality claims.
- **No contested politics on the map.** Such items can be measured, but they're flagged and hidden.
- **Score answers are shown as bands**, never as fake-precise interpolated numbers.
- **Don't re-announce TypeSafe's documented jaggedness as a discovery**
  (`01-jev.md` §6). Quantify it at scale, or go beyond it.
- **Private first.** Findings go to TypeSafe before anything else.

## Success
- A findings write-up: 3-5 jagged edges, each with the phenomenon, an exact repro,
  magnitude across N items, the noise floor, and a hypothesis about a general fix.
- A working private site: the sunburst over the tree, question cards with indicators,
  and an ask box.
- A reply from TypeSafe.

## Non-goals
- Questions that need arithmetic, counting, exact numbers, or date comparison (known
  Jev weak spots), except in an experiment that targets those weak spots on purpose.
  Factual questions *are* in scope when they're categorical (see `03-questions.md`).
- Category-rewrite demos (semantic codec, CA physics, and similar). They're parked and
  logged in `resources/conversations/`.
- A public launch. That's a later decision, made with TypeSafe.
