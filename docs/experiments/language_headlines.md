# language_headlines

family: language · new questions: 600

## 1. Question
Given two headlines Upworthy tested on the same story, can Jev tell which one readers clicked more, and does it get better when the real difference was bigger?

Headline tests are the cleanest record of what makes people click: same story, same image, randomized readers. A model that writes headlines should know which ones work; and where the difference was noise, it should be at a coin flip.

## 2. Sourcing
New questions (sources/upworthy_headlines): 600 pairs from the Upworthy Research Archive (Matias et al. 2021, CC BY 4.0), two versions of the same test with the same image, each shown to 1,000+ readers, one pair per test, 200 in each third of the click gap. Tests touching politics were dropped.

Sources: `upworthy_headlines`

## 3. Collection
600 new questions, each asked with the headlines in both orders (averaged).

## 4. Scoring
Share of pairs where Jev's pick (averaged over both orders) is the headline with the higher click-through rate, by band of click gap and for gaps that clear a two-proportion z-test (|z| > 1.96), each with a 90% bootstrap interval; how often Jev picks the longer headline; how often the first-listed one.

## 5. Visualization
Bars: agreement with the winner by click-gap band and for significant gaps, with a 50% line.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 1.383, top verdict `portrait`.

## Compared with
Upworthy's readers in 2013-2015 (randomized tests, clicks per version)

## Limits
Clicks measure curiosity, not quality; readers were Upworthy's audience of the time. Many small gaps are noise, which is why the bands and the significance cut are reported.

Results: `data/analysis/experiments/language_headlines.json` (private). Code: `scripts/experiments/`.
