# Research pass 3: human data for the thin branches

Third outside pass for `docs/16-experiments-plan.md` (after `docs/14-experiment-catalog.md` and `research-2.md`),
aimed by the atlas's Coverage tab (`scripts/experiments/coverage.py`). With the experiments on data already in the
corpus, nearly every question that has a right answer or real people's answers sits in an experiment about its topic.
What's left is questions with nothing to compare Jev with: the banks written for this project (mostly Self: love,
mind, personality, lifestyle) and closed questions scraped from Q&A sites. Covering those takes new human data, which
means new questions, an answer run, and a production rebuild, so each item below names the branch it fills.

Checked on 2026-09-30: items public, human data public at item level or as published per-item figures, license where
stated. "Closed conversion" means the study asked free text and the question has to become a pick, a yes/no or a
scale for Jev.

## Batch A (verified, strongest)

| # | Experiment | Human data | Items | Fills |
|---|---|---|---:|---|
| 1 | Emotional understanding and management tests (STEU, STEM; SECEU) | STEU/STEM items in the APA supplement (MacCann & Roberts 2008), item-level human data from Schlegel et al. 2025 on OSF; SECEU items and norms (N > 500) on its project site | 86 + 40 | self.personality.emotions_stress, self.mind.reading_people |
| 2 | Theory-of-mind battery (false belief, irony, faux pas, hinting, strange stories) | Strachan et al. 2024, item text and every human response on OSF (about 1,900 people), CC BY-NC | 62 | self.mind (closed conversion) |
| 3 | What people want in a partner (18 traits rated, 13 ranked) | Walter et al. 2020, 45 countries, raw data on OSF (N = 14,399); Buss 1989 per-culture means | 31 | self.love.dating_attraction |
| 4 | Ideal family size and the best ages for life's milestones | Gallup trend since 1936 (per-option shares); ESS Timing of Life country means; Pew 2025 | ~20 | self.love.family_parenting |
| 5 | Would you want to know when you'll die? (deliberate ignorance) | Gigerenzer & Garcia-Retamero 2017, per-item shares, German and Spanish samples | 10 | self.mind.time_mortality |
| 6 | What Americans fear, and paranormal beliefs | Chapman Survey of American Fears 2024, per-item share afraid | 90+ | self.mind.luck_fate, self.personality.emotions_stress |
| 7 | When will AI be able to do X? | AI Impacts 2023 survey (Grace et al. 2024), per-task forecasts from ~2,800 researchers, CC BY | 39 | world.future.ai, world.tech.ai |
| 8 | Economic games: dictator, ultimatum, trust, public goods | Mei et al. 2024 (PNAS) human distributions from 50+ countries; Engel 2011 and Johnson & Mislin 2011 meta-analyses | ~30 | self.values.fairness_justice |
| 9 | Many Labs 2 (28 effects) | OSF materials and item-level data, 15,305 people in 36 countries | ~60 | extends `judgment_classics` |
| 10 | Basic human values (Schwartz, 21 portraits) | European Social Survey microdata by country, CC BY-NC-SA | 21 | self.values |

## Batch B

| # | Experiment | Human data | Fills |
|---|---|---|---|
| 11 | Moral circle and speciesism | Crimston 2016 (30 entities; 36-country norms in Kirkland 2023); Caviola 2019 | self.values.animals_environment |
| 12 | GoEmotions crowd splits | per-rater labels, 3-5 raters per comment | self.mind.reading_people |
| 13 | Sarcasm the author intended | iSarcasmEval (author labels) | reading between the lines |
| 14 | Perils of Perception | Ipsos per-country guesses vs actual; non-political items only | world.society |
| 15 | Wellbeing against population norms | SWLS, WHO-5 published norms (scale level) for the 18 wellbeing items already answered | self.mind.happiness_wellbeing |
| 16 | Work interests by RIASEC type | Open Psychometrics RIASEC raw data (item level) for the 4,984 O*NET activities already answered | self.personality.interests |

## Not usable as is
EmoBench (no per-item human answers); the experience machine (small headline splits only; PhilPapers 2020 already
covers it); Pew's "what makes life meaningful" (open-ended); PANAS and PERMA (scale norms only).

## Known results to say as known
LLMs scoring above people on emotional-intelligence tests (Schlegel et al. 2025: about 81% vs 56%) and at or above
people on most theory-of-mind tests but below on faux pas (Strachan et al. 2024) are published results. Experiments 1
and 2 are "Jev next to the published results", never a discovery.
