# askjev: agent guide

Private project: a tree housing every closed question (Noul / Choice / Score) that humans or machines
ask, answered by Jev, for understanding Jev's capabilities, defaults, and jaggedness. It's built as
outreach to TypeSafe. See `README.md`.

## Source of truth
- `docs/00-09` are **canonical** and consistent with each other. When they conflict with
  anything else, the docs win.
- `docs/08-roadmap.md` has a **decisions log**. Don't reopen settled decisions (name, 35/35/30
  hemispheres, private, gateway-only access, not-a-benchmark framing...) without asking Brian.
- The GitHub repo is **public**. Never commit secrets, `data/`, or the local-only personal folders
  (`resources/references/notion/`, `resources/conversations/`, both gitignored). The data and findings stay private.
- `resources/` is **read-only reference material**. `resources/conversations/` is historical and
  contains superseded ideas (e.g. the "Everything Asked" name, IAB roots, a pinned model version,
  public launch plans). Don't treat it as current.
- When a decision changes, update the relevant doc *and* the decisions log in the same change. Don't
  add "superseded by" notes; rewrite the doc so it states only the current plan.

## Rules that are easy to get wrong
- Never frame results as a benchmark, score, or leaderboard; use indicators.
- **Jev is the ONLY model you may call through the AI Gateway.** Never call another gateway LLM or
  embedding model. Do authoring (descriptions, synthetic questions, transforms) yourself or with
  subagents, and use a local embedding model.
- Env: `AI_GATEWAY_API_KEY` (Jev only) + `DATABASE_URL` (Postgres). Jev is
  `typesafe-ai/jev` via Vercel AI Gateway (32k context), and the served version is logged on every call.
- Terms: **node** = topic in the tree; **question** = canonical question attached to one node
  (never a tree node); **probe** = what's sent (question × frame × variant); **answer** = the response to
  one probe. Follow-ups and duplicates are `question_links`, not tree edges.
  **universe** = a named systematic rewording (terse, old-english...) applied as an overlay: same
  nodes and question ids, different probe text. Never copy the tree or add universe text as new questions.
- Jev option names are seen by the model; question IDs aren't. Score levels are judged in
  isolation ("describe situations, not degrees"). Follow `docs/01-jev.md` §7 when writing questions.
- Don't present TypeSafe's documented jaggedness (`docs/01-jev.md` §6) as a discovery.
- Keep contested politics off the displayed map (flag it, don't delete it).
- Cache every model call by request hash, and never re-send an identical request.
