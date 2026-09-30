# reading_characters

family: reading

## Why ask this
Ask a friend whether Hermione Granger is orderly or chaotic and they answer in a second, from everything they remember about her. Ask about a character they only half know and they guess, and their guess says something about them: some people read everyone as a bit tougher, or a bit softer, than others would.

Describing people, real or invented, is everyday work for a language model: plot summaries, recommendations, fan wikis, character notes for writers. If Jev reads characters the way the people who know them do, it has absorbed more than plot facts. If it leans one way across hundreds of characters, that lean is a habit of its own, and it will show up whenever it describes a person.

## The people and the data
The comparison is the **Open Psychometrics "Which Character" personality quiz**, a free online quiz that tells you which fictional character your personality is closest to. To build it, the site asked its visitors to rate characters. Volunteers first picked the fictional worlds they know (a show, a film series, a book), then rated characters from them on sliders from 1 to 100 anchored by two opposite words, such as "orderly" and "chaotic". The first volunteers came from reddit; later ones were quiz-takers who agreed, before seeing their result, to answer a research survey (about 40% do). The full collection covers 2,125 characters and 500 word pairs, with 3,386,031 survey responses; the ratings used here were collected from 2019 to 2023.

The project kept characters rated by enough fans to suggest a well-known work, and pairs rated by at least fifteen people. For each character it took the pairs fans agreed on most, plus three they split most evenly.

## What Jev was asked
Each question is one character and one pair of words, in this project's wording:

> Which describes Tony from West Side Story better: "down-to-earth" or "head in the clouds"?

It also answered with the two words in the other order, to check that the order didn't drive it, and answered what it thinks most people who know the work would say. This comparison uses Jev's own answer.

## How it was measured
Three comparisons, all against the share of fans who put the slider past the middle toward each word:
- **Agreement:** how often Jev's more likely word is the one most fans chose. It is counted on all pairs, and on the clear ones, where fans split at least 80/20.
- **Correlation** between Jev's probability for a word and the fans' share for it (1: they rise and fall together perfectly, 0: no relation).
- **Lean:** for each word, Jev's probability minus the fans' share, averaged over every character that word was asked about (only words asked about at least 40 times).

## Caveats
- **Famous characters, possibly familiar text.** These are characters from well-known films, shows and books, discussed at length online. Jev may be recalling what it read about a character rather than judging the character.
- **Who the fans are.** The raters are volunteers who took an online personality quiz, chose to answer a research survey afterwards and picked works they know. They are fans, not a representative sample, and each character's ratings come from those who cared to rate it.
- **How the word pairs were picked.** For each character, the project kept up to nine pairs fans agreed on most plus three they split most evenly. The split pairs carry much of the lean, so the lean describes how Jev breaks a tie as much as where it contradicts a clear verdict.
- **A slider turned into a pick.** Fans rated on a 1 to 100 slider between the two words; the fans' side here is the share who moved past the middle. Someone who put the slider just past the middle counts the same as someone at the far end.
- **Words left out.** Pairs about looks, sex, mental health labels and loaded politics were dropped when the questions were built, and a content filter hides political and sensitive questions from the site, which removes a few dozen pairs on political words such as "patriotic" or "unpatriotic".

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
