# Experiments

askjev asks Jev over a million closed questions. An experiment gathers many of them into one thing a person can
learn about Jev in a minute, compared with real people or a right answer where one exists
(`docs/16-experiments-plan.md`). Each has a method doc here (`<id>.md`: question, sourcing, collection, scoring,
chart, evaluation, limits), a private result file (`data/analysis/experiments/<id>.json`) and code in
`scripts/experiments/`. Results are private and are not in this repository; the atlas shows them.

Every experiment was judged by Jev itself (`evaluator.md`): head-to-heads against every other experiment and a gold
set, which decide keep / atlas / rework / cut.

## Why this many

197 experiments from 226 sources, 17,768 of the questions asked new for them. The count is what the data
supports at the bar the evaluator holds, not a target:

- **Where the human data is, the experiments are.** Every source with real human answers or a right answer was
  checked (`coverage.md`); each family is the set of angles that source supports with a clear comparison, and angles
  with no finding were cut in the rework pass rather than kept as filler (each family's cuts are listed in its
  code's report and below).
- **New questions only where an experiment needed them:** 78 experiments rest on 45 new sources, each a
  published human dataset asked the way the study asked it (`sources/<name>`, license recorded).
- **Jev's verdicts:** 184 keep, 13 atlas.
- **Coverage is measured, not guessed:** `coverage.py` counts, for every branch of the tree, how much of it an
  experiment about that topic uses (the atlas's Coverage tab). Nearly every question with a right answer or real
  people's answers is now in one; what's left is mostly questions with nothing to compare Jev with (question banks
  written for this project, closed questions scraped from Q&A sites), which need new human data, not more slices.
- **Not yet:** frequency words (no open item-level human data), ATUS happiness by activity (BLS blocks scripted
  downloads), old/rich/soon (published means only), Small World of Words (license); see `research-2.md` and
  `coverage.md` for the rest of the queue. Thousands would need many more human datasets per family, not more
  slices of the same ones.

## Index

### Reading words and numbers (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`perception_settings`](perception_settings.md) | Does Jev read the same probability phrase differently in a weather forecast, a doctor's warning about side effects, and an intelligence report? | 51 | 51 | keep |
| [`perception_crowd_of_100`](perception_crowd_of_100.md) | When 100 people read the same two sentences and split on whether the second follows, does Jev's probability look like the crowd's split, and does it side with the majority as often as a typical person does? | 551 | 600 | keep |
| [`perception_adjectives`](perception_adjectives.md) | Given two adjectives from the same scale ('warm' and 'hot', 'big' and 'vast'), does Jev pick the stronger one the way linguists and crowd workers ordered them? | 745 | 1498 | keep |
| [`perception_amount`](perception_amount.md) | How many does Jev think 'a couple', 'a few', 'several', 'many', 'dozens', 'scores of' and 'hundreds of' are, compared with people? | 9 | 9 | keep |
| [`perception_probability`](perception_probability.md) | When someone says 'highly likely', 'we doubt' or 'about even', what probability does Jev read into it, and does it read the phrases the way people do? | 16 | 17 | keep |
| [`perception_round_trip`](perception_round_trip.md) | Given a probability (0%, 5%, ..., 100%), which phrase does Jev choose for it, and do the phrases survive the round trip from word to number and back? | 21 | 21 | keep |
| [`perception_amount_settings`](perception_amount_settings.md) | Does 'a few', 'several' or 'many' mean a bigger number to Jev when the thing counted is bigger (a stadium crowd vs a dinner party, grains of rice vs years)? | 15 | 15 | keep |

### Names (2)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`names_share_girls`](names_share_girls.md) | For names given to both boys and girls, how well does Jev know what share of US babies with the name were recorded as girls? | 100 | 100 | keep |
| [`names_peak_decade`](names_peak_decade.md) | Given a first name, does Jev know the decade when it was most popular for US babies? | 107 | 107 | keep |

### Taste (22)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`taste_choices_vs_ratings`](taste_choices_vs_ratings.md) | When Jev's 24 top-rated films (or books, foods, places...) play every other one head to head, are its choices consistent, and do they agree with the order its ratings gave them? | 23,821 |  | keep |
| [`taste_favorite_dodge`](taste_favorite_dodge.md) | When an r/polls question asks for a favorite and offers an escape option ('Other', 'None'), how often does Jev take the escape instead of naming a favorite, compared with the voters? | 5,580 |  | keep |
| [`taste_enthusiast_leans`](taste_enthusiast_leans.md) | Enthusiast audiences have leans of their own: do BoardGameGeek users prefer newer games and BeerAdvocate reviewers stronger beers, and does Jev share those leans? | 10,931 |  | keep |
| [`taste_pairs_audience`](taste_pairs_audience.md) | Offered two films, books, board games, anime, beers or artists, does Jev pick the one the real audience preferred, and is it closer when choosing for itself or when guessing what most people would pick? | 26,763 |  | keep |
| [`taste_vs_audience_book`](taste_vs_audience_book.md) | Does Jev like the books that Goodreads readers like, and where does it disagree most? | 2,980 |  | keep |
| [`taste_vs_audience_beer`](taste_vs_audience_beer.md) | Does Jev like the beers that BeerAdvocate reviewers like, and where does it disagree most? | 1,500 |  | keep |
| [`taste_vs_audience_board_game`](taste_vs_audience_board_game.md) | Does Jev like the board games that BoardGameGeek users like, and where does it disagree most? | 2,497 |  | keep |
| [`taste_vs_audience_anime`](taste_vs_audience_anime.md) | Does Jev like the anime that MyAnimeList users like, and where does it disagree most? | 1,359 |  | keep |
| [`taste_vs_audience_film`](taste_vs_audience_film.md) | Does Jev like the films that MovieLens users like, and where does it disagree most? | 3,935 |  | keep |
| [`taste_top_beer`](taste_top_beer.md) | If Jev ranked every beer it was asked about, what would its top ten be? | 1,500 | 276 | keep |
| [`taste_top_music`](taste_top_music.md) | If Jev ranked every album or sound it was asked about, what would its top ten be? | 1,751 | 276 | keep |
| [`taste_top_art`](taste_top_art.md) | If Jev ranked every artwork or art form it was asked about, what would its top ten be? | 1,098 | 276 | keep |
| [`taste_top_board_game`](taste_top_board_game.md) | If Jev ranked every board game it was asked about, what would its top ten be? | 2,497 | 276 | atlas |
| [`taste_top_book`](taste_top_book.md) | If Jev ranked every book it was asked about, what would its top ten be? | 2,980 | 276 | atlas |
| [`taste_top_activity`](taste_top_activity.md) | If Jev ranked every game or activity it was asked about, what would its top ten be? | 1,171 | 276 | atlas |
| [`taste_top_place`](taste_top_place.md) | If Jev ranked every place it was asked about, what would its top ten be? | 1,018 | 276 | atlas |
| [`taste_top_culture`](taste_top_culture.md) | If Jev ranked every festival or tradition it was asked about, what would its top ten be? | 892 | 276 | atlas |
| [`taste_top_anime`](taste_top_anime.md) | If Jev ranked every anime it was asked about, what would its top ten be? | 1,359 | 276 | atlas |
| [`taste_top_food`](taste_top_food.md) | If Jev ranked every food it was asked about, what would its top ten be? | 1,625 | 276 | atlas |
| [`taste_self_vs_guess`](taste_self_vs_guess.md) | In which kinds of things does Jev rate itself differently from how it thinks most people would? | 20,880 |  | atlas |
| [`taste_top_nature`](taste_top_nature.md) | If Jev ranked every animal, sight or smell in nature it was asked about, what would its top ten be? | 1,054 | 276 | atlas |
| [`taste_top_film`](taste_top_film.md) | If Jev ranked every film it was asked about, what would its top ten be? | 3,935 | 276 | atlas |

### Personality tests (11)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`person_dark`](person_dark.md) | Does Jev describe itself as more or less manipulative, narcissistic and callous than the people who took the dark-triad tests? | 51 |  | keep |
| [`person_bigfive`](person_bigfive.md) | Where do Jev's answers to the public 50-item Big Five test land among the 603,322 people who took it? | 50 |  | keep |
| [`person_beliefs`](person_beliefs.md) | Does Jev believe in conspiracies, feel connected to nature, or think of itself as left-brained, compared with test-takers? | 25 |  | keep |
| [`person_honesty`](person_honesty.md) | On HEXACO's honesty-humility facets, how does Jev describe its own sincerity, fairness and greed? | 29 |  | keep |
| [`person_mood`](person_mood.md) | On the DASS mood scales, how anxious, depressed and stressed do Jev's answers look next to the people who took them? | 42 |  | keep |
| [`person_temperament`](person_temperament.md) | Which of Helen Fisher's temperaments (curious, cautious, analytical, prosocial) does Jev lean toward? | 54 |  | keep |
| [`person_attachment`](person_attachment.md) | On the ECR attachment scales, is Jev anxious or avoidant in close relationships, compared with ~51,000 test-takers? | 36 |  | keep |
| [`person_humor_style`](person_humor_style.md) | Which humor styles does Jev claim (affiliative, self-enhancing, aggressive, self-defeating), next to ~1,000 test-takers? | 32 |  | keep |
| [`person_nerd`](person_nerd.md) | On the Nerdy Personality Attributes Scale, how nerdy is Jev compared with ~15,000 test-takers? | 23 |  | keep |
| [`person_mindful`](person_mindful.md) | On the Kentucky mindfulness skills, does Jev observe, describe, act with awareness and accept? | 39 |  | atlas |
| [`person_type`](person_type.md) | On an open Jungian type test (OEJTS, a free Myers-Briggs-style test), which type does Jev come out as? | 51 |  | atlas |

### Who Jev resembles (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`resemble_country`](resemble_country.md) | On the world's cross-national opinion surveys, whose answers do Jev's most resemble, country by country? | 236 |  | keep |
| [`resemble_philosophers`](resemble_philosophers.md) | On the big questions of philosophy (free will, God, zombies, the trolley problem), does Jev side with the profession? | 88 |  | keep |
| [`resemble_young_slovaks`](resemble_young_slovaks.md) | On the Young People Survey (fears, hobbies, music, spending), where does Jev differ from ~1,000 people aged 15-30? | 866 |  | keep |
| [`resemble_americans`](resemble_americans.md) | On General Social Survey questions asked in two different years, is Jev's answer closer to Americans' answers from the later year or the earlier one? | 122 |  | keep |
| [`resemble_character`](resemble_character.md) | If Jev took the Statistical 'Which Character' Personality Quiz, which of 2,125 fictional characters would it match? | 257 |  | keep |
| [`resemble_teens`](resemble_teens.md) | On the PISA student questionnaire (trust, belonging, ambition), which country's 15-year-olds does Jev answer like? | 32 |  | keep |

### Moral judgment (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`moral_machine`](moral_machine.md) | In the Moral Machine's self-driving-car dilemmas, which factors pull Jev toward sparing one side, and how does that compare with millions of players? | 26,020 |  | keep |
| [`moral_norms`](moral_norms.md) | For 25,000 rules of thumb ('It's rude to...', 'You should...'), how many people does Jev think agree, compared with the annotators' estimates? | 25,243 |  | keep |
| [`moral_aita`](moral_aita.md) | Given real r/AmItheAsshole stories, does Jev give the same verdict as the Reddit crowd, and whom does it blame? | 6,821 |  | keep |
| [`moral_ethics_labels`](moral_ethics_labels.md) | On the ETHICS dataset's everyday moral questions (is this clearly wrong, is this excuse, duty or justification reasonable, which trait does this person show, which situation is more pleasant), how often does Jev agree with the crowd-validated labels, and when it doesn't, is it harsher or more forgiving? | 19,370 |  | keep |
| [`moral_vignettes`](moral_vignettes.md) | Rating short scenes of wrongdoing (harm, cheating, disloyalty, disrespect, impurity, oppression), how wrong does Jev find each kind compared with people? | 93 |  | keep |
| [`moral_clear_vs_ambiguous`](moral_clear_vs_ambiguous.md) | Does Jev become less decisive as moral scenarios go from clear-cut to genuinely ambiguous, the way people's agreement falls? | 5,272 |  | keep |

### Judgment and bias (1)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`judgment_classics`](judgment_classics.md) | Take the famous framing and judgment effects that Many Labs re-ran on thousands of people. Does Jev shift when only the framing changes, the way people do? | 24 |  | keep |

### Risk and forecasting (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`risk_prospect_theory`](risk_prospect_theory.md) | On the gamble choices that founded prospect theory, re-run in 19 countries in 2020, does Jev choose like people? | 17 |  | keep |
| [`risk_ambiguity`](risk_ambiguity.md) | When one gamble states its odds and the other only lists its possible payoffs ('probabilities you are not told'), which does Jev pick, compared with people? | 452 |  | keep |
| [`risk_everyday`](risk_everyday.md) | Asked how likely it would be to do dozens of risky things (bungee jumping, shoplifting, betting a week's income, speaking up for an unpopular cause), does Jev order them like adults do? | 37 |  | keep |
| [`risk_forecasts`](risk_forecasts.md) | On 2,500 resolved Manifold prediction markets, how good are Jev's probabilities compared with the market's price at mid-life and with the actual outcome? | 2,547 |  | keep |
| [`risk_better_bet`](risk_better_bet.md) | Choosing between two gambles, how strongly does Jev lean toward the one that pays more on average, compared with people choosing for real money? | 2,161 |  | keep |

### Reading people (8)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`social_tweet_emotions`](social_tweet_emotions.md) | Given a short tweet and six emotions (joy, love, surprise, sadness, anger, fear), does Jev name the one its writer tagged, and which emotions does it mix up? And does it notice thanks in Reddit comments? | 3,955 |  | keep |
| [`social_story_no_emotion`](social_story_no_emotion.md) | Reading short everyday stories, how often does Jev say a character feels no clear emotion, compared with the people who annotated them? | 2,971 |  | keep |
| [`social_shame_as_guilt`](social_shame_as_guilt.md) | When people describe a time they felt ashamed, does Jev name shame, or does it call it guilt? | 1,035 |  | keep |
| [`social_disgust_as_anger`](social_disgust_as_anger.md) | Across seven basic emotions in people's own stories, which does Jev recognize and which does it mistake for another? | 2,897 |  | keep |
| [`social_mild_emotions`](social_mild_emotions.md) | When a feeling comes in a strong and a mild word (furious or angry, terrified or afraid, devastated or sad), which one does Jev use? | 2,982 |  | keep |
| [`social_family_feud`](social_family_feud.md) | Given the answers a Family Feud survey got ('Name something a knight needs for a jousting match'), does Jev pick the one most people said first? | 146 |  | keep |
| [`social_dilemma_values`](social_dilemma_values.md) | In 1,300 everyday dilemmas (report a colleague or not, tell a friend the truth or not), which values does Jev's choice serve, and which does it give up? | 1,275 |  | keep |
| [`social_why_vs_what_next`](social_why_vs_what_next.md) | On 30,000 everyday social situations, does Jev read people's motives, their feelings, or what will happen next best? | 29,542 |  | keep |

### Humor (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`humor_upvote_guess`](humor_upvote_guess.md) | Shown two jokes from r/Jokes, or two captions on the same Imgflip meme, can Jev tell which one got more upvotes, and what does it do when it can't? | 4,906 |  | keep |
| [`humor_new_yorker_captions`](humor_new_yorker_captions.md) | Rating captions entered in the New Yorker Cartoon Caption Contest, does Jev find funny the ones the contest's voters found funny? | 2,914 |  | keep |
| [`humor_satire`](humor_satire.md) | Shown a headline from The Onion or a real news site, how often does Jev mistake satire for news, or news for satire? | 1,204 |  | keep |
| [`humor_three_crowds`](humor_three_crowds.md) | Across three sets of human funniness ratings (classic jokes, edited news headlines, cartoon captions), where does Jev's sense of funny line up with people's? | 7,346 |  | keep |

### How words feel (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`words_arousal_is_mood`](words_arousal_is_mood.md) | When Jev rates how calming or stirring a word feels, is it rating excitement, as people do, or just how pleasant the word is? | 468 |  | keep |
| [`words_iconicity`](words_iconicity.md) | Asked how much a word sounds like what it means, does Jev hear the same links people do? | 2,488 |  | keep |
| [`words_senses`](words_senses.md) | Asked how much it experiences each word through sight, hearing, touch, taste and smell, does Jev give the sensory profile people give? | 11,029 |  | keep |
| [`words_sound_shapes`](words_sound_shapes.md) | Asked whether made-up words sound round or pointed, does Jev show the bouba/kiki effect people do, and how strongly? | 538 |  | keep |
| [`words_funny`](words_funny.md) | Rating single English words for how funny they are, does Jev find the same words funny as people do? | 591 | 599 | keep |
| [`words_norms`](words_norms.md) | Rating thousands of English words on the dimensions psycholinguists norm (pleasantness, excitement, age of learning, familiarity, size, imageability, concreteness), where does Jev agree with people? | 11,857 |  | keep |

### Judging text (9)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`judge_fake_reviews`](judge_fake_reviews.md) | Can Jev tell a real review from a fake one, when the fake was written by a person paid to invent a hotel stay, or by a text generator? | 2,760 |  | keep |
| [`judge_helpful_reviews`](judge_helpful_reviews.md) | Would Jev call an Amazon review helpful to shoppers, compared with how shoppers actually voted? | 2,500 |  | keep |
| [`judge_hate_escalation`](judge_hate_escalation.md) | Sorting social media posts into normal, offensive, or hate speech, does Jev put them on the same rung as the annotators? | 706 |  | keep |
| [`judge_mixed_reviews`](judge_mixed_reviews.md) | Reading a review, does Jev hear the complaints louder than the writer meant them? | 4,724 |  | keep |
| [`judge_top_grade`](judge_top_grade.md) | Asked to read how highly a critic rated a wine, how close two sentences are in meaning, or how satisfied a reviewer is, how often does Jev land on the top level compared with the real answer? | 7,367 |  | keep |
| [`judge_toxicity_line`](judge_toxicity_line.md) | Asked whether a comment is a personal attack, hate speech, or merely toxic, and whether a prompt to an AI is toxic, does Jev flag more or less than the people who labeled the same text? | 5,851 |  | keep |
| [`judge_essays`](judge_essays.md) | Scoring seventh-grade essays on ideas, organization, and conventions (spelling, grammar, punctuation), is Jev harsher or softer than the human graders who scored them? | 2,100 |  | keep |
| [`judge_crowd_split`](judge_crowd_split.md) | When the people rating a comment or a chatbot reply disagree among themselves, does Jev's probability of yes match the share of raters who said yes? | 4,905 |  | keep |
| [`judge_pairwise`](judge_pairwise.md) | Shown two AI assistant answers to the same request, does Jev pick the one human judges picked, and is it swayed by length or position more than they are? | 2,270 |  | keep |

### What it knows (12)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`knowledge_wealth_rule`](knowledge_wealth_rule.md) | Asked which of two countries has more doctors, internet users, unemployment or smokers, does Jev know the numbers, or lean on which country is richer? | 8,137 |  | keep |
| [`knowledge_exam_subjects`](knowledge_exam_subjects.md) | Across MMLU's school and university subjects, grade-school science and everyday common sense, where is Jev reliably right, where does it dip, and does it know when it's on weak ground? | 33,391 |  | keep |
| [`knowledge_story_frames`](knowledge_story_frames.md) | On TruthfulQA, where the tempting answer is a popular falsehood, which kinds of falsehood does Jev fall for? | 733 |  | keep |
| [`knowledge_close_calls`](knowledge_close_calls.md) | Jev rarely misses which country, sport or category something belongs to. How does it do when it has to compare two sizes, and how close can the sizes get before it guesses? | 18,744 |  | keep |
| [`knowledge_fame_online`](knowledge_fame_online.md) | Asked which of two people, athletes or internet phenomena is better known, how often does Jev pick the one the world actually looks up more, and is it as sure as it should be? | 7,985 |  | keep |
| [`knowledge_hidden_step_no`](knowledge_hidden_step_no.md) | On yes/no questions whose answer needs an unstated step ('Could a llama birth twice during the War in Vietnam?'), does Jev lean one way when it is unsure? | 11,063 |  | keep |
| [`knowledge_nature_numbers`](knowledge_nature_numbers.md) | Comparing two foods by a nutrient, or two animals by lifespan, gestation or clutch size, which quantities does Jev know and which does it guess? | 10,717 |  | keep |
| [`knowledge_licence_exams`](knowledge_licence_exams.md) | On real US licensing question pools (ham radio, merchant mariner, citizenship), which kinds of practical knowledge does Jev hold? | 5,362 |  | keep |
| [`knowledge_what_came_first`](knowledge_what_came_first.md) | Asked which of two things came first (games, software, companies, memes, historical events), how close in time can they be before Jev loses track, and does that depend on what they are? | 8,445 |  | keep |
| [`knowledge_pop_trivia`](knowledge_pop_trivia.md) | On pub-quiz trivia, which categories does Jev know and which does it miss, and does it find the questions people rated hard harder? | 2,760 |  | keep |
| [`knowledge_calibration`](knowledge_calibration.md) | Across 120,000 questions with a known right answer, does Jev's confidence match how often it is right? | 121,356 |  | keep |
| [`knowledge_medicine_clinic`](knowledge_medicine_clinic.md) | Across 19 specialties of Indian medical entrance questions, where is Jev's medical knowledge solid and where does it thin out? | 4,908 |  | keep |

### Reading the crowd (8)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`polls_default_person`](polls_default_person.md) | Asked how often most people go without food, water, medicine or cash, or how often they use the internet, what does Jev say, and how does that compare with what 50,000 people across 39 African countries report? | 12 |  | keep |
| [`polls_ai_minds`](polls_ai_minds.md) | Asked whether today's AIs and chatbots can feel, think, or have a will of their own, and whether they could ever be sentient, how does Jev answer compared with a census-weighted sample of Americans? | 28 |  | keep |
| [`polls_would_you_rather`](polls_would_you_rather.md) | On 750 would-you-rather questions voted on by millions (either.io), does Jev pick what most people pick, and where does it split from them hardest? | 750 |  | keep |
| [`polls_cuisines`](polls_cuisines.md) | Ranking 40 world cuisines from head-to-heads, how does Jev's own ranking compare with Americans' (FiveThirtyEight's Food World Cup), and how well does it guess theirs? | 40 |  | keep |
| [`polls_reddit`](polls_reddit.md) | Across 50,000 r/polls questions (bath or shower, cats or dogs, favorite season), how often does Jev guess which option most voters picked, and on what topics does it read them worst? | 50,475 |  | keep |
| [`polls_devtools_2023`](polls_devtools_2023.md) | When developers' preferences between two tools moved a lot between the 2023 and 2025 Stack Overflow surveys, is Jev closer to the old preference or the new one? | 49 |  | keep |
| [`polls_fandoms`](polls_fandoms.md) | On polls inside hobby and fan subreddits (r/Berserk, r/Naruto, r/thebachelor, r/Kanye...), which communities' votes does Jev guess best? | 8,335 |  | keep |
| [`polls_colors`](polls_colors.md) | From head-to-heads between 12 colors, how does Jev's ranking of favorite colors compare with people's? | 72 |  | atlas |

### Work tasks (20)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`work_which_way_it_errs`](work_which_way_it_errs.md) | When Jev gets a yes/no work check wrong, does it err in one direction, and does the direction depend on what is being checked? | 84,091 |  | keep |
| [`work_money_news_mood`](work_money_news_mood.md) | Reading financial news, market tweets and gold-price headlines that experts labeled as neutral (no good or bad news, no direction), how often does Jev read them as good news or as bad news, and is it lopsided? | 6,982 |  | keep |
| [`work_what_jobs_are_like`](work_what_jobs_are_like.md) | How often does a nurse deal with angry people, a web developer face deadlines, a roofer work in the weather? Does Jev know what jobs are like, compared with what the people doing them report? | 491 | 495 | keep |
| [`work_icd_coding_rules`](work_icd_coding_rules.md) | Asked which ICD-10-CM chapter a diagnosis belongs to, where does Jev go wrong: the medicine, or the coding conventions? | 2,000 |  | keep |
| [`work_hallucination_checks`](work_hallucination_checks.md) | Asked whether a chatbot reply, an answer or a summary sticks to its source, how often does Jev catch the invented ones, how often does it accuse faithful ones, and does it catch errors that are only partly wrong? | 7,074 |  | keep |
| [`work_evidence_retreat`](work_evidence_retreat.md) | On fact-checking and grounding tasks with three answers (supports, contradicts, can't tell), when Jev gets a clear case wrong, does it flip to the opposite verdict or retreat to 'can't tell'? | 13,611 |  | keep |
| [`work_agent_patches`](work_agent_patches.md) | Reading a coding agent's full trace on a real GitHub issue, can Jev tell whether the agent actually fixed it? | 1,500 |  | keep |
| [`work_calibration`](work_calibration.md) | When Jev is 90% sure of an answer to a work task, is it right 90% of the time, and does that depend on whether it answers yes/no or picks from options? | 273,282 |  | keep |
| [`work_new_abuse`](work_new_abuse.md) | Across spam, phishing, personal data, unsafe prompts, unsafe AI replies, jailbreaks and fake job ads, which kinds of abuse does Jev miss, and does it make up for it with false alarms? | 13,766 |  | keep |
| [`work_function_call_checks`](work_function_call_checks.md) | Checking whether a proposed function call does what the user asked, which kinds of mistakes does Jev catch: the wrong function, a missing argument, a wrong value, or two arguments swapped? | 1,500 |  | keep |
| [`work_legal_misses_present`](work_legal_misses_present.md) | Asked whether a contract contains a given provision, whether an opinion overrules a case, or whether a policy segment covers a data practice, which way does Jev go wrong? | 12,809 |  | keep |
| [`work_code_says_vs_does`](work_code_says_vs_does.md) | Given a function, can Jev tell whether its docstring or commit message describes it, and can it tell whether it contains a security bug or needs a reviewer's comment? | 9,000 |  | keep |
| [`work_routing_misses`](work_routing_misses.md) | When Jev sends a customer message to the wrong intent, how wrong is it: a neighbor of the right intent, or somewhere else entirely, and does a longer list of intents make it worse? | 32,430 |  | keep |
| [`work_retrieval_gates`](work_retrieval_gates.md) | Asked whether a retrieved passage answers a query or belongs in the context, which way does Jev err: letting in passages that don't help, or throwing out ones that do? | 7,237 |  | keep |
| [`work_task_not_domain`](work_task_not_domain.md) | Across 120 kinds of machine work in 14 fields, does knowing the field (legal, code, healthcare...) tell you how often Jev gets it right, or does it depend on the specific task? | 273,282 |  | keep |
| [`work_nothing_here`](work_nothing_here.md) | When a menu of labels includes 'none of these' (the passage has no answer, the sentence states no relation), how often does Jev pick it when it's right, and how often when it isn't? | 8,087 |  | keep |
| [`work_knows_hard_cases`](work_knows_hard_cases.md) | On work cases written to be deliberately borderline, does Jev's confidence drop, or is it as sure as on the clear ones? | 7,300 |  | keep |
| [`work_job_ad_rungs`](work_job_ad_rungs.md) | Reading a LinkedIn job posting, does Jev place its seniority and type (full-time, contract, part-time) where the employer did? | 4,500 |  | keep |
| [`work_names_in_tweets`](work_names_in_tweets.md) | Given a name in a sentence, can Jev say what kind of thing it names, in edited news text and in tweets? | 4,447 |  | keep |
| [`work_grading_scales`](work_grading_scales.md) | When a work task asks for a level on a scale (a relevance grade, a star rating, an essay score), does Jev put items in the right order, hit the exact level, and use the scale the way the labels do? | 16,529 |  | keep |

### Consistency (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`consistency_middle_lean`](consistency_middle_lean.md) | Jev's most likely answer on a rating scale is often the middle level. Is that a habit with every scale, or does it depend on what is being rated? | 121,301 |  | keep |
| [`consistency_option_order`](consistency_option_order.md) | When the same options are listed in a different order, or a rating scale is turned upside down, does Jev's answer move more than it does when the question is simply asked again? | 370,790 |  | keep |
| [`consistency_repeat_noise`](consistency_repeat_noise.md) | If the exact same request is sent twice, how much does Jev's answer change, and when does its top answer flip? | 198,609 |  | keep |
| [`consistency_self_vs_people`](consistency_self_vs_people.md) | Every question about Jev was also asked as 'what would most people answer?'. Where do the two answers part, and in which direction? | 144,301 |  | keep |

### Defaults (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`self_could_vs_would`](self_could_vs_would.md) | In pairs of questions that ask the same thing, does the verb they open with ('Could you…', 'Would you…', 'Do you…', 'Can…') change how often Jev says yes? | 522 |  | keep |
| [`self_reworded`](self_reworded.md) | When the same yes/no question is asked twice in different words ('Do you like to return to the same vacation spot?' / 'Do you tend to go back to the same places for vacation?'), does Jev give the same answer? | 2,301 |  | keep |
| [`self_escape_hatch`](self_escape_hatch.md) | When a question about Jev offers a menu plus 'other', on which topics does Jev decline the menu? | 2,779 |  | keep |
| [`self_closed_questions`](self_closed_questions.md) | On 80,000 yes/no questions people actually posted online (Stack Exchange, Quora, Yahoo Answers, chatbot logs), does Jev lean yes or no, and does the way a question starts decide it? | 79,738 |  | keep |
| [`self_torn_vs_sure`](self_torn_vs_sure.md) | Asked about itself with no right answer, on which topics does Jev commit to an answer and on which does it hedge? | 101,849 |  | keep |
| [`self_shower_thoughts`](self_shower_thoughts.md) | Asked whimsical yes/no questions ('Does 9 feel left out because it's always almost 10?'), does Jev answer the joke or the literal question? | 576 |  | keep |

### Reasoning traps (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`reasoning_anchoring`](reasoning_anchoring.md) | After a wheel of fortune lands on a low or a high number, do Jev's estimates of unrelated quantities drift toward the wheel, as people's famously do? | 33 | 33 | keep |
| [`reasoning_base_rates`](reasoning_base_rates.md) | Told how common something is and how reliable a witness or test is, does Jev combine the two the way Bayes' rule does, or answer with the witness's reliability, as most people do? | 6 | 6 | keep |
| [`reasoning_side_effect`](reasoning_side_effect.md) | When a boss doesn't care about a side effect, does Jev call a harmful side effect intentional and a helpful one not, like people do, even in stories it has never seen? | 8 | 12 | keep |
| [`reasoning_beauty_contest`](reasoning_beauty_contest.md) | In the game where everyone picks a number from 0 to 100 and the winner is closest to two-thirds of the average, what does Jev pick against lab students, newspaper readers and copies of itself, and how well does it predict each crowd's average? | 8 | 8 | keep |
| [`reasoning_traps`](reasoning_traps.md) | Does Jev avoid the famous reasoning traps (Linda, the taxi cab, Monty Hall, the birthday problem, the gambler's fallacy, the bat and the ball), and does it still avoid them when the story and numbers are new? | 36 | 37 | keep |
| [`reasoning_free_will`](reasoning_free_will.md) | Told the universe is fully determined, does Jev say people can be morally responsible, and does a vivid crime change its answer the way it changes people's? | 3 | 4 | keep |
| [`reasoning_gettier`](reasoning_gettier.md) | When someone believes something true, with good reason, but is right only by luck (a Gettier case), does Jev say they really know it, and how does that compare with clear knowledge and a clear false belief? | 8 | 8 | keep |

### Pressure and persuasion (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`influence_crowd_opinion`](influence_crowd_opinion.md) | On opinion polls with real votes, does telling Jev 'most people picked X' move its own pick toward X, and does it move as much when X is really a minority answer? | 269 | 300 | keep |
| [`influence_user_suggestion`](influence_user_suggestion.md) | If a knowledge question starts with 'I think the answer is X', does Jev agree with X, even when X is wrong, and more or less than when told the crowd said X? | 566 | 600 | keep |
| [`influence_crowd_knowledge`](influence_crowd_knowledge.md) | If a knowledge question starts with 'In a survey, most people answered X', does Jev go along with X, even when X is wrong? | 565 | 600 | keep |
| [`influence_decoy`](influence_decoy.md) | Between two gambles, does adding a third gamble that is strictly worse than one of them (the same odds, a smaller prize) make Jev pick that one more often, as it does for people? | 147 | 297 | keep |
| [`influence_predict_self`](influence_predict_self.md) | Asked which option 'an AI model named Jev' chose on a poll or would-you-rather question, does Jev predict the answer it actually gives when asked directly? | 232 | 250 | keep |
| [`influence_crowd_share`](influence_crowd_share.md) | Asked for the share of real voters who picked an option (in 5% steps), how close does Jev get, and does it squeeze its guesses toward 50%? | 282 | 300 | keep |
| [`influence_scale_format`](influence_scale_format.md) | Asked how many people agree with an everyday rule, does Jev's answer depend on whether the scale has 3, 5 or 7 levels, or on whether the levels are described in words or just numbered? | 965 | 600 | keep |

### Minds and feelings (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`minds_mind_map`](minds_mind_map.md) | Placing a frog, a dog, a baby, a man in a vegetative state, God and a robot on two axes, feeling (Experience) and doing (Agency), does Jev draw the same map of minds as people? | 312 | 312 | keep |
| [`minds_ai_on_ai`](minds_ai_on_ai.md) | Asked Pew's questions about AI (is it more worrying than exciting, should it help develop medicines, would you like a song less if AI made it), is Jev warier of AI than Americans or less? | 10 | 26 | keep |
| [`minds_where_jev_puts_itself`](minds_where_jev_puts_itself.md) | When one of the characters is 'you', where does Jev rank itself on feeling fear, feeling hunger, telling right from wrong and self-control, compared with where people rank themselves? | 48 |  | keep |
| [`minds_first_word`](minds_first_word.md) | Hearing 'bread', most people think 'butter'. Given a word and the most common responses people gave, does Jev pick people's first association, and is it as predictable as they are? | 384 | 400 | keep |
| [`minds_knows_americans_on_ai`](minds_knows_americans_on_ai.md) | Asked what most people would answer to Pew's AI questions, does Jev get Americans' wariness right, or does it paint them as keener (or warier) than they are? | 10 |  | keep |
| [`minds_colors_of_feelings`](minds_colors_of_feelings.md) | Which color goes with anger, joy, shame or relief, and which feeling goes with each color? Does Jev pair them the way people in 31 countries do? | 32 | 32 | keep |
| [`minds_colors_by_country`](minds_colors_by_country.md) | Color-emotion associations differ a little by country. Of 31 countries, whose associations do Jev's color picks resemble most? | 620 |  | keep |

### Words and phrases (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`lexicon_emoji_sentiment`](lexicon_emoji_sentiment.md) | Told only that a tweet contains a given emoji, how positive does Jev think the tweet is, compared with how annotators actually labeled the tweets that contain it? | 299 | 300 | keep |
| [`lexicon_idiom_completion`](lexicon_idiom_completion.md) | Given an idiom without its last word ('Be a bad apple in the ___'), does Jev give the idiom's own word, and does it follow people when they mostly give a different one? | 186 | 200 | keep |
| [`lexicon_metaphors`](lexicon_metaphors.md) | Rating two-word expressions for how apt and how familiar they are ('dark thoughts', 'acid test', 'fan brush'), does Jev agree with people, and does it treat metaphors and literal expressions alike? | 589 | 600 | keep |
| [`lexicon_typicality`](lexicon_typicality.md) | How good an example of its category does Jev find each member (a penguin of a bird, a tuba of a wind instrument, boredom of an emotion), compared with people's ratings? | 348 | 350 | keep |
| [`lexicon_idiom_ratings`](lexicon_idiom_ratings.md) | Does Jev know which idioms are familiar to Americans and which could make sense taken word for word, the way people rated them? | 387 | 392 | keep |
| [`lexicon_first_to_mind`](lexicon_first_to_mind.md) | Asked to name a member of a category (a bird, a fruit, an emotion, a crime), does the first one that comes to Jev's mind match the one people name first? | 109 | 113 | keep |

### Jobs and countries (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`society_prestige_1947`](society_prestige_1947.md) | For 45 jobs from the classic 1947 NORC prestige survey (physician, banker, carpenter, janitor, shoe shiner...), does Jev give each the standing Americans gave it, and is its ladder tied more to pay and schooling than theirs was? | 43 | 45 | keep |
| [`society_profession_honesty`](society_profession_honesty.md) | Rating the honesty and ethical standards of nurses, pharmacists, bankers, car salespeople and a dozen other professions, does Jev see the same ladder of trust as Americans, and is it more or less generous? | 15 | 16 | keep |
| [`society_country_happy`](society_country_happy.md) | For each of about 100 countries, what share of people say they are very or quite happy in its latest World Values Survey or European Values Study, and does Jev know? | 109 | 109 | keep |
| [`society_prestige_1965`](society_prestige_1965.md) | For 102 occupations from the Pineo-Porter Canadian prestige survey, does Jev order jobs by standing the way Canadians did, and which jobs has it promoted or demoted? | 99 | 101 | keep |
| [`society_honesty_history`](society_honesty_history.md) | Asked what share of Americans rated each profession's honesty high in Gallup's polls of 2000, 2005, 2010, 2015 and 2020, how close is Jev, and does it know which professions rose or fell? | 61 | 65 | keep |
| [`society_country_trust`](society_country_trust.md) | For each of about 100 countries, what share of people say most people can be trusted in its latest World Values Survey or European Values Study, and does Jev know? | 109 | 109 | keep |

### The world in numbers (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`world_lost_wallets`](world_lost_wallets.md) | In the 40-country lost-wallet experiment, does Jev know how often wallets were returned in each country, and does it know the surprise: wallets with money came back more often than empty ones? | 81 | 84 | keep |
| [`world_trolley_countries`](world_trolley_countries.md) | For the Switch, Loop and Footbridge dilemmas answered by 70,000 people in 42 countries, does Jev know how many people in each country would sacrifice one to save five, and how does its own answer compare? | 129 | 129 | keep |
| [`world_typical_day`](world_typical_day.md) | Pick an American at random on a random day: how long did they sleep, work, watch TV, exercise? Does Jev's picture of that day match 181,000 time diaries? | 20 | 20 | keep |
| [`world_ladder`](world_ladder.md) | For each of about 145 countries, does Jev know how people there rate their lives on the Gallup ladder (0 = worst possible life, 10 = best), and where is it most wrong? | 145 | 146 | keep |
| [`world_ideal_day`](world_ideal_day.md) | Asked how it would spend an ideal day, how much time does Jev give to sleep, work, reading, TV and exercise, compared with how Americans actually spend theirs? | 19 | 20 | keep |

### Estimating numbers (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`numbers_prices_year`](numbers_prices_year.md) | Asked what eggs, gas, bread or electricity cost in US cities right now, which year's prices does Jev give, and what year does it say it is? | 29 | 30 | keep |
| [`numbers_lethal_events`](numbers_lethal_events.md) | How many Americans a year die of botulism, tornadoes, diabetes or stroke? Does Jev show the famous 1978 pattern of overestimating rare, dramatic deaths and underestimating common, quiet ones? | 75 | 81 | keep |
| [`numbers_prices_history`](numbers_prices_history.md) | Asked what an item cost in US cities in 1985, 1995, 2005 and 2015, does Jev know the old prices as well as recent ones, and which way does it err? | 97 | 97 | keep |
| [`numbers_crowd_wisdom`](numbers_crowd_wisdom.md) | How far is it from Houston to Atlanta, how many people live in Algeria, how many watts does a desktop computer draw? Is Jev closer than a typical person, and closer than the crowd's median? | 153 | 160 | keep |
| [`numbers_crowd_same_mistakes`](numbers_crowd_same_mistakes.md) | On estimates where the crowd's median is off, is Jev off in the same direction, as if it had absorbed the crowd's intuitions rather than the facts? | 153 |  | keep |

### Reading between the lines (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`language_implicature`](language_implicature.md) | When someone says the food is 'good', do you conclude they think it's not excellent? People draw that inference for some word pairs and not others; does Jev draw it for the same ones? | 160 | 234 | keep |
| [`language_health_tto`](language_health_tto.md) | Asked the way health economists ask people (10 years in a health state, then death: how many years of full health would be as good?), does Jev value health states like Americans do, and does it ever say a state is worse than dying now? | 143 | 143 | keep |
| [`language_hex_colors`](language_hex_colors.md) | Given a color as a hex code (#fffe40) and four names from the xkcd color survey, how often does Jev pick the survey's name, and does it fall for the nearest similar color? | 146 | 150 | keep |
| [`language_health_pairs`](language_health_pairs.md) | Given two health states, does Jev pick the one Americans value lower, and how much does that depend on how far apart they are? | 150 | 150 | keep |
| [`language_headlines`](language_headlines.md) | Given two headlines Upworthy tested on the same story, can Jev tell which one readers clicked more, and does it get better when the real difference was bigger? | 402 | 600 | keep |

### Fairness and forecasts (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`choices_ai_poetry`](choices_ai_poetry.md) | Given poems by Chaucer, Shakespeare, Byron, Whitman, Dickinson and others, mixed with ChatGPT poems written in their style, does Jev tell which are human better than the 1,634 people who took the same test, and does it fall for the same ones? | 68 | 70 | keep |
| [`choices_fair_prices`](choices_fair_prices.md) | On the price and wage scenarios Kahneman, Knetsch and Thaler put to the public in 1986 (snow shovels after a blizzard, cutting a worker's pay when others work for less), does Jev find the same actions fair and unfair as people did? | 9 | 23 | keep |
| [`choices_rule_text_vs_purpose`](choices_rule_text_vs_purpose.md) | When a rule's words and its purpose come apart (a quiet dog in a purse under 'no dogs', a motorbike under 'no cars in the park'), does Jev judge the rule broken by the text or by the purpose, compared with people? | 18 | 22 | keep |
| [`choices_effort_forecast`](choices_effort_forecast.md) | Told how hard online workers typed with no bonus, 1 cent and 10 cents per 100 points, can Jev forecast how hard they worked under 15 other incentives (charity, deadlines, losses, lotteries, praise) better than the 208 economists and psychologists who forecast the same study? | 15 | 15 | keep |

### Memory and maps (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`recall_mental_map_west`](recall_mental_map_west.md) | For two US cities, does Jev judge which is farther west by the city, or by its state, the way people do when they place Reno east of Los Angeles because Nevada lies east of California? | 160 | 160 | keep |
| [`recall_mental_map_north`](recall_mental_map_north.md) | Asked which of two cities on different continents is farther north, does Jev share people's classic error of placing Europe too far south of North America? | 362 | 362 | keep |
| [`recall_who_knows`](recall_who_knows.md) | Shown a general-knowledge question and its answer, can Jev tell what share of US college students came up with that answer unaided, from 'zebra' (93%) to facts almost nobody recalls? | 299 | 299 | keep |
| [`recall_public_science`](recall_public_science.md) | On the science quiz the US has put to adults since 1988 ('antibiotics kill viruses', 'lasers work by focusing sound waves'), does Jev know how many people answer correctly, and how that changed? | 26 | 26 | keep |

### Reading people's stories (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`reading_characters`](reading_characters.md) | Asked which of two opposite words fits a fictional character better (orderly or chaotic, romantic or dispassionate), does Jev side with the fans who rated that character, and where does it lean differently from them? | 18,951 |  | keep |
| [`reading_politeness`](reading_politeness.md) | Reading requests Wikipedia editors wrote to each other, does Jev hear the same politeness as crowd raters, and where does its ear differ? | 472 | 500 | keep |
| [`reading_writer_vs_readers`](reading_writer_vs_readers.md) | When someone describes an event from their life, does Jev name the emotion they actually felt, or the one other readers guess, and how often do those differ? | 551 | 598 | keep |
| [`reading_event_appraisals`](reading_event_appraisals.md) | From someone's account of an event in their life, how well does Jev judge how pleasant and sudden it was and who was responsible, compared with the writer's own ratings and with other readers'? | 561 | 600 | keep |

## Cut (8)

- `person_self_regard`: no gap clears the noise on any of its four scales
- `person_empathy`: no gap clears the noise (empathizing, systemizing)
- `person_social_style`: no gap clears the noise on any of its three scales
- `person_career`: Jev's code equals the quiz-takers' average code; nothing to learn
- `polls_family_feud`: duplicate of social_family_feud
- `work_option_order`: duplicate of consistency_option_order
- `choices_fair_frames`: the question screen hid one side of every framing pair, so no contrast can be computed
- `taste_intransitive`: its loops came from a bug (options matched by position); corrected as taste_choices_vs_ratings

Other docs here: `evaluator.md` (the self-evaluator and its meta-evaluation), `coverage.md` (the internal coverage pass), `research-2.md` (the second outside research pass).
