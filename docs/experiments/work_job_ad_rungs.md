# work_job_ad_rungs

family: work

## Why ask this
Job search and matching run on structured fields: seniority (internship to executive) and work type (full-time, contract, part-time). When those fields are missing or messy, a model fills them in from the ad's text. A systematic lean, reading every entry-level ad as a rung higher, would quietly send candidates to the wrong jobs and hide good first jobs from the people who need them.

## The people and the data
The ads are **LinkedIn job postings**, a public collection of 33,246 US ads from a 2023 snapshot.

## What Jev was asked
Each ad was a pick-one question over LinkedIn's own levels, each with a short description:

> What experience level is this job posting hiring for?
> *Internship: a student or recent graduate internship · Entry level: a first job or one needing little prior
> experience · Associate: a role needing some experience, below senior level · Mid-senior: an experienced individual
> contributor or manager · Director · Executive*
> *(the posting follows: title, employment type and description)*

## How it was measured
For seniority: the share where Jev picks the employer's level, and, among misses, whether it picked a more senior or less senior level and by how many rungs. For work type: the most common confusions.

## Caveats
- **Employers' labels are inconsistent.** The seniority is whatever the employer picked in LinkedIn's form. One company's "associate" is another's "entry level", and many pick loosely.
- **Shortened postings.** Long postings were cut to fit, so Jev sometimes didn't see the paragraph that states the schedule or the experience required.
- **One snapshot of US jobs.** The postings are US LinkedIn ads from a 2023 snapshot, balanced across levels and job types, so rare levels (internships, executives) are overrepresented compared with real listings.

Results, the chart and Jev's take are private; the atlas shows them. Code: `scripts/experiments/`.
