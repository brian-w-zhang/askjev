# 12. Polish rubric

What "done" looks like for the three surfaces (map, portrait, atlas), written from Brian's feedback. Every iteration
scores each surface against it, before and after, with screenshots (kept in the session scratchpad, not the repo).
Scores are 0 (fails), 1 (mostly), 2 (meets).

## Voice
- **V1 No slop.** No report voice, no think-piece lines, no "we", no "tapestry/delve/crucial". Short sentences a person
  would say. The words sound like a toy someone made, not a consultancy.
- **V2 Playful but honest.** Jokes sit on top of true numbers. Claims say "your answers say", not "you are"; every card
  has fine print saying what the number can't tell you; hand-picked things say so; known limits (01-jev §6) are
  labeled as known.
- **V3 No overclaiming.** A 56% is "barely", not "can't"; 27% is "about a quarter", not "most". Nothing framed as a
  benchmark, ranking or overall score.

## Rhythm
- **R1 One idea per card.** A reader gets each card's point in five seconds without reading the fine print.
- **R2 Wrapped pacing.** Mix of big-number cards, charts, lists and memes; no three similar cards in a row.
- **R3 Earned length.** Nothing boring or repeated; every card would be missed if cut.

## Look
- **L1 TypeSafe language.** OS windows with pixel title bars, white nav chips, full-bleed color fields, crop marks,
  dither used sparingly; restraint over decoration.
- **L2 Type scale.** Small type except rare big numbers; one big headline per page at most; body 15-17px, fine print
  12-13px; nothing shouting.
- **L3 Memes.** Relevant to the card's number, current and not "unc", about one card in three, never on values
  cards, varied placement (beside, below, inline), captions from real numbers.
- **L4 Charts.** Direct labels, the takeaway visible without a legend hunt, no chart junk, legible at 360px.

## Craft
- **C1 Both themes, all widths.** 1440, 1024, 768, 390, 360: no horizontal scroll, overlaps, clipping or unreadable
  text; dark mode as considered as light.
- **C2 Zero console errors**, zero hydration warnings, no broken states (empty, slow, missing data, offline).
- **C3 Keyboard and screen reader basics.** Focus visible, controls reachable, images with alt text, landmarks.
- **C4 Fast.** First paint and interaction feel instant; payloads sized to what the page shows.
- **C5 Traceable.** Every number on the page equals the ledger (`verify_page.py`).

## Per surface
- **Map:** the sky stays as is; judged on the chrome (search window, panels, nav chips, deep links, back/forward).
- **Portrait:** all of the above; the story reads start to finish as "how's Jev doing?".
- **Atlas:** a first view that says what it is in one glance; findings, coverage, topics and sources easy to scan,
  search and sort; links into the map and back to the portrait.

## Research (what to borrow, what to avoid)
- **typesafe.ai / docs.typesafe.ai.** Borrow: one full-bleed color per page (pink, teal, sage, magenta, ink); a narrow
  text column with a thin left rule; tiny mono labels over paragraphs; huge grotesk only for the page's one headline;
  plain tables with a grey header row; the docs' tabbed example box (chips over one example); their own launch post
  ends "see below for the receipts", the same move as the portrait's receipts. Avoid: copying their hero art or
  logo, and anything that reads as an official TypeSafe page.
- **Spotify Wrapped and story formats.** Borrow: one stat per screen, the number first and the sentence under it,
  bold color changes between screens, a progress indicator, a shareable summary at the end. Avoid: tap-only
  navigation that hides the fine print (keep scroll + receipts); confetti and motion for its own sake.
- **The Pudding.** Borrow: a grid of story cards with a numbered chip, a date and a colored thumbnail; one real
  example before any aggregate; the reader answers first. Avoid: long scrollytelling for a point one chart makes.
- **Our World in Data explorers and search.** Borrow: picker rows (area, indicator, metric) that swap one chart;
  search results as cards with a mini chart and a one-line definition; sentence titles. Avoid: dense multi-panel
  control bars, cookie-banner-style chrome.
- **Searchable data catalogs** (OWID search, Datasette-style tables). Borrow: a search box that filters instantly,
  facet chips with counts, sortable columns, a detail view per row with provenance. Avoid: tables as the first view;
  a first-time visitor should see a few findings before any table.

## Scores
Filled in per iteration (see the changelog at the end of this file).
