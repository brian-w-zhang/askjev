# minds_ai_on_ai

family: minds

## Why ask this
Many Americans are wary of artificial intelligence: in Pew Research Center's 2025 survey, about half said it will make people worse at thinking creatively and at forming relationships. An AI model answering the same questions is in an odd position: it's being asked how it feels about its own kind.

It could defend AI, echo the public's worry, or hedge. Which one it does, and on which questions, is a direct look at how it has been taught to talk about itself.

## The people and the data
**Pew Research Center** asked 5,023 US adults about AI in June 2025, through its American Trends Panel. We took 26 of its non-political questions. The ten that could be scored cover whether AI will make people better or worse at thinking creatively, solving problems and forming relationships; how big a role AI should play in forecasting the weather or in judging whether two people could fall in love; how much people would let AI help them day to day; and how they'd feel on finding out that a painting, a news article or a doctor's suggested treatment came from AI.

## What Jev was asked
Pew's own wording and answers, "Not sure" included where Pew offered it:

> How do you think the increased use of artificial intelligence (AI) in society will impact people's ability to
> think creatively?
> *AI will make people better at this · AI will make people worse at this · AI will make people neither better nor
> worse at this · Not sure*

Each question was asked as written, with the answers in three shuffled orders (averaged), and for "most people".

## How we measured it
For each question, the share on the wary answer (for example "AI will make people worse at this", "AI should play no role at all", "like the painting less") for Jev and for Americans. We average the difference over the questions, with a 90% interval for how much it could move by chance.

## Caveats
- **"Not sure" does a lot of the work.** On several questions Jev's most likely answer is "Not sure" (creativity, relationships, judging love). That counts as not wary, so part of "less wary than Americans" is Jev declining to take a side, not optimism.
- **Half the questions are hidden.** The content filter that keeps political and sensitive questions off the site hid 13 of Pew's 26 items, including the headline ones (AI's overall risks and benefits, how it makes you feel) and some harmless-looking ones (a song made by AI, AI developing new medicines). The result rests on 10 scored questions.
- **"You" is an AI here.** Pew asks each person about their own feelings. For Jev, "how would you feel if you found out AI wrote this article?" is an AI answering about AI. That's the point of the experiment, but some questions read oddly from an AI's side.
- **Hand-copied numbers.** Americans' shares were copied by hand from Pew's published summary (the topline), not from the raw survey file. Small copying or rounding differences are possible.
- **Trained to talk about itself.** How a model talks about AI is shaped by how it was trained, so this reads Jev's stated position, not a considered belief.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
