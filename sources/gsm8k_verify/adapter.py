"""GSM8K (Cobbe et al. 2021, OpenAI): 8,792 grade-school math word problems with human-written step-by-step
solutions ending in "#### <answer>".

Template "gsm8k.final_correct" (Noul, node machine.education.answer_grading): is the final answer in
`solution` correct? Half the solutions are shown as written (truth true). The other half are perturbed
(truth false): the final answer N is replaced by a wrong value N' and so is the last mention of N in the
worked steps (usually the result of the last calculation), so the solution reads as a consistent
slip in the last step rather than a mismatch between the steps and the final line. The perturbation is
chosen per item by a seeded RNG: ±1, ±2, ±10, ×2, ÷2 (even N), or a swapped/changed digit; N' is a
positive integer different from N. meta records original, shown and method.
Solutions are cleaned of GSM8K calculator annotations (<<48/2=24>>) and end with "Final answer: N".
Problem + solution kept to ≤1,500 chars. Train + test.
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "gsm8k_verify"
BASE = "https://huggingface.co/api/datasets/openai/gsm8k/parquet/main/{split}/0.parquet"
SPLITS = ("train", "test")
TARGET = env_int("TARGET_GSM8K_VERIFY", 2000)
LICENSE = "MIT"
TEXT = "Is the final answer in `solution` the correct answer to `problem`?"
CRITERIA = {
    "true": "The final answer is the correct answer to the problem",
    "false": "The final answer is wrong",
}
SEED = 8792


def fetch(raw_dir: Path) -> None:
    for split in SPLITS:
        out = raw_dir / f"{split}.parquet"
        if out.exists():
            continue
        r = httpx.get(BASE.format(split=split), follow_redirects=True, timeout=120)
        r.raise_for_status()
        out.write_bytes(r.content)


def _num_pattern(n: int) -> re.Pattern:
    plain, comma = str(n), f"{n:,}"
    alts = {re.escape(plain), re.escape(comma)}
    return re.compile(r"(?<![\d.,])(" + "|".join(sorted(alts, key=len, reverse=True)) + r")(?![\d]|[.,]\d)")


def _perturb(n: int, rng: random.Random) -> tuple[int, str]:
    for _ in range(20):
        method = rng.choice(["+1", "-1", "+2", "-2", "+10", "-10", "x2", "/2", "digit"])
        if method == "x2":
            m = n * 2
        elif method == "/2":
            if n % 2:
                continue
            m = n // 2
        elif method == "digit":
            s = list(str(n))
            if len(s) >= 2 and rng.random() < 0.5 and s[-1] != s[-2]:
                s[-1], s[-2] = s[-2], s[-1]
                method = "swap_last_digits"
            else:
                i = rng.randrange(len(s))
                s[i] = str((int(s[i]) + rng.choice([1, 2, 3, 7, 8, 9])) % 10)
                method = "change_digit"
            if s[0] == "0":
                continue
            m = int("".join(s))
        else:
            m = n + int(method)
        if m > 0 and m != n:
            return m, method
    return n + 1, "+1"


def normalize(raw_dir: Path) -> Iterator[Question]:
    items = []
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, q, a in df.select("row", "question", "answer").iter_rows():
            body, _, final = a.rpartition("####")
            final = final.strip().replace(",", "")
            if not re.fullmatch(r"\d+", final):
                continue  # negative or decimal answers: keep the perturbation space simple
            body = re.sub(r"<<[^>]*>>", "", body).strip()
            q = " ".join(q.split())
            if len(q) + len(body) > 1400:
                continue
            items.append((f"{split}:{row}", q, body, int(final)))

    sample = sorted(hash_order(items, lambda x: x[0], "gsm8k.final_correct")[:TARGET])
    flip = set(x[0] for x in hash_order(sample, lambda x: x[0], "gsm8k.flip")[: len(sample) // 2])
    rng = random.Random(SEED)
    for sid, q, body, n in sample:
        meta = {"original": n}
        shown_body, shown = body, n
        if sid in flip:
            shown, method = _perturb(n, rng)
            matches = list(_num_pattern(n).finditer(body))
            if matches:
                m = matches[-1]
                rep = f"{shown:,}" if "," in m.group(1) else str(shown)
                shown_body = body[: m.start(1)] + rep + body[m.end(1):]
            meta.update({"shown": shown, "method": method, "last_step_changed": bool(matches)})
        solution = f"{shown_body}\nFinal answer: {shown}"
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"problem": q, "solution": solution},
            shape="verify",
            node_hint="machine.education.answer_grading",
            template_id="gsm8k.final_correct",
            source_item_id=sid,
            license=LICENSE,
            truth=sid not in flip,
            meta={**meta, "perturbed": sid in flip},
        )
