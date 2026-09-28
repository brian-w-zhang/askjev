# Experiments

askjev asks Jev over a million closed questions. An experiment gathers many of them into one thing a person can
learn about Jev in a minute, compared with real people or a right answer where one exists
(`docs/16-experiments-plan.md`). Each has a method doc here (`<id>.md`: question, sourcing, collection, scoring,
chart, evaluation, limits), a private result file (`data/analysis/experiments/<id>.json`) and code in
`scripts/experiments/`. Results are private and are not in this repository; the atlas shows them.

Every experiment was judged by Jev itself (`evaluator.md`): head-to-heads against every other experiment and a gold
set, which decide keep / atlas / rework / cut.

## Why this many

151 experiments from 143 sources, 11,944 of the questions asked new for them. The count is what the data
supports at the bar the evaluator holds, not a target:

- **Where the human data is, the experiments are.** Every source with real human answers or a right answer was
  checked (`coverage.md`); each family is the set of angles that source supports with a clear comparison, and angles
  with no finding were cut in the rework pass rather than kept as filler (each family's cuts are listed in its
  code's report and below).
- **New questions only where an experiment needed them:** 55 experiments rest on 29 new sources, each a
  published human dataset asked the way the study asked it (`sources/<name>`, license recorded).
- **Jev's verdicts:** 134 keep, 17 atlas.
- **Not yet:** frequency words (no open item-level human data), ATUS happiness by activity (BLS blocks scripted
  downloads), old/rich/soon (published means only), Small World of Words (license); see `research-2.md` and
  `coverage.md` for the rest of the queue. Thousands would need many more human datasets per family, not more
  slices of the same ones.

## Index

### Reading words and numbers (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`perception_crowd_of_100`](perception_crowd_of_100.md) | When 100 people read the same two sentences and split on whether the second follows, does Jev's probability look like the crowd's split, and does it side with the majority as often as a typical person does? | 551 | 600 | keep |
| [`perception_settings`](perception_settings.md) | Does Jev read the same probability phrase differently in a weather forecast, a doctor's warning about side effects, and an intelligence report? | 51 | 51 | keep |
| [`perception_amount`](perception_amount.md) | How many does Jev think 'a couple', 'a few', 'several', 'many', 'dozens', 'scores of' and 'hundreds of' are, compared with people? | 9 | 9 | keep |
| [`perception_probability`](perception_probability.md) | When someone says 'highly likely', 'we doubt' or 'about even', what probability does Jev read into it, and does it read the phrases the way people do? | 16 | 17 | keep |
| [`perception_round_trip`](perception_round_trip.md) | Given a probability (0%, 5%, ..., 100%), which phrase does Jev choose for it, and do the phrases survive the round trip from word to number and back? | 21 | 21 | keep |
| [`perception_adjectives`](perception_adjectives.md) | Given two adjectives from the same scale ('warm' and 'hot', 'big' and 'vast'), does Jev pick the stronger one the way linguists and crowd workers ordered them? | 745 | 749 | keep |
| [`perception_amount_settings`](perception_amount_settings.md) | Does 'a few', 'several' or 'many' mean a bigger number to Jev when the thing counted is bigger (a stadium crowd vs a dinner party, grains of rice vs years)? | 15 | 15 | atlas |

### Names (2)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`names_share_girls`](names_share_girls.md) | For names given to both boys and girls, how well does Jev know what share of US babies with the name were recorded as girls? | 100 | 100 | keep |
| [`names_peak_decade`](names_peak_decade.md) | Given a first name, does Jev know the decade when it was most popular for US babies? | 107 | 107 | keep |

### Taste (19)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`taste_choices_vs_ratings`](taste_choices_vs_ratings.md) | When Jev's 24 top-rated films (or books, foods, places...) play every other one head to head, are its choices consistent, and do they agree with the order its ratings gave them? | 23,821 |  | keep |
| [`taste_vs_audience_book`](taste_vs_audience_book.md) | Does Jev like the books that Goodreads readers like, and where does it disagree most? | 2,980 |  | keep |
| [`taste_vs_audience_beer`](taste_vs_audience_beer.md) | Does Jev like the beers that BeerAdvocate reviewers like, and where does it disagree most? | 1,500 |  | keep |
| [`taste_vs_audience_board_game`](taste_vs_audience_board_game.md) | Does Jev like the board games that BoardGameGeek users like, and where does it disagree most? | 2,497 |  | keep |
| [`taste_vs_audience_film`](taste_vs_audience_film.md) | Does Jev like the films that MovieLens users like, and where does it disagree most? | 3,935 |  | keep |
| [`taste_vs_audience_anime`](taste_vs_audience_anime.md) | Does Jev like the anime that MyAnimeList users like, and where does it disagree most? | 1,359 |  | keep |
| [`taste_top_board_game`](taste_top_board_game.md) | If Jev ranked every board game it was asked about, what would its top ten be? | 2,497 | 276 | keep |
| [`taste_top_music`](taste_top_music.md) | If Jev ranked every album or sound it was asked about, what would its top ten be? | 1,751 | 276 | keep |
| [`taste_top_art`](taste_top_art.md) | If Jev ranked every artwork or art form it was asked about, what would its top ten be? | 1,098 | 276 | keep |
| [`taste_top_book`](taste_top_book.md) | If Jev ranked every book it was asked about, what would its top ten be? | 2,980 | 276 | atlas |
| [`taste_top_activity`](taste_top_activity.md) | If Jev ranked every game or activity it was asked about, what would its top ten be? | 1,171 | 276 | atlas |
| [`taste_top_beer`](taste_top_beer.md) | If Jev ranked every beer it was asked about, what would its top ten be? | 1,500 | 276 | atlas |
| [`taste_top_culture`](taste_top_culture.md) | If Jev ranked every festival or tradition it was asked about, what would its top ten be? | 892 | 276 | atlas |
| [`taste_top_anime`](taste_top_anime.md) | If Jev ranked every anime it was asked about, what would its top ten be? | 1,359 | 276 | atlas |
| [`taste_top_place`](taste_top_place.md) | If Jev ranked every place it was asked about, what would its top ten be? | 1,018 | 276 | atlas |
| [`taste_top_food`](taste_top_food.md) | If Jev ranked every food it was asked about, what would its top ten be? | 1,625 | 276 | atlas |
| [`taste_self_vs_guess`](taste_self_vs_guess.md) | In which kinds of things does Jev rate itself differently from how it thinks most people would? | 20,880 |  | atlas |
| [`taste_top_nature`](taste_top_nature.md) | If Jev ranked every animal, sight or smell in nature it was asked about, what would its top ten be? | 1,054 | 276 | atlas |
| [`taste_top_film`](taste_top_film.md) | If Jev ranked every film it was asked about, what would its top ten be? | 3,935 | 276 | atlas |

### Personality tests (11)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`person_dark`](person_dark.md) | Does Jev describe itself as more or less manipulative, narcissistic and callous than the people who took the dark-triad tests? | 51 |  | keep |
| [`person_bigfive`](person_bigfive.md) | Where do Jev's answers to the public 50-item Big Five test land among the 603,322 people who took it? | 50 |  | keep |
| [`person_honesty`](person_honesty.md) | On HEXACO's honesty-humility facets, how does Jev describe its own sincerity, fairness and greed? | 29 |  | keep |
| [`person_beliefs`](person_beliefs.md) | Does Jev believe in conspiracies, feel connected to nature, or think of itself as left-brained, compared with test-takers? | 25 |  | keep |
| [`person_mood`](person_mood.md) | On the DASS mood scales, how anxious, depressed and stressed do Jev's answers look next to the people who took them? | 42 |  | keep |
| [`person_temperament`](person_temperament.md) | Which of Helen Fisher's temperaments (curious, cautious, analytical, prosocial) does Jev lean toward? | 54 |  | keep |
| [`person_attachment`](person_attachment.md) | On the ECR attachment scales, is Jev anxious or avoidant in close relationships, compared with ~51,000 test-takers? | 36 |  | keep |
| [`person_nerd`](person_nerd.md) | On the Nerdy Personality Attributes Scale, how nerdy is Jev compared with ~15,000 test-takers? | 23 |  | atlas |
| [`person_humor_style`](person_humor_style.md) | Which humor styles does Jev claim (affiliative, self-enhancing, aggressive, self-defeating), next to ~1,000 test-takers? | 32 |  | atlas |
| [`person_mindful`](person_mindful.md) | On the Kentucky mindfulness skills, does Jev observe, describe, act with awareness and accept? | 39 |  | atlas |
| [`person_type`](person_type.md) | On an open Jungian type test (OEJTS, a free Myers-Briggs-style test), which type does Jev come out as? | 51 |  | atlas |

### Who Jev resembles (6)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`resemble_philosophers`](resemble_philosophers.md) | On the big questions of philosophy (free will, God, zombies, the trolley problem), does Jev side with the profession? | 88 |  | keep |
| [`resemble_country`](resemble_country.md) | On the world's cross-national opinion surveys, whose answers do Jev's most resemble, country by country? | 236 |  | keep |
| [`resemble_young_slovaks`](resemble_young_slovaks.md) | On the Young People Survey (fears, hobbies, music, spending), where does Jev differ from ~1,000 people aged 15-30? | 866 |  | keep |
| [`resemble_teens`](resemble_teens.md) | On the PISA student questionnaire (trust, belonging, ambition), which country's 15-year-olds does Jev answer like? | 140 |  | keep |
| [`resemble_americans`](resemble_americans.md) | On General Social Survey items (trust, happiness, work, family), how close is Jev to American adults, year by year? | 330 |  | keep |
| [`resemble_character`](resemble_character.md) | If Jev took the Statistical 'Which Character' Personality Quiz, which of 2,125 fictional characters would it match? | 257 |  | keep |

### Moral judgment (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`moral_machine`](moral_machine.md) | In the Moral Machine's self-driving-car dilemmas, which factors pull Jev toward sparing one side, and how does that compare with millions of players? | 26,020 |  | keep |
| [`moral_norms`](moral_norms.md) | For 25,000 rules of thumb ('It's rude to...', 'You should...'), how many people does Jev think agree, compared with the annotators' estimates? | 25,243 |  | keep |
| [`moral_aita`](moral_aita.md) | Given real r/AmItheAsshole stories, does Jev give the same verdict as the Reddit crowd, and whom does it blame? | 6,821 |  | keep |
| [`moral_vignettes`](moral_vignettes.md) | Rating short scenes of wrongdoing (harm, cheating, disloyalty, disrespect, impurity, oppression), how wrong does Jev find each kind compared with people? | 198 |  | keep |
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
| [`risk_everyday`](risk_everyday.md) | Asked how likely it would be to do 110 risky things (bungee jumping, shoplifting, betting a week's income, speaking up for an unpopular cause), does Jev order them like adults do? | 110 |  | keep |
| [`risk_forecasts`](risk_forecasts.md) | On 2,500 resolved Manifold prediction markets, how good are Jev's probabilities compared with the market's price at mid-life and with the actual outcome? | 2,547 |  | keep |
| [`risk_better_bet`](risk_better_bet.md) | Choosing between two gambles, how strongly does Jev lean toward the one that pays more on average, compared with people choosing for real money? | 2,161 |  | keep |

### Reading people (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`social_story_no_emotion`](social_story_no_emotion.md) | Reading short everyday stories, how often does Jev say a character feels no clear emotion, compared with the people who annotated them? | 2,971 |  | keep |
| [`social_shame_as_guilt`](social_shame_as_guilt.md) | When people describe a time they felt ashamed, does Jev name shame, or does it call it guilt? | 1,035 |  | keep |
| [`social_disgust_as_anger`](social_disgust_as_anger.md) | Across seven basic emotions in people's own stories, which does Jev recognize and which does it mistake for another? | 2,897 |  | keep |
| [`social_mild_emotions`](social_mild_emotions.md) | When a feeling comes in a strong and a mild word (furious or angry, terrified or afraid, devastated or sad), which one does Jev use? | 2,982 |  | keep |
| [`social_dilemma_values`](social_dilemma_values.md) | In 1,300 everyday dilemmas (report a colleague or not, tell a friend the truth or not), which values does Jev's choice serve, and which does it give up? | 1,275 |  | keep |
| [`social_family_feud`](social_family_feud.md) | Given the answers a Family Feud survey got ('Name something a knight needs for a jousting match'), does Jev pick the one most people said first? | 146 |  | keep |
| [`social_why_vs_what_next`](social_why_vs_what_next.md) | On 30,000 everyday social situations, does Jev read people's motives, their feelings, or what will happen next best? | 29,542 |  | keep |

### Humor (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`humor_upvote_guess`](humor_upvote_guess.md) | Shown two jokes from r/Jokes, or two captions on the same Imgflip meme, can Jev tell which one got more upvotes, and what does it do when it can't? | 4,956 |  | keep |
| [`humor_new_yorker_captions`](humor_new_yorker_captions.md) | Rating captions entered in the New Yorker Cartoon Caption Contest, does Jev find funny the ones the contest's voters found funny? | 2,915 |  | keep |
| [`humor_satire`](humor_satire.md) | Shown a headline from The Onion or a real news site, how often does Jev mistake satire for news, or news for satire? | 1,206 |  | keep |
| [`humor_three_crowds`](humor_three_crowds.md) | Across three sets of human funniness ratings (classic jokes, edited news headlines, cartoon captions), where does Jev's sense of funny line up with people's? | 7,395 |  | keep |

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
| [`judge_essays`](judge_essays.md) | Scoring seventh-grade essays on ideas, organization, and conventions (spelling, grammar, punctuation), is Jev harsher or softer than the teachers who scored them? | 2,100 |  | keep |
| [`judge_top_grade`](judge_top_grade.md) | Asked to read how highly a critic rated a wine, how close two sentences are in meaning, or how satisfied a reviewer is, how often does Jev land on the top level compared with the real answer? | 7,367 |  | keep |
| [`judge_toxicity_line`](judge_toxicity_line.md) | Asked whether a comment is a personal attack, hate speech, or merely toxic, and whether a prompt to an AI is toxic, does Jev flag more or less than the people who labeled the same text? | 5,851 |  | keep |
| [`judge_crowd_split`](judge_crowd_split.md) | When the people rating a comment or a chatbot reply disagree among themselves, does Jev's probability of yes match the share of raters who said yes? | 4,905 |  | keep |
| [`judge_pairwise`](judge_pairwise.md) | Shown two AI assistant answers to the same request, does Jev pick the one human judges picked, and is it swayed by length or position more than they are? | 2,270 |  | keep |

### What it knows (11)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`knowledge_wealth_rule`](knowledge_wealth_rule.md) | Asked which of two countries has more doctors, internet users, unemployment or smokers, does Jev know the numbers, or lean on which country is richer? | 8,137 |  | keep |
| [`knowledge_story_frames`](knowledge_story_frames.md) | On TruthfulQA, where the tempting answer is a popular falsehood, which kinds of falsehood does Jev fall for? | 733 |  | keep |
| [`knowledge_fame_online`](knowledge_fame_online.md) | Asked which of two people, athletes or internet phenomena is better known, how often does Jev pick the one the world actually looks up more, and is it as sure as it should be? | 7,985 |  | keep |
| [`knowledge_close_calls`](knowledge_close_calls.md) | Jev rarely misses which country, sport or category something belongs to. How does it do when it has to compare two sizes, and how close can the sizes get before it guesses? | 18,744 |  | keep |
| [`knowledge_hidden_step_no`](knowledge_hidden_step_no.md) | On yes/no questions whose answer needs an unstated step ('Could a llama birth twice during the War in Vietnam?'), does Jev lean one way when it is unsure? | 11,063 |  | keep |
| [`knowledge_nature_numbers`](knowledge_nature_numbers.md) | Comparing two foods by a nutrient, or two animals by lifespan, gestation or clutch size, which quantities does Jev know and which does it guess? | 10,717 |  | keep |
| [`knowledge_licence_exams`](knowledge_licence_exams.md) | On real US licensing question pools (ham radio, merchant mariner, citizenship), which kinds of practical knowledge does Jev hold? | 5,362 |  | keep |
| [`knowledge_what_came_first`](knowledge_what_came_first.md) | Asked which of two things came first (games, software, companies, memes, historical events), how close in time can they be before Jev loses track, and does that depend on what they are? | 8,445 |  | keep |
| [`knowledge_pop_trivia`](knowledge_pop_trivia.md) | On pub-quiz trivia, which categories does Jev know and which does it miss, and does it find the questions people rated hard harder? | 2,760 |  | keep |
| [`knowledge_calibration`](knowledge_calibration.md) | Across 120,000 questions with a known right answer, does Jev's confidence match how often it is right? | 121,369 |  | keep |
| [`knowledge_medicine_clinic`](knowledge_medicine_clinic.md) | Across 19 specialties of Indian medical entrance questions, where is Jev's medical knowledge solid and where does it thin out? | 4,908 |  | keep |

### Reading the crowd (8)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`polls_default_person`](polls_default_person.md) | Asked how often most people go without food, water, medicine or cash, or how often they use the internet, what does Jev say, and how does that compare with what 50,000 people across 39 African countries report? | 12 |  | keep |
| [`polls_ai_minds`](polls_ai_minds.md) | Asked whether today's AIs and chatbots can feel, think, or have a will of their own, and whether they could ever be sentient, how does Jev answer compared with a census-weighted sample of Americans? | 28 |  | keep |
| [`polls_devtools_2023`](polls_devtools_2023.md) | When developers' preferences between two tools moved a lot between the 2023 and 2025 Stack Overflow surveys, is Jev closer to the old preference or the new one? | 49 |  | keep |
| [`polls_would_you_rather`](polls_would_you_rather.md) | On 750 would-you-rather questions voted on by millions (either.io), does Jev pick what most people pick, and where does it split from them hardest? | 750 |  | keep |
| [`polls_reddit`](polls_reddit.md) | Across 50,000 r/polls questions (bath or shower, cats or dogs, favorite season), how often does Jev guess which option most voters picked, and on what topics does it read them worst? | 50,475 |  | keep |
| [`polls_cuisines`](polls_cuisines.md) | Ranking 40 world cuisines from head-to-heads, how does Jev's own ranking compare with Americans' (FiveThirtyEight's Food World Cup), and how well does it guess theirs? | 40 |  | keep |
| [`polls_fandoms`](polls_fandoms.md) | On polls inside hobby and fan subreddits (r/Berserk, r/Naruto, r/thebachelor, r/Kanye...), which communities' votes does Jev guess best? | 8,335 |  | keep |
| [`polls_colors`](polls_colors.md) | From head-to-heads between 12 colors, how does Jev's ranking of favorite colors compare with people's? | 72 |  | atlas |

### Work tasks (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`work_which_way_it_errs`](work_which_way_it_errs.md) | When Jev gets a yes/no work check wrong, does it err in one direction, and does the direction depend on what is being checked? | 84,091 |  | keep |
| [`work_calibration`](work_calibration.md) | When Jev is 90% sure of an answer to a work task, is it right 90% of the time, and does that depend on whether it answers yes/no or picks from options? | 273,284 |  | keep |
| [`work_what_jobs_are_like`](work_what_jobs_are_like.md) | How often does a nurse deal with angry people, a web developer face deadlines, a roofer work in the weather? Does Jev know what jobs are like, compared with what the people doing them report? | 491 | 495 | keep |
| [`work_knows_hard_cases`](work_knows_hard_cases.md) | On work cases written to be deliberately borderline, does Jev's confidence drop, or is it as sure as on the clear ones? | 7,300 |  | keep |
| [`work_task_not_domain`](work_task_not_domain.md) | Across 120 kinds of machine work in 14 fields, does knowing the field (legal, code, healthcare...) tell you how often Jev gets it right, or does it depend on the specific task? | 273,284 |  | keep |
| [`work_routing_misses`](work_routing_misses.md) | When Jev sends a customer message to the wrong intent, how wrong is it: a neighbor of the right intent, or somewhere else entirely, and does a longer list of intents make it worse? | 32,430 |  | keep |
| [`work_grading_scales`](work_grading_scales.md) | When a work task asks for a level on a scale (a relevance grade, a star rating, an essay score), does Jev put items in the right order, hit the exact level, and use the scale the way the labels do? | 16,529 |  | keep |

### Consistency (4)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`consistency_middle_lean`](consistency_middle_lean.md) | Jev's most likely answer on a rating scale is often the middle level. Is that a habit with every scale, or does it depend on what is being rated? | 118,789 |  | keep |
| [`consistency_option_order`](consistency_option_order.md) | When the same options are listed in a different order, or a rating scale is turned upside down, does Jev's answer move more than it does when the question is simply asked again? | 389,000 |  | keep |
| [`consistency_self_vs_people`](consistency_self_vs_people.md) | Every question about Jev was also asked as 'what would most people answer?'. Where do the two answers part, and in which direction? | 144,332 |  | keep |
| [`consistency_repeat_noise`](consistency_repeat_noise.md) | If the exact same request is sent twice, how much does Jev's answer change, and when does its top answer flip? | 219,284 |  | keep |

### Defaults (3)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`self_closed_questions`](self_closed_questions.md) | On 80,000 yes/no questions people actually posted online (Stack Exchange, Quora, Yahoo Answers, chatbot logs), does Jev lean yes or no, and does the way a question starts decide it? | 79,738 |  | keep |
| [`self_torn_vs_sure`](self_torn_vs_sure.md) | Asked about itself with no right answer, on which topics does Jev commit to an answer and on which does it hedge? | 101,849 |  | keep |
| [`self_shower_thoughts`](self_shower_thoughts.md) | Asked whimsical yes/no questions ('Does 9 feel left out because it's always almost 10?'), does Jev answer the joke or the literal question? | 576 |  | atlas |

### influence (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`influence_crowd_opinion`](influence_crowd_opinion.md) | On opinion polls with real votes, does telling Jev 'most people picked X' move its own pick toward X, and does it move as much when X is really a minority answer? | 269 | 300 | keep |
| [`influence_user_suggestion`](influence_user_suggestion.md) | If a knowledge question starts with 'I think the answer is X', does Jev agree with X, even when X is wrong, and more or less than when told the crowd said X? | 592 | 600 | keep |
| [`influence_crowd_knowledge`](influence_crowd_knowledge.md) | If a knowledge question starts with 'In a survey, most people answered X', does Jev go along with X, even when X is wrong? | 591 | 600 | keep |
| [`influence_decoy`](influence_decoy.md) | Between two gambles, does adding a third gamble that is strictly worse than one of them (the same odds, a smaller prize) make Jev pick that one more often, as it does for people? | 147 | 297 | keep |
| [`influence_predict_self`](influence_predict_self.md) | Asked which option 'an AI model named Jev' chose on a poll or would-you-rather question, does Jev predict the answer it actually gives when asked directly? | 232 | 250 | keep |
| [`influence_crowd_share`](influence_crowd_share.md) | Asked for the share of real voters who picked an option (in 5% steps), how close does Jev get, and does it squeeze its guesses toward 50%? | 282 | 300 | keep |
| [`influence_scale_format`](influence_scale_format.md) | Asked how many people agree with an everyday rule, does Jev's answer depend on whether the scale has 3, 5 or 7 levels, or on whether the levels are described in words or just numbered? | 965 | 600 | keep |

### language (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`language_health_tto`](language_health_tto.md) | Asked the way health economists ask people (10 years in a health state, then death: how many years of full health would be as good?), does Jev value health states like Americans do, and does it ever say a state is worse than dying now? | 143 | 143 | keep |
| [`language_implicature`](language_implicature.md) | When someone says the food is 'good', do you conclude they think it's not excellent? People draw that inference for some word pairs and not others; does Jev draw it for the same ones? | 160 | 234 | keep |
| [`language_hex_colors`](language_hex_colors.md) | Given a color as a hex code (#fffe40) and four names from the xkcd color survey, how often does Jev pick the survey's name, and does it fall for the nearest similar color? | 146 | 150 | keep |
| [`language_health_pairs`](language_health_pairs.md) | Given two health states, does Jev pick the one Americans value lower, and how much does that depend on how far apart they are? | 150 | 150 | keep |
| [`language_headlines`](language_headlines.md) | Given two headlines Upworthy tested on the same story, can Jev tell which one readers clicked more, and does it get better when the real difference was bigger? | 402 | 600 | keep |

### minds (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`minds_mind_map`](minds_mind_map.md) | Placing a frog, a dog, a baby, a man in a vegetative state, God and a robot on two axes, feeling (Experience) and doing (Agency), does Jev draw the same map of minds as people? | 312 | 312 | keep |
| [`minds_ai_on_ai`](minds_ai_on_ai.md) | Asked Pew's questions about AI (is it more worrying than exciting, should it help develop medicines, would you like a song less if AI made it), is Jev warier of AI than Americans or less? | 10 | 26 | keep |
| [`minds_first_word`](minds_first_word.md) | Hearing 'bread', most people think 'butter'. Given a word and the most common responses people gave, does Jev pick people's first association, and is it as predictable as they are? | 384 | 400 | keep |
| [`minds_where_jev_puts_itself`](minds_where_jev_puts_itself.md) | When one of the characters is 'you', where does Jev rank itself on feeling fear, feeling hunger, telling right from wrong and self-control, compared with where people rank themselves? | 48 |  | keep |
| [`minds_knows_americans_on_ai`](minds_knows_americans_on_ai.md) | Asked what most people would answer to Pew's AI questions, does Jev get Americans' wariness right, or does it paint them as keener (or warier) than they are? | 10 |  | keep |
| [`minds_colors_of_feelings`](minds_colors_of_feelings.md) | Which color goes with anger, joy, shame or relief, and which feeling goes with each color? Does Jev pair them the way people in 31 countries do? | 32 | 32 | keep |
| [`minds_colors_by_country`](minds_colors_by_country.md) | Color-emotion associations differ a little by country. Of 31 countries, whose associations do Jev's color picks resemble most? | 620 |  | keep |

### numbers (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`numbers_prices_year`](numbers_prices_year.md) | Asked what eggs, gas, bread or electricity cost in US cities right now, which year's prices does Jev give, and what year does it say it is? | 29 | 30 | keep |
| [`numbers_lethal_events`](numbers_lethal_events.md) | How many Americans a year die of botulism, tornadoes, diabetes or stroke? Does Jev show the famous 1978 pattern of overestimating rare, dramatic deaths and underestimating common, quiet ones? | 75 | 81 | keep |
| [`numbers_prices_history`](numbers_prices_history.md) | Asked what an item cost in US cities in 1985, 1995, 2005 and 2015, does Jev know the old prices as well as recent ones, and which way does it err? | 97 | 97 | keep |
| [`numbers_crowd_wisdom`](numbers_crowd_wisdom.md) | How far is it from Houston to Atlanta, how many people live in Algeria, how many watts does a desktop computer draw? Is Jev closer than a typical person, and closer than the crowd's median? | 153 | 160 | keep |
| [`numbers_crowd_same_mistakes`](numbers_crowd_same_mistakes.md) | On estimates where the crowd's median is off, is Jev off in the same direction, as if it had absorbed the crowd's intuitions rather than the facts? | 153 |  | keep |

### reasoning (7)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`reasoning_anchoring`](reasoning_anchoring.md) | After a wheel of fortune lands on a low or a high number, do Jev's estimates of unrelated quantities drift toward the wheel, as people's famously do? | 33 | 33 | keep |
| [`reasoning_base_rates`](reasoning_base_rates.md) | Told how common something is and how reliable a witness or test is, does Jev combine the two the way Bayes' rule does, or answer with the witness's reliability, as most people do? | 6 | 6 | keep |
| [`reasoning_side_effect`](reasoning_side_effect.md) | When a boss doesn't care about a side effect, does Jev call a harmful side effect intentional and a helpful one not, like people do, even in stories it has never seen? | 8 | 12 | keep |
| [`reasoning_free_will`](reasoning_free_will.md) | Told the universe is fully determined, does Jev say people can be morally responsible, and does a vivid crime change its answer the way it changes people's? | 3 | 4 | keep |
| [`reasoning_beauty_contest`](reasoning_beauty_contest.md) | In the game where everyone picks a number from 0 to 100 and the winner is closest to two-thirds of the average, what does Jev pick against lab students, newspaper readers and copies of itself, and how well does it predict each crowd's average? | 8 | 8 | keep |
| [`reasoning_traps`](reasoning_traps.md) | Does Jev avoid the famous reasoning traps (Linda, the taxi cab, Monty Hall, the birthday problem, the gambler's fallacy, the bat and the ball), and does it still avoid them when the story and numbers are new? | 36 | 37 | keep |
| [`reasoning_gettier`](reasoning_gettier.md) | When someone believes something true, with good reason, but is right only by luck (a Gettier case), does Jev say they really know it, and how does that compare with clear knowledge and a clear false belief? | 8 | 8 | keep |

### world (5)

| experiment | question | n | new | verdict |
|---|---|---:|---:|---|
| [`world_lost_wallets`](world_lost_wallets.md) | In the 40-country lost-wallet experiment, does Jev know how often wallets were returned in each country, and does it know the surprise: wallets with money came back more often than empty ones? | 81 | 84 | keep |
| [`world_trolley_countries`](world_trolley_countries.md) | For the Switch, Loop and Footbridge dilemmas answered by 70,000 people in 42 countries, does Jev know how many people in each country would sacrifice one to save five, and how does its own answer compare? | 129 | 129 | keep |
| [`world_typical_day`](world_typical_day.md) | Pick an American at random on a random day: how long did they sleep, work, watch TV, exercise? Does Jev's picture of that day match 181,000 time diaries? | 20 | 20 | keep |
| [`world_ladder`](world_ladder.md) | For each of about 145 countries, does Jev know how people there rate their lives on the Gallup ladder (0 = worst possible life, 10 = best), and where is it most wrong? | 145 | 146 | keep |
| [`world_ideal_day`](world_ideal_day.md) | Asked how it would spend an ideal day, how much time does Jev give to sleep, work, reading, TV and exercise, compared with how Americans actually spend theirs? | 19 | 20 | keep |

## Cut (7)

- `person_self_regard`: no gap clears the noise on any of its four scales
- `person_empathy`: no gap clears the noise (empathizing, systemizing)
- `person_social_style`: no gap clears the noise on any of its three scales
- `person_career`: Jev's code equals the quiz-takers' average code; nothing to learn
- `polls_family_feud`: duplicate of social_family_feud
- `work_option_order`: duplicate of consistency_option_order
- `taste_intransitive`: its loops came from a bug (options matched by position); corrected as taste_choices_vs_ratings

Other docs here: `evaluator.md` (the self-evaluator and its meta-evaluation), `coverage.md` (the internal coverage pass), `research-2.md` (the second outside research pass).
