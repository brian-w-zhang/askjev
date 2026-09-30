# work_money_news_mood

family: work

## Why ask this
A line like "The order comprises all production lines for a plywood mill, company said in a statement received by Lesprom Network." is the kind of thing a news feed, an analyst's summary tool or a trading desk sorts every day into good, bad or neither. Much of this flow is neutral: it reports something without telling an investor whether to be pleased or worried.

A model doing the sorting will sometimes err on neutral items, which is expected. What matters is which way. If its mistakes fall evenly on both sides, they wash out. If it hears good news in neutral items more often than bad, every digest it writes tilts rosier than the news, and across thousands of items the tilt adds up.

## The people and the data
Three labeled datasets, each with its own labelers:

- **Financial PhraseBank** (Malo, Sinha, Korhonen, Wallenius and Takala, 2014): about 4,840 sentences from English news about companies listed in Helsinki, each labeled positive, neutral or negative by 5 to 8 of 16 annotators with a finance background (3 researchers and 13 master's students at Aalto University School of Business). They were told to judge each sentence only as an investor would (might this news move the stock price up, down or not at all?), so a sentence with no financial relevance counts as neutral. Only the 2,264 sentences all annotators agreed on were used here, so these are the clearest labels of the three.
- **Market tweets**: an English set of finance tweets on Hugging Face, labeled bullish, bearish or neutral. Its description says the tweets came through the Twitter API but not who labeled them.
- **Gold-price headlines** (Sinha and Khandait): 11,412 headlines about gold from 2000-2019, scraped from sites such as Reuters, Bloomberg and Kitco and labeled by three human annotators who were subject-matter experts, reading the headline only, with disagreements settled by consensus. Of their nine yes/no labels, two are used here: "price going up" and "price going down". A headline with neither counts as neutral, which includes headlines about gold that aren't about its price at all.

## What Jev was asked
Each item was a separate multiple-choice question. The company-news sentences read, for example:

> What is the sentiment of "For 2009, net profit was EUR3m and the company paid a dividend of EUR1.30 apiece." for the company's investors?
> *neutral: Neither good nor bad news for the company's investors · negative: Bad news for the company's investors ·
> positive: Good news for the company's investors*

The tweets were asked "Is [the tweet] a bearish, bullish or neutral signal for the stock or market it mentions?", with neutral described as "It reports news or data with no clear direction for the price". The headlines were asked "Does [the headline] report the gold price going up, going down, or neither?", with neither described as "The headline reports no rise or fall in the gold price". The question wording and the descriptions were written for this project; the texts and the labels are the datasets'. Every question was also asked with the answers in three shuffled orders, to check that the order didn't drive the pick.

## How it was measured
For each dataset, take only the items its labelers called neutral, and count how often Jev's most likely answer was good news (positive, bullish, up) and how often it was bad news (negative, bearish, down). The lean is the ratio of the two. A 90% interval comes from resampling the items.

As a check, the same count on the clearly good and clearly bad items: how often Jev gets the direction backwards. If it did that often, a lean on neutral items could just be noise.

## Caveats
- **Neutral is the hardest label.** Neutral is where labelers disagree most, and the three datasets define it differently. In the Financial PhraseBank, any sentence with no effect on the stock price counts as neutral, including a profit figure with no comparison. Some of Jev's "misses" are borderline items, and at least one looks like a label slip (a hand-picked gold headline about a record close is labeled "neither").
- **The label descriptions are this project's.** Jev saw descriptions written for this project, not the labelers' instructions. The PhraseBank labelers judged each sentence as investors; Jev read "Neither good nor bad news for the company's investors". The tweet options illustrate bullish and bearish with examples (an upgrade, a beat; a downgrade, a miss), while neutral has none.
- **One possible reading, not a finding.** Company announcements are often written to sound positive. Jev may take that framing at face value where the finance-trained labelers discounted it. This experiment doesn't test that; it would need items where the spin and the substance are varied separately.
- **Who labeled the tweets is unknown.** The tweet dataset's public description says the tweets came from the Twitter API but not who labeled them or how, so less is known about its neutral label than about the other two. A content filter that hides political and sensitive questions from the site removed a few dozen tweets.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
