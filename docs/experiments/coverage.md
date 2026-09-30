# Coverage: what the corpus can already answer

The internal pass for `docs/16-experiments-plan.md` (pass 2). Counts are shown questions (not hidden, not harmful).
Per-source table: `data/analysis/experiments/_coverage_sources.csv` (private).

## The shape
- **264 sources.** 52 carry real human answer distributions, 172 carry an answer key, 52 carry neither (mostly
  questions written for this project, plus Stack Exchange, Quora and Yahoo questions).
- **Machine:** 130 task sources, 302,180 questions, nearly all with answer keys.
- **Human answers, by volume:** Reddit polls (50,590), Moral Machine (26,020), Social Chemistry (25,243), character
  ratings (18,951), taste ratings (12,271), hobby-subreddit polls (8,335), Scruples/AITA (10,893), StoryCommonsense
  (5,985), five taste head-to-head sets (~24,800), Humicroedit (4,383), 538 food (4,339), dev-tool pairs (4,056),
  toxicity sets (civil comments, Wikipedia attacks, hate speech: ~6,400), caption contest (2,915), IPIP (2,888),
  Manifold (2,547), helpfulness ratings (Amazon, HelpSteer2, Open Assistant, MT-Bench: ~8,500), iconicity (2,488),
  choices13k and Wulff gambles (2,869), Open Psychometrics (1,268), Young People Survey (866), would-you-rather (750),
  GlobalOpinionQA (507, 133 countries), GSS (330, 22 years), ProtoQA (146), music and mental health (144), PISA (140),
  AIMS (97), Jester (97), PhilPapers (88), color favorites (72), Many Labs (69), EPQ (63), Afrobarometer (26).
- **Answer keys outside Machine:** Wikidata comparisons (32,039), Social IQa (29,542), MMLU (9,026), Pantheon fame
  (11,467), BoolQ (8,716), World Bank pairs (8,531), ARC (7,356), USDA nutrients (7,000), ETHICS (16,699), CommonsenseQA
  (5,808), AnAge lifespans (5,000), medical exams (7,285), mariner and ham-radio licensing (5,249), sensory modality
  (3,971), SciQ (3,875), empathetic dialogues (2,982), HotpotQA comparisons (2,980), ISEAR emotions (2,897), trivia
  (2,769), moral stories (2,671), captions and jokes by votes (4,956), TruthfulQA (748), NBA (399), US civics (114).
- **Neither, but useful as Jev-only portraits:** ~190,000 questions written for this project (personality,
  lifestyle, love, mind, values, taste), word norms whose human means are in `meta` (Glasgow 8,876, Lancaster 9,899,
  concreteness 2,981), O*NET activities (4,984), daily dilemmas (1,294).

## What each can support without new questions
| Family | Sources | Experiments it supports |
|---|---|---|
| Personality tests vs test-takers | IPIP, Open Psychometrics, EPQ, OEJTS, MFQ, wellbeing | Big Five, type, ~20 scale families, moral foundations, wellbeing |
| Who Jev resembles | GlobalOpinionQA, GSS, PISA, Afrobarometer, character ratings, PhilPapers | country, year, character, philosophers, teenagers |
| Moral judgment vs people | Moral Machine, Social Chemistry, Scruples/AITA, moral vignettes, Many Labs | trolley weights, everyday norms, AITA verdicts, foundations vignettes, biases |
| Taste vs audiences | taste ratings, head-to-heads, 538 food, dev tools, would-you-rather, Reddit and hobby polls | ranked lists per domain, taste vs audience, favorites census, communities |
| Humor | captions, jokes, Humicroedit, Jester, New Yorker contest | can Jev tell what's funny, by format |
| Judging text like people | toxicity sets, helpfulness sets, MT-Bench | offense, helpfulness, judging AI answers |
| Risk and chance | choices13k, Wulff, BBRS risk, Manifold, calibration | gambles, risk attitude, forecasting vs markets |
| Knowledge with keys | Wikidata, Pantheon, World Bank, USDA, AnAge, exams, TruthfulQA, NBA | what Jev knows about fame, countries, food, animals, exams, misconceptions |
| Social and commonsense | Social IQa, CommonsenseQA, StoryCommonsense, ProtoQA, ISEAR, empathetic dialogues | reading people, Family Feud answers, emotions |
| Words | Glasgow, Lancaster, concreteness, iconicity, pseudowords, bouba/kiki | how words feel, look, sound |
| Work | 130 Machine tasks | ~20 task families: where Jev is sure and right, sure and wrong |
| Consistency | shuffled, reversed and "most people" versions of everything | stability, scale use, self vs others |

## What's one small bank away
- **Taste finals:** the top 24 per domain, every pair (~2,500 questions).
- **Perception experiments** (`13-perception-experiments.md`): probability, frequency and amount words, adjectives,
  quantities of the world, lethal events, framing: ~1,000 questions with published human data.
- **External A list** (`15-analysis-review.md`): mind perception, feelings about AI, the ladder by country, beauty
  contest, colors of feelings, word associations, a typical day, prices, self-prediction, crowd prediction, decoys,
  pushback, social influence, scale design: ~5,000 questions.

## What's weak and gets redone
- **Taste from thin head-to-heads** (about 7 pairs per film): replaced by full rating ranks, finals and audience
  comparisons.
- **"Unusual topic" cards** (60) and "stable/fragile topic" cards (12): cut; stability becomes one experiment on how
  and where answers move.
- **Jev-only comparisons presented as findings** ("beyond reputation", theme stances): kept only where framed as Jev
  vs its own guess, and compared with real audiences where they exist.
- **Nine Moral Machine rows, 127 task rows, 30 knowledge rows, 14 agreement rows:** merged into one experiment each
  per family, with the rows as its chart.

## Measured coverage (2026-09-30)
`scripts/experiments/coverage.py` now measures this instead of estimating it, on every `export.py` run, and the atlas's
Coverage tab shows it per branch and topic. A question counts as covered when an experiment about its topic uses it;
corpus-wide experiments (calibration, option order, repeat noise, self vs people, torn vs sure, closed-question lean)
are counted apart, since they touch nearly everything. `work_which_way_it_errs` and `work_task_not_domain` sweep every
work task but report each task, so they count as covering them.

After the five experiments on data already here (`reading_characters`, `knowledge_exam_subjects`,
`work_money_news_mood`, `social_tweet_emotions`, `moral_ethics_labels`), 68% of shown questions sit in a topic
experiment and 96% of those with a right answer or real people's answers do. Nearly all that remains has nothing to
compare Jev with: the banks written for this project (mostly Self), closed questions scraped from Stack Exchange,
Quora, Yahoo Answers and WildChat, the vital-article judgments (`knowledge_heard_of` was tried against Wikipedia page views and cut: views measure what
people look up, not what they've heard of),
the "greatest of all time" pairs (fame does not predict Jev's picks, 52%, so no experiment) and the O*NET
activities. Covering them takes new human data: `research-3.md`.
