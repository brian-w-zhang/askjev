# polls_devtools_2023

family: polls

## Why ask this
A model's opinions are frozen at the moment its training data ends, while the world keeps moving. Developer tools move fast: a framework that everyone wanted to keep using one year can fall out of favor two years later.

Stack Overflow's yearly developer survey records those shifts. Comparing Jev with three survey years shows which moment its taste reflects, and whether its recommendations about tools might be out of date.

## The people and the data
The **Stack Overflow Developer Survey** asks developers which technologies they've worked with and which they want to keep working with. Head-to-heads were built from three years (2023, 2024, 2025): among respondents who had used both tools in a pair and wanted to keep using exactly one, which one did they pick? The focus is the 49 pairs where that preference moved by 20 points or more between 2023 and 2025, with at least 50 such respondents in both years.

The surveys themselves are big (89,184 responses in 2023, 65,437 in 2024, 49,191 in 2025), but each pair rests only on the people who had used both tools, from about 50 to a few hundred.

## What Jev was asked
One question per pair, the way a developer might be asked:

> Which web framework or web technology would you rather work with over the next year: Next.js or Spring Boot?
> *Next.js · Spring Boot*

## How it was measured
For each moved pair, is Jev's probability closer to the 2023 share or the 2025 share? The analysis also checks, year by year, how often Jev's pick matches a clear majority (60% or more) among developers.

## Caveats
- **"Closer" isn't "agrees".** So part of the result is Jev leaning further in the old direction than developers ever did, not matching 2023 exactly.
- **Small, changing samples.** Each pair's share comes only from respondents who had used both tools, sometimes about 50 people. Samples this small bounce around from year to year, and a pull toward 2023 could partly be the 2025 numbers being noisier.
- **Who answers the survey.** Stack Overflow's survey reaches developers who visit the site and choose to answer, from 49,191 to 89,184 a year; they are not all developers, and the mix changes each year.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
