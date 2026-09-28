# taste_top_book

family: taste

## Why ask this
A favorite book is a small self-portrait: it says what a reader values (ideas, plot, comfort, jokes). Asking a model about thousands of books one at a time gives a real ranking, and a final among its top picks settles the order at the top. The question is what kind of reader that makes Jev.

## The people and the data
No people here: this is Jev against its own opinions. How Jev's taste compares with Goodreads readers is its own experiment ("Jev's taste in books vs Goodreads readers").

## What Jev was asked
Every book one at a time, with five answers describing what you'd actually do:

> How much would you enjoy reading Shift by Hugh Howey?
> *You'd put it down after a chapter or two · You'd finish it out of duty and forget it soon after · You'd enjoy it
> once and not reread it · You'd recommend it to a friend · You'd reread it and count it among your favorite books*

Each was also asked with the answers in reverse order, and the two averaged. Then the 24 highest-rated books played a round-robin final: 276 games of "Which book would you rather read?", each asked with the titles in both orders.

## How it was measured
A book's rating is where Jev's answer lands on the five levels (0 to 4). In the final, each game gives the winner Jev's probability of picking it, so a lopsided game counts as nearly a whole win and a close one as about half. The order comes from a standard way of ranking players from head-to-head results (a Bradley-Terry model).

## Caveats
- **The final was close.** Swapping two of them would take very little, so read the top five as a group more than an order.
- **The catalog decides the contest.** The books are the most-rated titles on Goodreads (each with at least 2,000 ratings): a popular, English-language list from 2017. A reference manual and a scripture turning up at the bottom says as much about what's in the catalog as about Jev.
- **The finalists were picked by Jev's own ratings.**

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
