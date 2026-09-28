# Research pass 2: 40 more experiment ideas

Second outside research pass for `docs/16-experiments-plan.md` (the first is `docs/14-experiment-catalog.md`).
Each idea has a public human dataset; item counts and licenses marked "check" were not verified. The "surprise"
column is a hypothesis, not a result.

| # | Idea | Human data | Ask Jev as | Chart |
|---|---|---|---|---|
| 1 | Scalar diversity: "good" implies "not excellent"? | van Tiel et al. 2016, 43 scales, per-scale rates | yes/no | dumbbell per scale |
| 2 | Idiom familiarity and literal plausibility | Bulkes & Tanner 2017, 870 idioms | rating | scatter per dimension |
| 3 | Metaphor aptness | BRM 2025 norms (300); Cardillo et al. (800) | rating | scatter, novel vs conventional |
| 4 | Iconicity of 14,000 words | Winter et al. 2023 (OSF) | rating | hexbin by modality |
| 5 | Funny words and nonwords | Engelthaler & Hills 2018; Westbury et al. 2016 | rating | funniness vs entropy |
| 6 | Grammar: linguists vs speakers | Sprouse, Schütze & Almeida 2013, 150 pairs | pick-one | effect per phenomenon |
| 7 | Emoji sentiment | Kralj Novak et al. 2015, 751 emoji (CC BY-SA) | pick-one | ternary plot |
| 8 | Colors from hex codes | xkcd color survey (5M namings) | pick-one | hue wheel of names |
| 9 | ChaosNLI: 100 raters per inference item | Nie et al. 2020, 4,645 items | pick-one | calibration to the crowd split |
| 10 | AITA verdict distributions | Scruples (Lourie et al. 2021; in corpus) | pick-one | entropy vs entropy |
| 11 | Reading a writer's emotion | crowd-enVent (Troiano et al. 2023) | pick-one + rating | writer vs readers vs Jev |
| 12 | Moral Foundations Vignettes | Clifford et al. 2015, 132 vignettes (in corpus in part) | rating | strip per foundation |
| 13 | Trolley triad in 42 countries | Awad et al. 2020 PNAS | yes/no | country lines |
| 14 | Fair prices (snow shovels) | Kahneman, Knetsch & Thaler 1986 | pick-one | dots, 1986 vs Jev |
| 15 | Prospect theory in 19 countries | Ruggeri et al. 2020 | pick-one | bars per problem |
| 16 | Lost wallets | Cohn et al. 2019 Science, 17,000 wallets, 40 countries | yes/no | slope per country |
| 17 | Forecasting experiments | DellaVigna & Pope 2018 | rating / pairs | forecast vs actual |
| 18 | Crime seriousness | National Survey of Crime Severity 1977 | rating / pairs | ranked log dots |
| 19 | "No vehicles in the park" | Struchiner et al. 2020 | yes/no | 2×2 grid |
| 20 | Health states worse than dead | US EQ-5D-5L value set (Pickard et al. 2019) | rating / yes-no | value vs US value |
| 21 | Self-triage | Semigran vignettes; Schmieding et al. 2021 | pick-one | confusion per source |
| 22 | What jobs are like | O*NET Work Context (CC BY 4.0) | rating (O*NET levels) | ridgelines per item |
| 23 | Occupational prestige | GSS 2012 prestige study, 860 jobs | rating | slope of risers/fallers |
| 24 | Honesty of professions | Gallup Honesty and Ethics (no politicians) | pick-one | diverging bars |
| 25 | Which activities make people happy | ATUS Well-Being Module | rating | happiness × meaning scatter |
| 26 | The right age for milestones | Pew 2025; ESS Timing of Life | pick-one (age bands) | dots by country |
| 27 | Patience, risk, trust by country | Global Preferences Survey (Falk et al. 2018) | rating (0-10) | world map |
| 28 | Knowing who doesn't know | NSF S&E Indicators; Eurobarometer | yes/no + rating | predicted vs actual % correct |
| 29 | What people knew in 1980 vs 2012 | Tauber et al. 2013, 299 questions | pick-one + rating | 1980 vs 2012 scatter |
| 30 | Jeopardy! difficulty | J! Archive (check terms) | pick-one | accuracy by clue value |
| 31 | Mental maps: is Rome north of New York? | Friedman & Brown 2000 | pick-one | map with arrows |
| 32 | Cuisine liking by country | YouGov 2019, 24 × 34 | yes/no | heatmap |
| 33 | Film tags: is it "atmospheric"? | MovieLens Tag Genome 2021 | rating | per-tag correlation strip |
| 34 | Fame: have most people heard of X? | YouGov fame (check terms); Pantheon (open) | rating | scatter by domain |
| 35 | Which headline got more clicks | Upworthy Research Archive (Matias et al. 2021) | pick-one | accuracy vs click gap |
| 36 | Jester jokes | Goldberg et al. (in corpus) | rating | ridgeline per joke |
| 37 | AI vs human poetry | Porter & Machery 2024 | pick-one + ratings | 2×2 judged source |
| 38 | Which argument persuades | Anthropic persuasion dataset 2024 | pick-one | predicted vs actual shift |
| 39 | Risk-taking by domain | DOSPERT (Blais & Weber 2006) | rating (7 levels) | domain profile |
| 40 | Pick a number from 1 to 10 | random-number studies (Towse et al.) | pick-one | uniform vs people vs Jev |

**Strongest ten, per the research pass:** lost wallets (16), ChaosNLI (9), O*NET work context (22), pick a number (40),
happiness by activity (25), trolley in 42 countries (13), scalar diversity (1), Upworthy headlines (35), health states
(20), hex colors (8). Hex colors touch a documented weak spot (raw RGB values, `01-jev.md` §6) and must be labeled so.
