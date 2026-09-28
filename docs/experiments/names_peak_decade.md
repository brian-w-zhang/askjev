# names_peak_decade

family: names · new questions: 107

## 1. Question
Given a first name, does Jev know the decade when it was most popular for US babies?

FiveThirtyEight's 'how to tell someone's age when all you know is her name' made this famous: names carry a birth year. A model that knows the curves can tell a Mildred from a Madison.

## 2. Sourcing
New questions (sources/baby_names): 'In which decade were the most US babies named "<name>" born?', options the 1880s to the 2010s; about 10 names peaking in each decade (30,000+ babies, a clear peak). Truth from SSA birth records.

Sources: `baby_names`

## 3. Collection
107 new questions, each in three shuffled orders (averaged).

## 4. Scoring
Share where Jev's top decade is the peak; share within one decade; mean error in decades, by the true decade (does it know old names as well as new ones?); direction of the misses.

## 5. Visualization
A confusion strip: true peak decade (x) vs Jev's decade (y), dot size = names; plus ridges for a few names (records' births by decade vs Jev's distribution).

## 6. Evaluation
Run `scripts/experiments/evaluate.py new`; the verdict is stored with the result.

## Compared with
US Social Security Administration birth records, 1880-2017

## Limits
Births, not living people: a name that peaked in the 1910s has few living bearers.

Results: `data/analysis/experiments/names_peak_decade.json` (private). Code: `scripts/experiments/`.
