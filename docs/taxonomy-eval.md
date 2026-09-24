# Known-path taxonomy test: Shopify product taxonomy (120 leaf items)

Jev walks Shopify's own tree (beam K=3, children names only as options) from the top, given only the
depth-5 leaf category name. Accuracy of the predicted path prefix at each depth:

- depth 1: 74.2%
- depth 2: 65.8%
- depth 3: 59.2%
- depth 4: 58.3%

This validates the placement machinery (beam search, geometric-mean path score) on a tree with known answers.
