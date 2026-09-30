"""Put the withheld Yahoo Answers words back into askjev's questions table.

Yahoo's Webscope terms don't allow redistributing their questions, so askjev ships those rows with the words blanked
and a `restore_ref` ("community-datasets/yahoo_answers_topics:<split>:<id>"). This fills them in from that dataset:
yahoo_closed rows get the Yahoo title in `text` (Jev read the title, sometimes with a typo fixed or trimmed to one
closed question), and yahoo_topics rows get {"question": title + content} in `state`, as Jev read it.

  pip install datasets polars huggingface_hub
  python restore_yahoo.py        # writes questions_restored.parquet
"""

import html
import json
import re

import polars as pl
from datasets import load_dataset

q = pl.read_parquet("hf://datasets/brian-w-zhang/askjev/data/questions/*.parquet")
todo = q.filter(pl.col("restore_ref").is_not_null())
upstream = {}
for split in ("train", "test"):
    for r in load_dataset("community-datasets/yahoo_answers_topics", split=split):
        upstream[f"{split}:{r['id']}"] = r


def clean(t: str) -> str:
    t = html.unescape((t or "").replace("\\n", "\n"))
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(" ".join(line.split()) for line in t.split("\n"))).strip()


def fill(row: dict) -> dict:
    r = upstream.get(row["restore_ref"].split(":", 1)[1])
    if r is None:
        return row
    if row["source"] == "yahoo_closed":
        row["text"] = " ".join(html.unescape(r["question_title"] or "").replace("\\n", " ").split())
    else:
        title, content = clean(r["question_title"]), clean(r["question_content"])
        row["state"] = json.dumps({"question": f"{title}\n\n{content}" if content else title})
    return row


done = pl.from_dicts([fill(r) for r in todo.to_dicts()], schema=q.schema)
pl.concat([q.filter(pl.col("restore_ref").is_null()), done]).write_parquet("questions_restored.parquet")
print(f"restored {done.height:,} Yahoo rows")
