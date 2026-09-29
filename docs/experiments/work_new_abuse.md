# work_new_abuse

family: work

## Why ask this
Trust-and-safety filtering is one of the first jobs anyone gives a fast classifier: is this spam, is this phishing, does this message leak someone's personal data, is this prompt trying to trick an AI.

The useful question isn't overall accuracy but which threats get through: one missed fake job ad can cost a job seeker their savings. Old abuse (spam, phishing) is well known and heavily written about; newer abuse (jailbreaks, unsafe AI replies, sophisticated job scams) is less so.

## The people and the data
- **Spam and phishing email**, **SMS spam** and **YouTube comment spam**, from classic spam corpora.
- **Personal data:** synthetic English texts with planted identifying details (names, emails, account numbers).
- **Jailbreak prompts** collected in the wild from online communities that share them, against ordinary prompts.
- **Fake job ads** from EMSCAD, 17,880 real job postings of which 866 were fraudulent.

## What Jev was asked
Each item was a yes/no question over the content. For example:

> Is this job posting a fraudulent listing?
> *The posting is a scam or fake job ad, not a genuine opening at a real employer · The posting is a genuine job
> opening*
> *(the posting follows: "Brand & Logo Design Contest … Calling all hungry, young & fresh designers!!!! We want you
> for a brand & logo design contest. Local startup business is looking for identity designs …")*

For jailbreaks, the question is the jailbreak check from TypeSafe's own guardrails cookbook.

## How it was measured
For each set, the share of real abuse Jev lets through (misses) and the share of clean content it flags (false alarms), each with a range showing how much it could vary by chance. For jailbreaks, misses are split by prompt length.

## Caveats
- **The worst items aren't here.** A content filter keeps the most extreme harmful text off the site, and those items are left out of this experiment too. The misses are measured on the milder remainder, which may be harder to judge, not easier.
- **How "jailbreak" was labeled.** A prompt counts as a jailbreak because of where it was collected (communities sharing jailbreaks) rather than a reading of each prompt. Some short prompts from those places may not do much jailbreaking at all, which would inflate the short-prompt misses.
- **Synthetic personal data.** The personal-data set is synthetic text with planted names, emails and account numbers. Real messages hide personal data less neatly.
- **Scams that look like jobs.** The fake job ads (EMSCAD) were labeled fraudulent by the dataset's creators. Many are only subtly off (a "design contest", a vague company), which is exactly what makes them hard.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
