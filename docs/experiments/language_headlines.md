# language_headlines

family: language

## Why ask this
Headline tests are the cleanest record there is of what makes people click. A site writes two headlines for the same story, shows each to a random half of its readers, and keeps the winner. From 2013 to 2015, Upworthy, a viral news site known for curiosity-gap headlines, ran these tests constantly, and the full record has since been published.

Models now write and pick headlines all the time. A model that can spot the winner has absorbed something real about what grabs attention. And where two headlines did equally well, a well-calibrated model should be unsure.

## The people and the data
The **Upworthy Research Archive** (Matias, Munger, Le Quere and Ebersole, 2021) is the published record of Upworthy's headline tests.

## What Jev was asked
> Upworthy tested these two headlines for the same story on its readers, with the same image. Which headline got
> more clicks?
> *He Looks Buttoned Up On TV, But There Was A Time Where His Reality Was Completely Terrifying · He Was Afraid Of
> Himself For Many Years Until A Man Taught Him How To Fly*

(The first one won.) Each pair was asked with the headlines in both orders, and the two answers averaged, so neither headline benefits from being listed first.

## How it was measured
How often Jev's pick is the headline that actually got more clicks, separately for small, medium and large click gaps. The pairs whose gap is too large to be chance (a standard significance test) are also marked and reported on their own, since for the rest there may be no real winner to find.

## Caveats
- **A third of the pairs hidden.** A content filter hid 198 of the 600 pairs from the site because a headline touched sex, violence or politics. Emotional, dramatic stories were Upworthy's staple, so the pairs left lean toward the gentler ones.
- **One outlet, one era.** These are Upworthy's readers between 2013 and 2015, clicking the site's trademark curiosity-gap headlines. What worked on them may not work on today's readers or on other sites.
- **Jev may have seen some of these.** The Upworthy archive has been public for years and the headlines were widely shared, so Jev could have seen some of them, though not their click counts, in training.
- **Most gaps are noise.** Many tested pairs differ by a hair.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
