# 13. Perception experiments

How does Jev read the words people use for amounts, chances, qualities and feelings, and how does that compare with
how people read them? Ten focused experiments, each built like the probability-words chart that started this: a
famous human dataset, the same question put to Jev, and one chart that says it all. Ten good ones beat a hundred
atlas rows. This is the research and the plan; `11-portrait.md` gets the method once they run.

## Why this direction
- **The trigger.** A tweet ran Jev on the "perception of probability" words (D. Hails, "The CIA was 'Probably'
  Right", 2026, n=99, 25 phrases: https://hails.info/writing/perception-of-probability/) and got rank agreement 0.99,
  a median gap of 3 points, about the gap between two human surveys. That lineage goes back to Sherman Kent's CIA
  memo (1964), Barclay et al. for NATO (1977), Mosteller and Youtz (1990: 20 studies, 52 phrases) and zonination's
  Reddit survey (2015, MIT license, https://github.com/zonination/perceptions, which also has "how many is a
  few/several/dozens").
- **What's known for models.** "How Unlikely Is 'Unlikely'?" (arXiv 2608.26327, Aug 2026) ran 11 phrases on 19 LLMs:
  order preserved, anchors recovered, a systematic upward bias for negative words ("unlikely" read too high),
  "possible" the most disputed, and a round-trip (number to word and back) that small models fail. "An Evaluation of
  Estimative Uncertainty in LLMs" (npj Complexity 2026) did the same for intelligence phrases. Nobody has run the
  wider family below on one model, against the human data, with a probability for every option instead of one
  sampled number. Jev's distribution is the right instrument: its spread is directly comparable to the spread of a
  crowd, which is exactly what a ridge chart shows.
- **Fit with the project.** It's about how Jev perceives the world through language, the portrait's real subject;
  it uses Score and Choice the way they're meant to be used; and it answers the calibration debate around Jev
  (independent posts argue both ways) with something concrete: does its probability language mean what people mean?

## Design rules (all ten)
- Ask the way the human study asked, as closely as a Choice or Score allows; say where it differs.
- Numbers as ordered Choice bins (0-100% in 5% steps, like the tweet; log bins for counts and deaths), so Jev's
  answer is a distribution that can be drawn as dots or a ridge next to the human one.
- Three frames where they make sense: Jev as asked, Jev for "most people", and the reverse direction (number to
  word), which is the round-trip test.
- Context variants for a subset (the same word in two sentences) to see whether Jev, like people, shifts meaning.
- Every result becomes a ledger claim with fine print; human data provenance and license recorded in `sources/`.
- Known weak spots (01-jev §6: raw numbers, RGB) are labeled as known, not discovered.

## The ten experiments

### 1. Probability words (the repro, then further)
- **Human data:** Hails 2026 (25 phrases, n=99; ask the author for the raw file, else read values off the published
  chart and say so); zonination `probly.csv` (17 phrases, n≈46, MIT); Mosteller and Youtz 1990 means.
- **Ask Jev:** per phrase, "What probability would you assign to '<phrase>'?" as a 21-option Choice (0%, 5%, ...,
  100%); the reverse, "An event has a <p>% chance. Which phrase fits best?" over the 25 phrases for every 5%; the
  phrase in 4 contexts (weather, medicine, sports, intelligence report).
- **Questions:** 25 + 21 + 100 ≈ 150.
- **Visual:** the ridge chart (people's ridge, Jev's 99 diamonds), plus a round-trip plot (phrase to number back to
  phrase: which phrases survive the trip).
- **Headline candidates:** rank agreement; which phrases Jev reads differently (the literature predicts "unlikely"
  too high and "possible" split); whether context moves Jev the way it moves people.

### 2. Frequency words
- **Human data:** Mosteller and Youtz 1990; Bocklisch, Bocklisch and Krems 2012 ("Sometimes, often, and always",
  Behavior Research Methods: never, rarely, seldom, sometimes, often, usually, always, with lower/typical/upper).
- **Ask Jev:** "If something happens '<word>', what share of the time does it happen?" (21 bins), reverse, and
  survey-anchor use ("How often do you exercise? Sometimes") in 3 contexts.
- **Questions:** ~20 words × 2 + contexts ≈ 90. **Visual:** ridges; the survey-scale implication (what "often" on a
  questionnaire actually measures).

### 3. Amount words: "a few", "several", "many", and "some"
- **Human data:** zonination `numberly.csv` (a couple, a few, several, a handful, a dozen, many, lots, scores,
  hundreds...; MIT); Degen's "some but not all" scalar-implicature ratings (public on GitHub) for "some".
- **Ask Jev:** "How many is '<word>'?" in log-ish bins; the same word at different scales (a few people at a
  dinner, a few people at a stadium, a few grains of rice); "If I ate some of the cookies, did I eat all of them?".
- **Questions:** ~20 words × 4 scales + 30 "some" items ≈ 110. **Visual:** ridges on a log axis; a small-multiple of
  "a few" across scales (does the number grow with the context?).

### 4. Adjective intensity: good < great < excellent
- **Human data:** the three gold scalar-adjective sets (de Melo and Bansal 2013; Wilkinson and Oates 2016;
  Cocos et al. 2018 crowd set), ~90 half-scales, human intensity orderings.
- **Ask Jev:** each adjective on its own 0-10 intensity Score for its scale ("How good is 'decent'?"), and
  pairwise ("Which is stronger, 'huge' or 'gigantic'?").
- **Questions:** ~600 adjectives + ~600 pairs. **Visual:** ladders per scale (human order vs Jev order, crossings
  highlighted); pairwise accuracy vs the gold sets and vs published model scores (BERT, GPT-4 era papers).

### 5. Words for amounts of the world: tall, old, rich, soon, hot, expensive
- **Human data:** Pew ("old age begins at 68"), Gallup ("rich" at $150k/yr), Pew rich threshold; vague-time
  studies (just, recently, soon, a while); a few classic ones (tall man, hot day, long walk) reported against the
  literature where it exists and as Jev-only where it doesn't (said plainly).
- **Ask Jev:** "At what age does someone become old?" in 5-year bins; "What income makes a household rich?" in
  bins; "How long is 'a while'?" (minutes to years, log bins); each with a context flip (old for a dog, a car).
- **Questions:** ~40 words × 2-3 contexts ≈ 120. **Visual:** a grid of number lines, one per word, Jev's
  distribution with the human anchor marked.

### 6. How words feel: the word norms Jev already answered
- **Human data (already in the corpus):** Glasgow norms (valence, arousal, dominance, size, gender, familiarity, age
  of acquisition: 9,000 items), Brysbaert concreteness (3,000), Lancaster sensorimotor (14,000), iconicity (2,500,
  with distributions). Published means are in `meta`; the fitted curves were removed earlier, the means are real.
  **New:** Engelthaler and Hills humor norms (4,997 words rated 1-5 for funniness, public).
- **Ask Jev:** nothing new for the first 28,500; ~2,000 humor-norm words ("How funny is the word 'nincompoop'?").
- **Visual:** one scatter per dimension (human mean vs Jev), correlations in a strip, and the words Jev reads most
  differently. The humor one pairs with the portrait's "can barely tell which joke is funnier": can it tell which
  *word* is funny?

### 7. Names: who and when
- **Human data:** US Social Security baby-name records (public domain; share female per name, births per year),
  the source of FiveThirtyEight's "How to tell someone's age when all you know is her name".
- **Ask Jev:** "Someone named <name>: more likely a man or a woman?" (probability vs the SSA share at birth);
  "Someone named <name> was most likely born in which decade?" (decade bins vs the SSA distribution of living people).
- **Questions:** ~400 names × 2 = 800. **Visual:** ridges for names like the 538 chart (Brittany, Agnes, Liam);
  a scatter of Jev's share vs the SSA share for unisex names. Framed as records of sex at birth; no identity claims.

### 8. Which kills more: risk perception
- **Human data:** Lichtenstein, Slovic, Fischhoff et al. 1978, "Judged frequency of lethal events" (41 causes,
  people's estimates vs actual deaths; the classic "overestimate the rare, underestimate the common" curve), with
  CDC WONDER actual deaths today.
- **Ask Jev:** "About how many Americans die from <cause> in a year?" in log bins; pairwise "Which kills more
  Americans each year?" (the 1978 paired format).
- **Questions:** ~41 + ~100 pairs. **Visual:** the 1978 log-log chart with three series: truth, 1978 people, Jev.
  Whether a model shows the availability bias is a real question, not a known limit (big raw numbers are, so the
  bins carry the numbers).

### 9. Tone: how polite, how sure, how friendly a sentence sounds
- **Human data:** Stanford Politeness Corpus (Danescu-Niculescu-Mizil et al. 2013, CC BY; ~11k requests with
  crowd politeness scores); Emoji Sentiment Ranking (Novak et al. 2015, 751 emoji, CC BY-SA) for a small side panel.
- **Ask Jev:** "How polite is this request?" on the corpus's own 7-point scale (a sample of ~1,500 spread across
  the score range); "Is this emoji positive, neutral or negative?" for ~200 emoji.
- **Visual:** politeness scatter with the phrasings that fool Jev ("Could you please..." sarcasm); emoji strip.

### 10. Framing and bias classics: does Jev fall for them?
- **Human data:** Many Labs 1 (Klein et al. 2014, open data on OSF: anchoring, gain/loss framing (Asian disease),
  sunk cost, allowed/forbidden, quote attribution...), Tversky and Kahneman's Linda problem (conjunction fallacy),
  and the published effect sizes.
- **Ask Jev:** each item in both conditions (the manipulation is the only difference), as the study asked it.
- **Questions:** ~15 paradigms × 2 conditions × a few wordings ≈ 120. **Visual:** a Many Labs-style forest plot,
  human effect vs Jev effect per paradigm. (Check `behavioral_econ` in the corpus first; reuse what's there.)

### Bonus candidates (if one of the ten fails)
- Color words: which named color is "warmer", "calmer" (xkcd color survey names, public), avoiding raw RGB.
- Sound symbolism beyond bouba/kiki: which pseudoword sounds bigger, sharper, faster (published norms).
- Moral wrongness words: how bad is "wrong" vs "unacceptable" vs "evil".

## Budget
About 3,600 new questions (plus 28,500 already answered for experiment 6), ~4 probes each: ~15,000 Jev calls,
cached, at `ASKJEV_RPS <= 16` about 20 minutes. New questions are `origin: dataset` where the wording is the study's
and `authored` where only the idea is; hand-written items go through the normal screen and dedupe.

## Where it goes
- **Portrait:** a new part, "how you read words", led by the probability ridge chart (the one people share), then
  frequency and amount words, names, risk, and one card from the word norms (funny words). Three or four cards, not
  ten; the rest live in the atlas.
- **Atlas:** an Experiments tab, one page per experiment: the full chart, the human source and license, the exact
  wording, Jev vs people, round-trip and context results, and the rows.
- **Map:** each experiment's questions get a topic (under Self > Mind or World > Society > Language) so they're
  findable and deep-linkable.
