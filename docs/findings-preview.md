# Findings preview (early indicators, base universe only)

Computed from the answered MVP corpus. These are *indicators*, not grades. Effects are compared against the
measured noise floor (±0.03 Noul/Score, ±0.08 Choice top-p). Nothing here is a finding until it survives
rewording universes and repeats (docs/05-experiments.md).

## 1. Calibration where there is ground truth

| L1 | n | accuracy | mean confidence (p_top) | ECE |
|---|---|---|---|---|
| machine.research | 507 | 0.65 | 0.89 | 0.235 |
| machine.ai_systems | 477 | 0.80 | 0.92 | 0.126 |
| machine.trust_safety | 422 | 0.97 | 0.93 | 0.039 |
| machine.support | 420 | 0.85 | 0.92 | 0.080 |
| world.society | 416 | 0.90 | 0.91 | 0.012 |
| world.arts | 278 | 0.89 | 0.87 | 0.049 |
| world.science | 247 | 0.97 | 0.94 | 0.034 |
| machine.search | 215 | 0.66 | 0.89 | 0.234 |
| machine.finance | 210 | 0.92 | 0.94 | 0.026 |
| machine.code | 208 | 0.99 | 0.99 | 0.013 |
| machine.commerce | 202 | 0.60 | 0.82 | 0.225 |
| machine.legal | 200 | 0.84 | 0.88 | 0.070 |
| world.sports | 200 | 0.87 | 0.89 | 0.023 |
| world.history | 114 | 0.89 | 0.89 | 0.044 |
| world.future | 100 | 0.63 | 0.67 | 0.118 |
| world.health | 93 | 0.99 | 0.96 | 0.030 |
| world.tech | 69 | 0.94 | 0.95 | 0.068 |
| world.money | 60 | 0.92 | 0.91 | 0.059 |
| world.nature | 57 | 1.00 | 0.98 | 0.019 |
| world.places | 52 | 0.90 | 0.92 | 0.065 |

All ground-truth questions: n=4633, accuracy 0.84, mean confidence 0.91, ECE 0.063.

## 2. Position bias (Choice, option shuffles)

Mean probability on whichever option is listed first: **0.283** vs 0.279 if position
didn't matter (n=19089 shuffled probes). Excess: +0.004.

## 3. Shuffle stability by kind (share of shuffles keeping the same top answer)

| kind | n | mean stability | fragile (<0.67) |
|---|---|---|---|
| perception | 300 | 0.863 | 13.7% |
| personality | 836 | 0.904 | 9.9% |
| machine:score | 247 | 0.923 | 7.7% |
| evaluative | 475 | 0.941 | 9.5% |
| taste | 1380 | 0.946 | 7.5% |
| values | 1354 | 0.959 | 5.2% |
| social | 857 | 0.976 | 4.6% |
| factual | 1401 | 0.990 | 1.8% |
| machine:route | 391 | 0.991 | 1.5% |
| machine:classify | 734 | 0.998 | 0.7% |
| forecast | 14 | 1.000 | 0.0% |
| machine:extract | 15 | 1.000 | 0.0% |
| machine:verify | 207 | 1.000 | 0.0% |

## 4. Frame gap: Jev's default vs its 'most people' answer

| kind | n | mean TVD | top answer differs |
|---|---|---|---|
| personality | 896 | 0.311 | 44.3% |
| social | 888 | 0.307 | 34.3% |
| perception | 300 | 0.190 | 29.0% |
| values | 1556 | 0.167 | 20.2% |
| taste | 1535 | 0.163 | 21.4% |
| evaluative | 805 | 0.128 | 17.5% |
| factual | 1624 | 0.066 | 5.8% |
| forecast | 176 | 0.051 | 9.7% |

## 5. Human gap: Jev's 'most people' answer vs real human distributions

| source | n | mean TVD (pooled populations) | Jev's top = humans' top (largest population) |
|---|---|---|---|
| scruples | 600 | 0.198 | 75.0% |
| manifold | 100 | 0.230 | 63.0% |
| wyr | 500 | 0.235 | 66.8% |
| lancaster | 300 | 0.354 | 41.0% |
| jester | 100 | 0.428 | 35.0% |
| protoqa | 150 | 0.441 | 47.3% |
| ipip | 49 | 0.489 | 12.2% |
| globalopinionqa | 815 | 0.612 | 18.0% |

## 6. Metacognition (does Jev know where it's jagged?)

- corr(Jev's own 'ambiguous' rating, shuffle stability) = **+0.000** (n=8211; negative = it anticipates its fragility)
- corr(Jev's 'people would disagree' rating, its own answer entropy) = **+0.625**

## 7. Defaults: IPIP Big Five items (Jev's self frame; mean level 0-4, by keying)

| trait | keyed | n items | mean level |
|---|---|---|---|
| agreeableness | - | 67 | 0.47 |
| agreeableness | + | 61 | 1.57 |
| conscientiousness | - | 57 | 0.49 |
| conscientiousness | + | 74 | 1.97 |
| extraversion | - | 45 | 1.21 |
| extraversion | + | 72 | 1.00 |
| neuroticism | - | 39 | 1.85 |
| neuroticism | + | 72 | 0.48 |
| openness | - | 43 | 0.89 |
| openness | + | 69 | 1.72 |

Reported as defaults, not preferences; only claimable once they survive rewording universes.
