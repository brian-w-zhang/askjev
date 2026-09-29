# knowledge_pop_trivia

family: knowledge

## Why ask this
Trivia is a quick map of what a model has absorbed well. A pub quiz database, split into categories, shows where the knowledge is thick and where it thins out. That matters to anyone who asks a model about a game's plot, a show's cast or a band's discography and takes the answer on trust.

Every question also carries an easy, medium or hard label from the person who wrote it, a rough outside check on whether what a quiz writer thinks is hard is also hard for the model.

## The people and the data
The Open Trivia Database is a free quiz database (CC BY-SA 4.0) written by volunteers, who give every question a category and a difficulty rating.

## What Jev was asked
Each question as the database has it, with its four options:

> The cake depicted in Valve's "Portal" franchise most closely resembles which real-world type of cake?
> *Devil's Food · German Chocolate · Black Forest · Molten Chocolate*

Each was also asked with the options in shuffled orders.

## How it was measured
The share right per category and per difficulty rating, with 90% intervals.

## Caveats
- **Written by volunteers.** The Open Trivia Database is written and rated by contributors. Difficulty is one person's judgment, and some answers are the contributor's opinion of what counts as right.
- **Pop culture ages fast.** Video game and TV trivia is often about details from a specific release or episode; those are exactly the facts that are thinly written up, and some may postdate what Jev learned.
- **Multiple choice.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
