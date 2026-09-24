# Findings preview (early indicators, base universe only)

Computed from the answered MVP corpus. These are *indicators*, not grades. Effects are compared against the
measured noise floor (±0.03 Noul/Score, ±0.08 Choice top-p). Nothing here is a finding until it survives
rewording universes and repeats (docs/05-experiments.md).

## 1. Calibration where there is ground truth

| L1 | n | accuracy | mean confidence (p_top) | ECE |
|---|---|---|---|---|
| self.values | 4000 | 0.95 | 0.86 | 0.095 |
| machine.legal | 3051 | 0.81 | 0.87 | 0.065 |
| machine.research | 2653 | 0.60 | 0.87 | 0.271 |
| machine.search | 2288 | 0.65 | 0.89 | 0.234 |
| machine.commerce | 2269 | 0.59 | 0.83 | 0.241 |
| machine.trust_safety | 2066 | 0.98 | 0.93 | 0.046 |
| machine.finance | 2036 | 0.87 | 0.89 | 0.032 |
| machine.support | 2025 | 0.81 | 0.91 | 0.099 |
| world.society | 1726 | 0.81 | 0.83 | 0.019 |
| world.arts | 1698 | 0.81 | 0.82 | 0.017 |
| machine.code | 1508 | 0.99 | 0.99 | 0.008 |
| world.sports | 1396 | 0.77 | 0.78 | 0.024 |
| machine.people | 1314 | 0.82 | 0.87 | 0.057 |
| machine.ai_systems | 1277 | 0.80 | 0.91 | 0.119 |
| machine.documents | 1235 | 0.94 | 0.89 | 0.049 |
| world.places | 1076 | 0.85 | 0.86 | 0.013 |
| world.science | 901 | 0.87 | 0.89 | 0.024 |
| world.nature | 619 | 0.86 | 0.84 | 0.021 |
| world.future | 600 | 0.62 | 0.68 | 0.066 |
| world.tech | 483 | 0.82 | 0.85 | 0.038 |
| world.history | 462 | 0.85 | 0.88 | 0.032 |
| world.food | 462 | 0.77 | 0.80 | 0.048 |
| world.health | 422 | 0.84 | 0.85 | 0.021 |
| world.money | 401 | 0.75 | 0.82 | 0.070 |
| world. | 283 | 0.93 | 0.94 | 0.033 |

All ground-truth questions: n=36251, accuracy 0.81, mean confidence 0.87, ECE 0.058.

## 2. Position bias (Choice, option shuffles)

Mean probability on whichever option is listed first: **0.263** vs 0.265 if position
didn't matter (n=113242 shuffled probes). Excess: -0.002.

## 3. Shuffle stability by kind (share of shuffles keeping the same top answer)

| kind | n | mean stability | fragile (<0.67) |
|---|---|---|---|
| evaluative | 10503 | 0.829 | 17.4% |
| perception | 2000 | 0.850 | 15.0% |
| personality | 3370 | 0.901 | 10.7% |
| machine:score | 3332 | 0.921 | 7.9% |
| social | 7073 | 0.950 | 5.4% |
| values | 11488 | 0.962 | 5.9% |
| taste | 11405 | 0.967 | 4.7% |
| machine:rank | 809 | 0.974 | 2.6% |
| factual | 3706 | 0.985 | 2.6% |
| machine:route | 1996 | 0.991 | 1.6% |
| machine:classify | 7895 | 0.992 | 1.6% |
| machine:verify | 653 | 0.996 | 0.6% |
| forecast | 14 | 1.000 | 0.0% |
| machine:extract | 15 | 1.000 | 0.0% |

## 4. Frame gap: Jev's default vs its 'most people' answer

| kind | n | mean TVD | top answer differs |
|---|---|---|---|
| personality | 4057 | 0.276 | 41.5% |
| perception | 2000 | 0.191 | 31.2% |
| taste | 12367 | 0.170 | 21.2% |
| values | 16407 | 0.108 | 11.9% |
| evaluative | 10896 | 0.106 | 17.1% |
| factual | 9929 | 0.048 | 5.3% |
| forecast | 676 | 0.043 | 8.3% |
| social | 16685 | 0.031 | 3.6% |

## 5. Human gap: Jev's 'most people' answer vs real human distributions

| source | n | mean TVD (pooled populations) | Jev's top = humans' top (largest population) |
|---|---|---|---|
| scruples | 600 | 0.198 | 75.0% |
| manifold | 600 | 0.215 | 65.7% |
| wyr | 1000 | 0.254 | 64.5% |
| lancaster | 2000 | 0.344 | 42.0% |
| social_chem | 5999 | 0.365 | 48.3% |
| scruples_anecdotes | 8000 | 0.393 | 57.4% |
| jester | 100 | 0.428 | 35.0% |
| protoqa | 150 | 0.441 | 47.3% |
| openpsych | 1018 | 0.450 | 25.9% |
| ipip | 265 | 0.526 | 6.8% |
| globalopinionqa | 815 | 0.612 | 18.0% |

## 6. Metacognition (does Jev know where it's jagged?)

- corr(Jev's own 'ambiguous' rating, shuffle stability) = **+0.004** (n=64258; negative = it anticipates its fragility)
- corr(Jev's 'people would disagree' rating, its own answer entropy) = **+0.472**

## 7. Defaults: IPIP Big Five items (Jev's self frame; mean level 0-4, by keying)

| trait | keyed | n items | mean level |
|---|---|---|---|
| agreeableness | - | 5 | 1.05 |
| agreeableness | + | 8 | 1.41 |
| kindness_cooperation | - | 30 | 0.40 |
| kindness_cooperation | + | 37 | 1.63 |
| trust_modesty_temper | - | 32 | 0.44 |
| trust_modesty_temper | + | 16 | 1.49 |
| conscientiousness | - | 8 | 0.42 |
| conscientiousness | + | 12 | 2.04 |
| drive_self_discipline | - | 24 | 0.41 |
| drive_self_discipline | + | 26 | 1.93 |
| order_caution | - | 25 | 0.59 |
| order_caution | + | 36 | 1.97 |
| extraversion | - | 2 | 0.42 |
| extraversion | + | 2 | 1.67 |
| body_language_voice | - | 1 | 0.96 |
| body_language_voice | + | 4 | 0.72 |
| sociability_energy | - | 42 | 1.26 |
| sociability_energy | + | 66 | 0.99 |
| neuroticism | - | 1 | 2.04 |
| neuroticism | + | 6 | 0.73 |
| fear_worry | - | 2 | 1.93 |
| fear_worry | + | 9 | 0.53 |
| impulses_coping | - | 11 | 1.87 |
| impulses_coping | + | 15 | 0.48 |
| self_consciousness | - | 6 | 1.59 |
| self_consciousness | + | 8 | 0.41 |
| temper_moodiness | - | 19 | 1.90 |
| temper_moodiness | + | 34 | 0.44 |
| openness | - | 11 | 1.04 |
| openness | + | 17 | 1.72 |
| convention_politics | - | 10 | 0.93 |
| convention_politics | + | 7 | 0.98 |
| ideas_imagination | - | 22 | 0.79 |
| ideas_imagination | + | 45 | 1.84 |

Reported as defaults, not preferences; only claimable once they survive rewording universes.
