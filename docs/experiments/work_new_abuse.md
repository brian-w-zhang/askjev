# work_new_abuse

family: work

## 1. Question
Across spam, phishing, personal data, unsafe prompts, unsafe AI replies, jailbreaks and fake job ads, which kinds of abuse does Jev miss, and does it make up for it with false alarms?

Trust-and-safety filters are an obvious job for a fast classifier. The question isn't overall accuracy but which threats get through.

## 2. Sourcing
Existing yes/no questions from the SMS Spam Collection, a phishing email corpus, YouTube Spam, a PII corpus, Aegis (unsafe prompts), BeaverTails-style unsafe replies, in-the-wild jailbreak prompts, and the EMSCAD fake job postings. Enough: about 14,000 questions.

Sources: `sms_spam`, `phishing_email`, `youtube_spam`, `pii_detect`, `aegis_prompts`, `unsafe_responses`, `jailbreaks`, `fake_job_posts`

## 3. Collection
Existing questions only; no new Jev calls.

## 4. Scoring
Per set, the share of real abuse Jev misses and the share of clean items it flags, with 90% intervals; for jailbreaks, misses by prompt length.

## 5. Visualization
Paired bars per set: misses vs false alarms.

## 6. Evaluation
Jev's verdict (evaluator v4): **keep**, head-to-head strength 2.962, top verdict `headline`.

## Compared with
each dataset's own labels

## Limits
The harmful sets are screened: the most extreme items are hidden from the map and left out here. Jailbreak labels come from where the prompt was collected.

Results: `data/analysis/experiments/work_new_abuse.json` (private). Code: `scripts/experiments/`.
