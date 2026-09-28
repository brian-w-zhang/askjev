# language_hex_colors

family: language

## Why ask this
Designers, developers and anyone working with a web page constantly deal with colors written as codes: #fdff63 is a pale yellow. A model that helps with that work needs to know roughly what color a code is, or at least which name fits it.

TypeSafe's own documentation says Jev is weak at raw numbers like these. This experiment measures how weak, with an answer key made by a huge crowd, and separates "no idea at all" from "right family, wrong shade".

## The people and the data
In 2010 the webcomic **xkcd** ran an online color survey: people were shown random colors and typed whatever name came to mind. About 222,500 people took part, and the result is a list of 949 colors with the name most people used for each (released into the public domain). It has since become a standard reference, built into common software.

We picked 150 colors.

## What Jev was asked
> Which name fits the color with the hex code #fdff63 best?
> *canary · tomato · deep brown · light mustard*

(The survey's name is "canary"; "light mustard" is the look-alike.) Each question was asked with the names in three different orders, and the answers averaged.

## How we measured it
How often Jev's top pick is the survey's name, against 25% for a random guess, with a 90% interval. For the misses, whether they went to the look-alike (right family, wrong shade) or to a far color (no idea).

## Caveats
- **A known weak spot.** TypeSafe lists raw numbers, and hex and RGB values especially, among Jev's documented weak spots. This experiment measures that limit; it doesn't discover it, which is why it stays small.
- **It may be recall, not seeing.** The xkcd color list is copied everywhere: the popular plotting library matplotlib ships all 949 names with their exact hex codes. Jev may partly be remembering name-code pairs from code it was trained on rather than working out the color.
- **The look-alike can be a fair answer.** The near option is the closest other survey color, at least 40 steps away on the red-green-blue scale. Some of those pairs are genuinely hard for people too, so a "miss" to the look-alike is often a defensible pick.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
