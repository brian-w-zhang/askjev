# Jev: what we depend on

Verified 2026-09-24 against the full docs archive (`resources/references/typesafe-docs/`,
digest in `resources/references/typesafe-docs-digest.md`) and the Vercel AI Gateway
model listing. **UNVERIFIED** marks anything not confirmed.

## 1. How we call it
- **Jev is the only model called through Vercel AI Gateway** (`AI_GATEWAY_API_KEY` in `.env`; the other
  env var is `DATABASE_URL`, see `06-pipeline.md` §1). **No other gateway model may be used** (Brian's
  rule, 2026-09-24). Everything the docs call an "LLM step" (drafting node descriptions, synthetic
  questions, Score-level wording, universe transforms, split/group proposals) is done by **Claude Code
  itself or its subagents**, writing files that the pipeline ingests. Embeddings come from a **local
  open model** (`06-pipeline.md` §2).
- Model id **`typesafe-ai/jev`**. That's "latest" with no version suffix, and `type: "evaluation"` in the gateway listing.
- **The context window through the gateway is 32,000 tokens.** The direct API documents 64k for state plus all
  questions, and 32k for state plus the longest single question. The batch planner budgets
  **32k per request**.
- Pricing is $0.042 per 1M input tokens, with output free. The listing says `zdr: all` and `no_training: all`.
- **UNVERIFIED (first spike):** the request/response shape through the gateway. Does it
  accept the native `state` + `questions` body and return `probabilities`, `confidence`, and the
  served version?
- Because "latest" moves on release, **every call logs the served version**, and
  experiments never compare answers across versions. TypeSafe promises never to change a
  deployed version silently, and may keep 1.13.0 on long-term support (from the interview).
  The current version is `jev-1.13.0`, while most of TypeSafe's cookbooks ran on 1.12.

## 2. Request semantics (native API; the reference for meaning)
```jsonc
{"state": <string|object|array>,          // content being judged; prefer named fields
 "model": "...",
 "questions": {                            // IDs are NOT sent to the model
   "q1": {"type":"noul",  "instructions":"...", "criteria":{"true":"...","false":"..."}},  // criteria optional
   "q2": {"type":"choice","instructions":"...", "criteria":{"opt":"desc or null", ...}},  // ≤255 options (reliable to ~240)
   "q3": {"type":"score", "instructions":"...", "criteria":["level0","level1", ...]}}}    // 2..10 levels, low→high
```
- The full question goes in `instructions`, because IDs aren't seen. Option **names and
  descriptions are both sent** to the model, so names are never "neutral".
- `instructions` and criteria values can be objects. The field names are free-form but seen by
  the model. TypeSafe's pattern is `question`, `focus`, `inspect`, `compare`, and per-option
  `{what, not_for, examples, signals}` (the "contrastive criteria" pattern). Our tree
  nodes use exactly this shape (`02-tree.md` §4).
- State fields can be referenced in backticks, e.g. `` `ticket.messages[0].text` ``.

## 3. Response semantics
```jsonc
{"model":"jev-1.13.0",
 "answers":{
   "q1":{"type":"noul","noul":0.95},                                                    // no confidence on Noul
   "q2":{"type":"choice","choice":"billing","probabilities":{...},"confidence":0.81},
   "q3":{"type":"score","score":1.05,"legend":{...},"probabilities":{"0":0.0,"1":0.95,"2":0.05},"confidence":0.92}},
 "usage":{"input_tokens":N,"output_tokens":M}}
```
- `score` = Σ level × p, so it can fall between levels. Different distributions can give the
  same score. **Store the probabilities; display bands.**
- `confidence` (Choice and Score only) is derived from how peaked the distribution is, by a
  formula that isn't disclosed. Use `probabilities` for statistics. Values are rounded to about 2 decimals.
- Errors: 401 · 422 (the body names the field) · 429 · 529 overloaded. Retry 429/529 with backoff.

