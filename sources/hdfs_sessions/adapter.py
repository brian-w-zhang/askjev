"""Loghub HDFS_v1 (Xu et al., SOSP 2009; Zhu et al., ISSRE 2023): 11.2M log lines from a 200-node Hadoop
cluster, sliced into 575,061 sessions by block id; each block is labelled normal or anomaly (16,838
anomalies) by the original authors' handcrafted rules. Public on Zenodo (loghub record 8196385).

Template "hdfs.anomalous_session" (Noul, node machine.operations.logs_incidents): is the log for one
block anomalous? State = the block id and all its log lines in order, compacted: date, time and thread
id dropped, the block's own id written as <blk>, the "dfs." package prefix dropped ("LEVEL component:
message"). Sessions are never cut (a cut could hide the anomaly), so only sessions whose compacted log
fits in 2,500 chars are used: at 1,500 chars no normal session survives except 13-line read-only ones,
and every anomaly left is a 2-4 line stub, so length alone would give the answer. Even at 2,500, a
third of anomalous blocks are 2-7 line stubs (blocks allocated and never written) while no normal block
has fewer than 13 lines; short anomalies are capped at a third of the anomalous sample. Truth = the
dataset label. 40% anomalous. meta has the line count.

fetch() downloads HDFS_v1.zip (187 MB) and, in one streaming pass over HDFS.log, extracts the lines of a
fixed candidate set of blocks (the first 8,000 anomalous and 16,000 normal blocks in salted-hash order)
into sessions.jsonl; normalize() samples from that file.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "hdfs_sessions"
URL = "https://zenodo.org/api/records/8196385/files/HDFS_v1.zip/content"
TARGET = env_int("TARGET_HDFS_SESSIONS", 1500)
ANOMALY_SHARE = 0.40
MAX_CHARS = 2500
SHORT_LINES, SHORT_SHARE = 8, 1 / 3  # anomalous stubs under 8 lines: at most a third of anomalies
CAND_ANOMALY, CAND_NORMAL = 8000, 16000
LICENSE = "Loghub license (free for research or academic work, with attribution)"
TEXT = "Is the HDFS log `log` for block `block_id` (written <blk> in the log) anomalous?"
CRITERIA = {
    "true": "Something went wrong with this block: an error, an exception, or a missing or out-of-place step in its write, replication or deletion",
    "false": "The block went through a normal life cycle with nothing wrong",
}
BLK = re.compile(r"blk_-?\d+")


def fetch(raw_dir: Path) -> None:
    zpath, out = raw_dir / "HDFS_v1.zip", raw_dir / "sessions.jsonl"
    if out.exists():
        return
    if not zpath.exists():
        with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            with open(zpath, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    with zipfile.ZipFile(zpath) as z:
        labels = dict(csv.reader(io.TextIOWrapper(z.open("preprocessed/anomaly_label.csv"), encoding="utf-8")))
        labels.pop("BlockId", None)
        anom = hash_order([b for b, l in labels.items() if l == "Anomaly"], str, "hdfs.cand")[:CAND_ANOMALY]
        norm = hash_order([b for b, l in labels.items() if l == "Normal"], str, "hdfs.cand")[:CAND_NORMAL]
        want = set(anom) | set(norm)
        lines: dict[str, list[str]] = defaultdict(list)
        with z.open("HDFS.log") as fh:
            for raw in io.TextIOWrapper(fh, encoding="utf-8", errors="replace"):
                hits = set(BLK.findall(raw)) & want
                if not hits:
                    continue
                parts = raw.rstrip("\n").split(" ", 3)  # date, time, pid, "LEVEL component: message"
                line = f"{parts[1]} {parts[3]}" if len(parts) == 4 else raw.strip()
                for b in hits:
                    lines[b].append(line)
    with open(out, "w", encoding="utf-8") as fh:
        for b in sorted(want):
            fh.write(json.dumps({"block": b, "label": labels[b], "lines": lines.get(b, [])}) + "\n")


def normalize(raw_dir: Path) -> Iterator[Question]:
    pools: dict[bool, list] = {True: [], False: []}
    for line in open(raw_dir / "sessions.jsonl", encoding="utf-8"):
        d = json.loads(line)
        b = d["block"]
        log = "\n".join(x.split(" ", 1)[1].replace(b, "<blk>").replace(" dfs.", " ") for x in d["lines"])
        if d["lines"] and len(log) <= MAX_CHARS:
            pools[d["label"] == "Anomaly"].append((b, log, len(d["lines"])))
    n_anom = round(TARGET * ANOMALY_SHARE)
    n_short = round(n_anom * SHORT_SHARE)
    short = hash_order([x for x in pools[True] if x[2] < SHORT_LINES], lambda x: x[0], "hdfs.anomaly")[:n_short]
    long_ = hash_order([x for x in pools[True] if x[2] >= SHORT_LINES], lambda x: x[0], "hdfs.anomaly")
    anom = short + long_[: n_anom - len(short)]
    norm = hash_order(pools[False], lambda x: x[0], "hdfs.normal")[: TARGET - len(anom)]
    for (block, log, n), is_anom in sorted([(x, True) for x in anom] + [(x, False) for x in norm]):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"block_id": block, "log": log},
            shape="detect",
            node_hint="machine.operations.logs_incidents",
            template_id="hdfs.anomalous_session",
            source_item_id=block,
            license=LICENSE,
            truth=is_anom,
            meta={"label_raw": "Anomaly" if is_anom else "Normal", "n_lines": n},
        )
