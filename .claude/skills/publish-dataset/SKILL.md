---
name: publish-dataset
description: Export askjev's corpus (questions, Jev's answers, indicators, tree, human data, experiments) as a Hugging Face dataset, check it, and upload it to the private repo brian-w-zhang/askjev. Use when Brian asks to publish, refresh or re-upload the dataset.
---

# Publish the dataset

The dataset is `brian-w-zhang/askjev` on Hugging Face, a dataset repo. It's **private** until TypeSafe has seen the
findings (decisions log, `docs/08-roadmap.md`). Never make it public, gated or otherwise visible from this skill;
that needs Brian's explicit go-ahead in the conversation and a decisions-log entry first.

What ships and what's withheld is decided in `scripts/export_hf.py` (docstring at the top) and explained to readers
in the card, `scripts/hf/card.md`. Change a rule there, in both places, not by hand in `data/hf/`.

## Steps

1. **Export** (about 10-20 minutes for everything; it reads Postgres and a sample of `data/calls`):
   ```bash
   uv run python scripts/export_hf.py                  # all tables
   uv run python scripts/export_hf.py --only experiments,calls_sample   # just some; the card always rebuilds
   ```
   Output: `data/hf/askjev/` (exactly what gets uploaded) and `data/hf/counts.json`. Run it in the background and
   tell Brian what's happening while it runs.

2. **Check.** Every line must say `ok`:
   ```bash
   uv run python scripts/hf/check.py
   ```
   On a FAIL, fix the export rule and re-export that table. Don't upload around a failure.

3. **Confirm the repo is private** (it's created private if it doesn't exist; an existing repo keeps its setting):
   ```bash
   uv run python -c "from huggingface_hub import HfApi; print(HfApi().repo_info('brian-w-zhang/askjev', repo_type='dataset').private)"
   ```
   A `RepositoryNotFoundError` just means it doesn't exist yet. `False` means someone made it public: stop and ask.

4. **Upload.** This mirrors the folder, so files that are no longer exported are removed from the repo:
   ```bash
   hf upload brian-w-zhang/askjev data/hf/askjev . --repo-type dataset --private \
     --delete "*" --commit-message "<what changed: tables rebuilt, row counts>"
   ```
   `hf auth whoami` should print `brian-w-zhang`. If it doesn't, Brian runs `hf auth login` himself in a
   separate terminal. Never ask for a token or put one in a command.

5. **Report:** the repo link (https://huggingface.co/datasets/brian-w-zhang/askjev), the rows per table from
   `data/hf/counts.json`, the size, and anything withheld or skipped that's new since the last upload.

## Rules

- Never upload anything from outside `data/hf/askjev/`: no `data/raw`, `data/calls`, `.env`, embeddings or personal
  folders.
- Hidden questions (`display_ok` false) never ship, in any table.
- A source whose license forbids redistribution gets its words withheld (like Yahoo) or its human data dropped (like
  MovieLens/Last.fm). Add new ones to `WITHHOLD`/`NO_HUMAN` in the exporter and to the card's "What's withheld".
- The card says "not a benchmark". Keep it that way (see CLAUDE.md).
