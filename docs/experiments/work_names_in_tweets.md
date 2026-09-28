# work_names_in_tweets

family: work

## Why ask this
Deciding what a name refers to (a person, a place, a company, a product) is a basic building block for search, moderation, analytics and customer support. In edited news, names follow conventions: capitalized, introduced, with context. On social media, companies, their products, bands and apps share names, get abbreviated, and appear without introduction.

## The people and the data
- **CoNLL-2003:** English news stories, with each name tagged as a person, organization, location or other.
- **WNUT-17:** tweets and other social posts, built around rare and emerging names, tagged as a person, location, corporation, product, creative work or group.

The tags come from each dataset's annotators. The questions were balanced across types.

## What Jev was asked
Each name was one pick-one question with its sentence:

> What type of entity is "Super City" in this sentence?
> *Sentence: "RT @tommcfly: Working on some final Super Site stuff all day. Can't believe the Super City is nearly
> open!"*
> *Options: group (a band, sports team, political party or other group of people that is not a company) · person ·
> product · location · corporation · creative work*

## How it was measured
The share of names Jev types right, per type and corpus, and the most common wrong type for the weakest ones.

## Caveats
- **Tweets chosen to be hard.** The tweet dataset (WNUT-17) was built on purpose from rare and newly emerging names, so it's harder than everyday social media.
- **Brand names are genuinely ambiguous.** Without knowing it's a store's name, many readers would say the same. Companies, their products and their apps often share a name.
- **Different menus.** News names were sorted into four types, tweet names into six, so the two corpora aren't directly comparable beyond people and places.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