## 4. Limits and throughput
- **1,200 req/min and 250k tokens/s** ("adjusting dynamically").
- The cookbooks say rate limiting kicks in **above about 8 concurrent workers**, so we run about 8.
- Latency is about 100-150 ms per call.
- **Batching:** all questions over one state go in one request. They're evaluated independently,
  and batching doesn't change the answers. Cookbook numbers: 12.2× cheaper and 10× faster than separate calls.
- English works best.

## 5. Determinism
- There's no seed or temperature. The docs say it's "designed to return stable answers", with no guarantee.
- Observed: most answers have std 0.0 across repeats. Some Nouls vary (mean std ≈ 0.01; one
  ranged 0.43-0.53 across 15 runs), and Choice top labels sometimes flip.
- **For us:** the first response for a request hash is canonical. Experiment 0 measures
  the noise floor, and every reported effect must exceed it.

## 6. Jaggedness TypeSafe already documents (jev-1.13)
From `model-jaggedness/jev-1.13` (reviewed 2026-09-17). **Don't present these as discoveries.
Quantify them at scale and by topic, or go beyond them.**
1. Literal reading (answers the words, not the intent)
2. Math and numbers: counting, raw numeric values (hex/RGB is worse than names)
3. Date/time comparison
4. Indirection and double negatives
5. Large irrelevant state (context rot)
6. Adversarial content and prompt injection can move answers
7. Contradictory instructions or criteria
8. **No structural invariants.** A Noul and a yes/no Choice aren't comparable (0.22 vs 0.01), and
   P(q) + P(not q) ≠ 1 (their example sums to 1.19)
9. No generation

**Not on their list, and so our novel ground:** option-order and position bias, rewording (universe)
fragility by topic, transitivity, decoy/IIA effects, the self-vs-human frame gap,
calibration by topic and by industry (they publish no calibration metrics), and
placement stability. Also, "pairwise reranking" is claimed on their use-case page but
never demonstrated.

## 7. Question-writing rules (from the docs; they apply to every generator)
- **One snap judgment per question** ("something a knowledgeable person decides in a
  second"). Decompose composite judgments and weight the parts in code.
- **Choice:** give the full list plus `other`/`none`. Pair a Choice with an absolute Noul when
  "none fit" is possible (a Choice always has a winner).
- **Score:** describe *situations, not degrees*. Each level is judged alone, without its
  number or neighbors. Use one dimension, give rare extremes their own level, and never
  interpolate magnitudes.
- **Noul:** one condition, phrased so high means yes, never inverted criteria. 0.5
  means uncertain, not "medium".
- Keep content in the state and the judgment in the question. Send only the relevant context.
- "Name the narrowest fact that decides it."
- Thresholds are product policy: three bands (act / review / don't act), tuned per question.

## 8. Legal points that shape the project
My reading of the agreements, not legal advice. The sources are the MCA (typesafe.ai/legal/mca) and the AUP.
- Output rights belong to us (§4.2). Label AI output as AI (AUP 1.4).
- **AUP 3.7 bans probing vulnerabilities.** This is quality research, not security testing:
  keep prompt-injection attack work out of scope, and send findings privately first.
- §2.3(b) bans distillation and training imitators. Don't release the answer dataset in a way that
  invites training on it without asking.
- §16.4: no implied partnership or branding. "askjev" is fine privately; ask before going public.
- If an ask box ever goes public: §2.3(a) bans offering Jev "as a standalone service",
  and we'd be liable for end users (§5, §13). Ask TypeSafe first.

## 9. Company context
TypeSafe AI, Inc., in person in SF. Diogo Almeida (CEO, co-invented RLHF/InstructGPT),
Sasha Sheng (COO, handles hiring, best reached on Discord), Erik Gafni (CTO). Training is
RLCD, "reinforcement learning for calibrated decisions". Positioning: "Machine Native
Intelligence", "Build prod, not God", 99% machine-to-machine. They want people to
"experiment and do weird shit", and they collect failure-mode reports on Discord. Sources:
the transcript (`resources/transcripts/`) and the Notion notes (`resources/references/notion/`).
