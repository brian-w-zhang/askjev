#!/usr/bin/env bash
# Phase 6: regenerate every machine source at its scaled-up target (docs/09-mvp-plan.md, Phase 6).
# Adapters keep their original seeded sample (unset env = original target, identical ids) and grow it
# prefix-stably, so the Phase 5 questions stay a subset. ASKJEV_EXTRA_* sizes each secondary template.
# Normalizes only (fetch + normalize -> data/normalized/<name>.jsonl); ingest separately.
set -euo pipefail
cd "$(dirname "$0")/.."

export ASKJEV_TARGET_BANKING77=3000
export ASKJEV_EXTRA_BANKING77=1500            # banking77.urgency, banking77.money_left
export ASKJEV_TARGET_SMS_SPAM=3000
export ASKJEV_EXTRA_SMS_SPAM=1500             # sms.call_to_action
export ASKJEV_TARGET_JAILBREAKS=1200
export ASKJEV_TARGET_EMOTION=2500
export ASKJEV_TARGET_SCIFACT=100000           # every pair that fits in 1,500 chars
export ASKJEV_TARGET_UNFAIR_TOS=4000
export ASKJEV_EXTRA_UNFAIR_TOS=1500           # unfair_tos.clause_type
export ASKJEV_TARGET_FINANCIAL_PHRASEBANK=2200
export ASKJEV_TARGET_AMAZON_REVIEWS=4000
export ASKJEV_EXTRA_AMAZON_REVIEWS=1500       # amazon.topic
export ASKJEV_TARGET_MSMARCO_RELEVANCE=4000
export ASKJEV_EXTRA_MSMARCO_RELEVANCE=1500    # msmarco.relevance_level
export ASKJEV_TARGET_CODE_LANG=1500
export ASKJEV_TARGET_PEOPLE_DOCS=2500

# World hemisphere
export ASKJEV_TARGET_BOOLQ=6000
export ASKJEV_TARGET_OPENTDB=100000           # every clean item (a full per-category sweep at 5.5 s/request)
export ASKJEV_TARGET_LANCASTER=2000           # 400 words x 5 senses
export ASKJEV_TARGET_MANIFOLD=600

for s in banking77 sms_spam jailbreaks emotion scifact unfair_tos financial_phrasebank amazon_reviews \
         msmarco_relevance code_lang people_docs typesafe_seeds \
         boolq opentdb lancaster manifold; do
  uv run askjev source "$s"
done
