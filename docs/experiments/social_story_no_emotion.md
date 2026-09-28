# social_story_no_emotion

family: social

## 1. Question
Reading short everyday stories, how often does Jev say a character feels no clear emotion, compared with the people who annotated them?

Reading feelings into plain events is most of what reading a story is. A reader that often answers 'no clear emotion' is being literal where people infer.

## 2. Sourcing
Existing StoryCommonsense questions (Rashkin et al. 2018): five-sentence stories, one character, 'Which emotion best describes ...' with Plutchik's eight emotions plus 'no clear emotion'; each with three MTurk annotators' labels. Enough: about 3,000 story lines.

Sources: `storycommonsense`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
The average share each label gets from annotators vs Jev's average probability on it; how often Jev's top pick is 'no clear emotion' when at least two of the three annotators named the same real emotion. 90% bootstrap intervals over story lines.

## 5. Visualization
Paired bars over the nine labels: annotators vs Jev.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 3.796, top verdict `headline`.

## Compared with
StoryCommonsense MTurk annotators (three per story line)

## Limits
Annotators were asked to find an emotion, which may push them away from 'none'. Literal reading is on TypeSafe's own list of known weak spots (01-jev §6, item 1); this measures it on stories.

Results: `data/analysis/experiments/social_story_no_emotion.json` (private). Code: `scripts/experiments/`.
