# words_sound_shapes

family: words

## Why ask this
Show people a round blob and a spiky star and ask which one is "bouba" and which is "kiki". Most people, in most languages tested, call the blob "bouba" and the star "kiki". This **sound symbolism** extends to made-up words in general: "noo-moo" sounds soft and round, "pee-kay" sharp and pointed.

A model can't hear, but it has read about the effect and has seen which letters go with which kinds of words. It might reproduce the effect, flatten it, or exaggerate it.

## The people and the data
Two datasets:
- **McCormick and colleagues (2015):** 536 made-up words, each heard as a recording and rated by about 52 people on how round or pointed it sounds.
- **Ćwiek and colleagues (2022):** the classic bouba/kiki test run with 917 people speaking 25 languages; each heard one of the words and picked a drawn shape.

## What Jev was asked
For each made-up word, a seven-level question written for this project:

> Say the made-up word "noo-moo" (IPA /numu/) out loud. Does it sound more like a round shape or a pointed shape to
> you?
> *It sounds like a smooth, soft blob with no corners at all, like a cloud · It sounds curved and soft, with a corner
> or two at most · It sounds more like curves than points, though not entirely smooth · It sounds just as much like
> curves as like points · It sounds more like corners and edges than curves, though not entirely sharp · It sounds
> angular and sharp, with a curve or two at most · It sounds like a jagged, spiky shape, all sharp points, like a star
> or broken glass*

Plus the two classic questions, which describe a round, blob-like shape and a spiky one and ask which would be called "bouba" and which "kiki". Each was also asked with the answers reversed, and averaged.

## How it was measured
The ranking of the 536 words by Jev and by people (a rank correlation: 1 means the same order); how widely each side's ratings spread (their standard deviation); and for bouba and kiki, the share choosing the expected shape.

## Caveats
- **People heard the words, Jev read them.** Raters heard recordings of each made-up word. Jev read a respelling written for this project ("noo-moo") plus its phonetic spelling. Reading "pee-kay" may make the spiky letters (k, p) stand out more than hearing it does.
- **The effect is famous.** Bouba and kiki are one of the best-known results in psychology, and widely written about.
- **Words for shapes, not pictures.** For bouba and kiki, people heard the word and picked between two drawn shapes. Jev got the shapes described in words ("round and blob-like", "spiky"), which spells out the contrast.
- **No license on the data.** Both datasets are posted publicly without an explicit data license; they're used for private research only.
- **One scale from two questions.** Half the raters were asked how pointed each word sounds and half how rounded; the two are combined into one round-to-pointed scale, as the study's authors do.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
