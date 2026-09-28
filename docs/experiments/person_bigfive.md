# person_bigfive

family: personality

## Why ask this
The Big Five (openness, conscientiousness, extraversion, agreeableness and neuroticism) is the personality model psychologists actually use. The 50-statement public version is probably the most taken personality test on the internet, and its answers are open, so any set of answers can be placed against hundreds of thousands of real people.

That makes it the cleanest way to ask the question behind the whole portrait: if Jev took the same test as everyone else, where would it land? And does it see itself the way it sees everyone else?

## The people and the data
The test is the 50-item Big-Five Factor Markers from the International Personality Item Pool, a set of public domain personality statements. The Open Psychometrics website published every response it collected from 2016 to 2018. The study keeps the 603,322 people who answered all 50 statements, one record per internet address, and score them exactly as the test says: ten statements per trait, some counted in reverse.

## What Jev was asked
All 50 statements, one question each, word for word from the test:

> How well does this statement describe you: "I am easily disturbed."
> *This does not describe me at all · This describes me a little · This describes me moderately well · This
> describes me well · This describes me very well*

Each statement was also asked as "what would most people say", and with the five answers in reverse order, to check the order didn't drive Jev's answers.

## How it was measured
For each trait, Jev's expected answers are added up exactly as the test scores a person, then the analysis asks what share of the 603,322 people scored lower. That share is Jev's percentile: 50 is the middle of the crowd. Because a trait rests on only ten statements, they are resampled to get a 90% interval, and the reversed-order answers and the "most people" answers are scored the same way.

## Caveats
- **Who the people are.** The comparison group is everyone who took this free test on the Open Psychometrics website from 2016 to 2018, one record per internet address. They chose to take a personality test online, so they are not a random sample of anyone.
- **Slightly different answer scales.** People answered from "disagree" to "agree". Both have five steps and are scored the same way, but the words at each step differ, which can shift where answers land.
- **A model describing itself.** Statements like "I get stressed out easily" assume a life with stress in it. Jev's answers show how it presents itself, shaped by how it was trained to talk, not a measured inner state.
- **Middle answers.** Jev tends to pick the middle level on questions about itself (see "Jev picks the middle when asked what it likes"). The people who took the test did not, which pulls Jev's percentiles toward the middle of the crowd on some traits. Read the square against the ring as well as against the crowd.
- **One hidden item.** A content filter hides a few questions from the site; one of the 50 statements ("I worry about things") is hidden from the list below but was scored.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
