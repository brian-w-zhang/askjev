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


## Scores (0 fails, 1 mostly, 2 meets)
Screenshots for every score are in the session scratchpad (sweep*/, r1/, s*/), not the repo.

| Criterion | Map before | Map after | Portrait before | Portrait after | Atlas before | Atlas after |
|---|---|---|---|---|---|---|
| V1 no slop | 2 | 2 | 1 | 2 | 0 | 2 |
| V2 playful, honest | – | – | 2 | 2 | 1 | 2 |
| V3 no overclaiming | 2 | 2 | 1 | 2 | 1 | 2 |
| R1 one idea per card | – | – | 1 | 2 | – | – |
| R2 Wrapped pacing | – | – | 1 | 2 | – | – |
| R3 earned length | – | – | 1 | 2 | 1 | 2 |
| L1 TypeSafe language | 2 | 2 | 2 | 2 | 1 | 2 |
| L2 type scale | 2 | 2 | 1 | 2 | 1 | 2 |
| L3 memes | – | – | 1 | 2 | – | – |
| L4 charts | – | – | 1 | 2 | 1 | 2 |
| C1 themes, widths | 1 | 2 | 2 | 2 | 1 | 2 |
| C2 zero errors | 1 | 2 | 2 | 2 | 2 | 2 |
| C3 keyboard, a11y | 2 | 2 | 1 | 2 | 1 | 2 |
| C4 fast | 2 | 2 | 1 | 2 | 0 | 2 |
| C5 traceable | – | – | 2 | 2 | 2 | 2 |

What moved each score:
- **Map C1:** the nav chips sat on top of the open panel on phones; they now step aside. **C2:** a link to a topic
  that doesn't exist logged a 404; it's now checked first and dropped quietly. The only console line left is a
  deprecation warning from @react-three/fiber itself (`THREE.Clock`), still present in its latest release.
- **Portrait V1/V3:** ledger sentences and card copy reread three times; "built most of its own map" became "about
  27%", "can't tell a joke" became "can barely tell", a hard-coded meme number was wired to the data. **R1-R3:** the
  weakest cards (crowd agreement, "quieter than everyone") moved to the atlas; new cards come from real test-takers
  (online tests, career code) and real scales (checkup). **L3:** meme labels were drawn with Tailwind's `outline`
  utility by accident (white boxes); fixed. **C3:** calibration guesses work from the keyboard. **C4:** 1.37 MB of
  HTML to 0.70 MB (200 KB to 108 KB gzipped): receipts render when opened, the 2,869-dot scatter became a binned
  density grid, memes went from 2 MB of PNG to 170 KB of WebP.
- **Atlas:** first view is now findings as cards with section chips and counts (the table is one click away),
  readable sentences (topic names instead of ids, commas, ordinals, typical values), coverage as cards. **C4:** 848 KB
  to 196 KB (29 KB gzipped): topic and source tables load when their tab opens.

## Performance
| Measure | Before | After |
|---|---|---|
| /portrait HTML | 1,366 KB (200 KB gz) | 697 KB (108 KB gz) |
| /portrait/atlas HTML | 848 KB (132 KB gz) | 196 KB (29 KB gz) |
| memes | 2.0 MB | 170 KB |
| map API, warm | 10-60 ms | same |
| map API, cold | /api/layout 12 s, /api/node 2.2 s | same (edge-cached in production; the map session's code) |

Production, median of 3 cold loads at 1440 px (`scripts/portrait/vitals.mjs`):

| Route | LCP | CLS | TTFB | Transferred |
|---|---|---|---|---|
| / (map) | 64 ms | 0 | 23 ms | 5.9 MB (star snapshot, the map's own) |
| /portrait | 644 ms | 0.029, now 0 (tweet image sized) | 24 ms | 260 KB |
| /portrait/atlas | 188 ms | 0 | 28 ms | 40 KB |

## Changelog
**Changed**
- Rubric (this doc), research notes, and four scripts in `scripts/portrait/`: `sweep.mjs` (5 widths × 2 themes:
  errors, overflow, alt text, unnamed controls), `interact.mjs` (23 visitor steps across map, portrait, atlas),
  `vitals.mjs`, and `verify_page.py` against production (`ASKJEV_KEY`).
- Map: quiet bad deep links, nav chips out of the way of the phone panel, nav links no longer prefetch the portrait.
- Portrait: new cards from data already in the corpus (online tests vs ~50 Open Psychometrics scales and their real
  test-takers, the career code, the checkup on five wellbeing scales); weaker cards moved to the atlas; big-number
  cards for rhythm; a Wrapped summary at the end; density chart for gambles; five strongest and weakest knowledge
  domains; keyboard-operable calibration; copy reread three times for slop and overclaiming.
- Atlas: findings as cards with section facets and counts (table one click away), coverage as cards, topic names,
  tables loaded on demand, readable ledger sentences for every claim.
- Performance: portrait 1.37 MB to 0.70 MB of HTML, atlas 848 KB to 196 KB, memes 2 MB to 170 KB.
- Shipping: `sync_prod.py --delta` (changed rows in one transaction; 18 wellbeing questions in 50 s), stars
  rebuilt (1,048,982), portrait data and memes published privately (`publish.py`, `PORTRAIT_URL`), deployed.
  Production matches local: same question count, same 518 page numbers (`verify_page.py`), zero failed steps in the
  interaction sweep on desktop and phone.

**Experiments atlas (2026-09-28, `16-experiments-plan.md`)**
- The atlas became the experiments library: 192 cards with chart thumbnails, Jev's verdict and rank, a page per
  experiment; the old claims moved to a reference tab. Atlas HTML: 252 KB transferred, LCP 380 ms, CLS 0.
- Sweeps: `sweep.mjs` on map, portrait, atlas and experiment pages at five widths and both themes (no overflow; only the
  known `THREE.Clock` warning); `interact.mjs` extended to the experiments (search, family facet, a page, its map link,
  back), zero failed steps on production; `verify_page.py --experiments` checks every experiment page against its own
  entry, and production flags exactly what local flags (pager titles, axis ticks, names like choices13k).
- Shipping: 17,098 new questions synced (`--delta`; the post-sync `analyze` hit a dropped connection and was re-run by
  hand), 39 new topics, stars rebuilt (1,066,067), portrait and experiments published (`publish.py`), deployed.
  Production matches local: 1,066,067 questions, 1,737 nodes, 192 experiment pages.

**Left**
- `THREE.Clock` deprecation warning from @react-three/fiber (fixed only by an upstream release).
- Cold map API latency: `/api/node` no longer counts a million rows on a cold function (counts come from the star
  snapshot), the panel opens before its data, and the dots are cached by browsers (docs/07-ui.md, Deployment).
  `scripts/portrait/perf.mjs` times first dots, topic and dot clicks, and nav switches on a desktop and a phone.
- GitHub builds need Brian to link GitHub in Vercel (the deploy session's open item); deploys run from this machine.
- A stories mode (tap-through cards) can wrap the same cards later.
