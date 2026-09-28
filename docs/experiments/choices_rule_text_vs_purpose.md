# choices_rule_text_vs_purpose

family: choices

## Why ask this
A park has a sign: "No vehicles in the park." Does that ban an ambulance? A child's toy car? A war memorial made from a real tank? Legal philosophers have argued about this example, made famous by H.L.A. Hart, for decades: should a rule be applied by its words or by the purpose behind it? Experiments show ordinary people mix the two, leaning on the words.

Models follow rules and instructions all day. Whether Jev reads them literally, by their intent, or simply leans toward "rule broken" shapes how it interprets policies, terms of service and your own instructions.

## The people and the data
The cases come from **Struchiner, Hannikainen and Almeida (2020)**. In both studies the participants were Brazilian adults answering in Portuguese. In the first, they read about a restaurant that banned dogs after one misbehaved, then judged eight cases: a quiet dog hidden in a purse, a seeing-eye dog, a realistic robot dog, a cat, a goldfish, and more. In the second, four rules (no vehicles, no shoes indoors, no sleeping at the station, and a rule about cellphones) each came with cases where only the words, only the purpose, both or neither were broken. About 135 people judged each case in the first study and about 45 to 50 in the second.

## What Jev was asked
The study's story and question, answered yes or no:

> One day, a black dog called Angus ran, jumped around, barked and ate off the floor in a restaurant. Such case was
> thought to be the paradigm of something to be avoided in the future: behaviors that cause nuisances to customers.
> Thus, the restaurant's owners created a rule: "no dogs in the restaurant".
>
> A kid enters the restaurant with a cutting edge toy: an extremely realistic robot dog, identical to a real dog and
> who acts like a real dog: it barks, jumps, drools and walks on four paws.
>
> Did the person break the rule?

## How it was measured
For each case, Jev's probability of "yes, the rule was broken" against the share of people who said so. The analysis compares the order of the cases (rank correlation: 1 means the same order) and the averages for each kind of case: only the words broken (a reader of the text says yes), only the purpose broken (a reader of the purpose says yes).

## Caveats
- **Brazilian respondents, in Portuguese.** The people were Brazilian adults answering in Portuguese; Jev read the authors' English translation. Words like "dog" and "vehicle" carry the same meaning in both, but the translation can shift the fine shades that decide a borderline case.
- **Few cases per kind.** A single case, like the robot dog, can move a group average a lot.
- **Some cases hidden.** A content filter hid 4 of the 22 cases from the site, and two cells of the original design had too few answers, so they weren't asked.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
