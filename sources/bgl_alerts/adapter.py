"""Loghub BGL (Oliner & Stearley, DSN 2007; Zhu et al., ISSRE 2023): 4.75M RAS log lines from the Blue
Gene/L supercomputer at Lawrence Livermore; system administrators tagged 348,460 lines as alerts, with an
alert category (KERNDTLB, APPSEV, KERNMNTF...). Public on Zenodo (loghub record 8196385).

Template "bgl.alert" (Noul, node machine.operations.logs_incidents): is the log line an alert? State =
the raw line without the label column (timestamps, node, type, component, severity, message). Truth =
the admins' tag. 40% alerts.
The log repeats a few messages millions of times, so lines are grouped by a masked template (component,
severity and message with digits and hex runs masked) and at most 3 lines per template are kept (10 for alert templates, which are few: ~80 masked alert
templates against thousands of non-alert ones).
Alerts: round-robin over alert categories, then templates. Non-alerts: half are drawn from lines with
severity WARNING or worse (ERROR, SEVERE, FATAL, FAILURE), which the admins did not tag, so severity
alone doesn't give the answer; the other half from any non-alert line.
fetch() downloads BGL.zip (57 MB) and, in one streaming pass, keeps up to 3 (alerts: 10) lines per masked
template (those with the smallest line hash) in candidates.jsonl.
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "bgl_alerts"
URL = "https://zenodo.org/api/records/8196385/files/BGL.zip/content"
TARGET = env_int("TARGET_BGL_ALERTS", 1500)
ALERT_SHARE = 0.40
PER_TEMPLATE = {True: 10, False: 3}  # alert lines come from few templates, so keep more of each
LICENSE = "Loghub license (free for research or academic work, with attribution)"
TEXT = "Is the Blue Gene/L log line `log_line` an alert that needs an administrator's attention?"
CRITERIA = {
    "true": "The line reports a failure an administrator must act on (hardware, kernel, file system, network or application failure)",
    "false": "The line is routine or informational, or an error that needs no action",
}
MASK = re.compile(r"0x[0-9a-fA-F]+|\b[0-9a-fA-F]{6,}\b|\d+")
SEVERE = {"WARNING", "ERROR", "SEVERE", "FATAL", "FAILURE"}


def fetch(raw_dir: Path) -> None:
    zpath, out = raw_dir / "BGL.zip", raw_dir / "candidates.jsonl"
    if out.exists():
        return
    if not zpath.exists():
        with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            with open(zpath, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    keep: dict[tuple[str, str], list[tuple[str, int, str]]] = defaultdict(list)
    with zipfile.ZipFile(zpath) as z, z.open("BGL.log") as fh:
        for i, raw in enumerate(fh):
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            parts = line.split(" ", 9)
            if len(parts) < 10:
                continue
            label, comp, level, msg = parts[0], parts[7], parts[8], " ".join(parts[9].split())
            key = (label, f"{comp} {level} {MASK.sub('#', msg)}")
            h = hashlib.sha256(f"bgl|{i}".encode()).hexdigest()
            lst = keep[key]
            cap = PER_TEMPLATE[label != "-"]
            if len(lst) < cap:
                lst.append((h, i, line))
                lst.sort()
            elif h < lst[-1][0]:
                lst[-1] = (h, i, line)
                lst.sort()
    with open(out, "w", encoding="utf-8") as fh:
        for (label, tpl), lst in sorted(keep.items()):
            for _, i, line in lst:
                fh.write(json.dumps({"line_no": i + 1, "label": label, "template": tpl, "line": line}) + "\n")


def _round_robin(groups: dict[str, list], k: int) -> list:
    out, i = [], 0
    while len(out) < k and any(i < len(v) for v in groups.values()):
        for g in sorted(groups):
            if i < len(groups[g]) and len(out) < k:
                out.append(groups[g][i])
        i += 1
    return out


def _spread(items: list[dict], salt: str) -> list[dict]:
    """Salted-hash order that takes one line per template before any second line."""
    by_t: dict[str, list] = defaultdict(list)
    for it in hash_order(items, lambda x: x["line_no"], salt):
        by_t[it["template"]].append(it)
    tpls = hash_order(list(by_t), str, salt)
    out, r = [], 0
    while any(r < len(by_t[t]) for t in tpls):
        out += [by_t[t][r] for t in tpls if r < len(by_t[t])]
        r += 1
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = [json.loads(l) for l in open(raw_dir / "candidates.jsonl", encoding="utf-8")]
    for r in rows:
        parts = r["line"].split(" ", 9)
        r["level"] = parts[8]
        r["shown"] = " ".join(" ".join(parts[1:]).split())
    rows = [r for r in rows if len(r["shown"]) <= 1000]
    n_alert = round(TARGET * ALERT_SHARE)
    by_cat: dict[str, list] = defaultdict(list)
    for r in rows:
        if r["label"] != "-":
            by_cat[r["label"]].append(r)
    alerts = _round_robin({c: _spread(v, f"bgl.alert|{c}") for c, v in by_cat.items()}, n_alert)
    normal = [r for r in rows if r["label"] == "-"]
    n_norm = TARGET - len(alerts)
    severe = _spread([r for r in normal if r["level"] in SEVERE], "bgl.normal.severe")[: n_norm // 2]
    taken = {r["line_no"] for r in severe}
    rest = _spread([r for r in normal if r["line_no"] not in taken], "bgl.normal.any")[: n_norm - len(severe)]
    for r in sorted(alerts + severe + rest, key=lambda r: r["line_no"]):
        yield Question(
            text=TEXT,
            primitive="noul",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=CRITERIA,
            state={"log_line": r["shown"]},
            shape="detect",
            node_hint="machine.operations.logs_incidents",
            template_id="bgl.alert",
            source_item_id=f"line:{r['line_no']}",
            license=LICENSE,
            truth=r["label"] != "-",
            meta={"label_raw": r["label"], "severity": r["level"]},
        )
