"""Loghub (Zhu et al., ISSRE 2023; github.com/logpai/loghub): 2,000-line samples of real system logs from
16 systems, each line parsed into header fields (component, level...) and a message with an event
template id (from the Loghub parsing benchmark).

Templates (node machine.operations.logs_incidents):
- "loghub.system" (Choice, 16 systems): which system wrote `log_line`? State = the raw line (header
  included, cut to 500 chars). Truth = the file it came from.
- "loghub.component" (Choice, per-system options): which component of `system` wrote the message
  `log_message`? State = the system name and the message only (the header, which names the component, is
  removed). Truth = the parsed Component field. Five systems whose components are named modules:
  Android, HealthApp, HDFS, OpenStack (Nova), Spark; each keeps its components with 5+ distinct messages.
Both: lines deduplicated by message; at most CAP_EVENT lines per event template (the samples repeat a
few templates hundreds of times); round-robin over systems (and, within one, over event templates).
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "loghub_lines"
BASE = "https://raw.githubusercontent.com/logpai/loghub/master/{s}/{s}_2k.{ext}"
TARGET_SYSTEM = env_int("TARGET_LOGHUB_SYSTEM", 2000)
TARGET_COMPONENT = env_int("TARGET_LOGHUB_COMPONENT", 1500)
CAP_EVENT_SYSTEM = 25
CAP_EVENT_COMPONENT = 10
MIN_COMPONENT = 5
LICENSE = "Loghub license (free for research or academic work, with attribution)"
SYSTEM_TEXT = "Which system wrote the log line `log_line`?"
COMPONENT_TEXT = "Which component of `system` wrote the log message `log_message`?"

SYSTEMS = {  # dataset folder -> (key, description)
    "Android": ("android", "Android phone system log"),
    "Apache": ("apache", "Apache HTTP server error log"),
    "BGL": ("blue_gene_l", "Blue Gene/L supercomputer"),
    "HDFS": ("hdfs", "Hadoop Distributed File System"),
    "HPC": ("hpc_cluster", "High-performance computing cluster"),
    "Hadoop": ("hadoop_mapreduce", "Hadoop MapReduce job"),
    "HealthApp": ("health_app", "Mobile health and step-counting app"),
    "Linux": ("linux", "Linux server system log"),
    "Mac": ("macos", "macOS system log"),
    "OpenSSH": ("openssh", "OpenSSH server"),
    "OpenStack": ("openstack", "OpenStack cloud"),
    "Proxifier": ("proxifier", "Proxifier proxy client"),
    "Spark": ("spark", "Apache Spark"),
    "Thunderbird": ("thunderbird", "Thunderbird supercomputer"),
    "Windows": ("windows", "Windows event log"),
    "Zookeeper": ("zookeeper", "Apache ZooKeeper"),
}
SYSTEM_OPTIONS = {k: d for k, d in SYSTEMS.values()}
COMPONENT_SYSTEMS = {
    "Android": "Android phone",
    "HealthApp": "a mobile health and step-counting app",
    "HDFS": "the Hadoop Distributed File System",
    "OpenStack": "OpenStack Nova",
    "Spark": "Apache Spark",
}


def fetch(raw_dir: Path) -> None:
    for s in SYSTEMS:
        for ext in ("log", "log_structured.csv"):
            out = raw_dir / f"{s}_2k.{ext}"
            if out.exists():
                continue
            r = httpx.get(BASE.format(s=s, ext=ext), follow_redirects=True, timeout=120)
            r.raise_for_status()
            out.write_bytes(r.content)


def _slug(name: str) -> str:
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z][a-z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name)  # CamelCase -> Camel_Case
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _cut(t: str, n: int = 500) -> str:
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + " ..."


def _load(raw_dir: Path, s: str) -> list[dict]:
    raw = (raw_dir / f"{s}_2k.log").read_text(encoding="utf-8", errors="replace").splitlines()
    rows = list(csv.DictReader(open(raw_dir / f"{s}_2k.log_structured.csv", newline="", encoding="utf-8")))
    assert len(raw) == len(rows), (s, len(raw), len(rows))
    out, seen = [], set()
    for line, r in zip(raw, rows):
        msg = " ".join(r["Content"].split())
        if not msg or msg in seen:
            continue
        seen.add(msg)
        out.append({"id": f"{s}:{r['LineId']}", "line": " ".join(line.split()), "msg": msg,
                    "event": r["EventId"], "component": (r.get("Component") or "").strip()})
    return out


def _spread(items: list[dict], cap: int, salt: str) -> list[dict]:
    """Round-robin over event templates (salted-hash order), at most `cap` lines per template."""
    by_ev: dict[str, list] = defaultdict(list)
    for it in items:
        by_ev[it["event"]].append(it)
    lists = [hash_order(v, lambda x: x["id"], f"{salt}|{e}")[:cap] for e, v in sorted(by_ev.items())]
    out, i = [], 0
    while any(i < len(v) for v in lists):
        out += [v[i] for v in lists if i < len(v)]
        i += 1
    return out


def _round_robin(pools: dict[str, list], k: int) -> list:
    out, i = [], 0
    while len(out) < k and any(i < len(v) for v in pools.values()):
        for key in sorted(pools):
            if i < len(pools[key]) and len(out) < k:
                out.append((key, pools[key][i]))
        i += 1
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    data = {s: _load(raw_dir, s) for s in SYSTEMS}

    sys_pools = {s: _spread(items, CAP_EVENT_SYSTEM, f"loghub.system|{s}") for s, items in data.items()}
    for s, it in sorted(_round_robin(sys_pools, TARGET_SYSTEM), key=lambda x: x[1]["id"]):
        yield Question(
            text=SYSTEM_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=SYSTEM_OPTIONS,
            state={"log_line": _cut(it["line"])},
            shape="classify",
            node_hint="machine.operations.logs_incidents",
            template_id="loghub.system",
            source_item_id=it["id"],
            license=LICENSE,
            truth=SYSTEMS[s][0],
            meta={"event_id": it["event"]},
        )

    comp_pools, comp_options = {}, {}
    for s in COMPONENT_SYSTEMS:
        spread = _spread(data[s], CAP_EVENT_COMPONENT, f"loghub.component|{s}")
        counts: dict[str, int] = defaultdict(int)
        for it in spread:
            counts[it["component"]] += 1
        keep = {c for c, n in counts.items() if n >= MIN_COMPONENT and c}
        comp_options[s] = {_slug(c): c for c in sorted(keep)}
        comp_pools[s] = [it for it in spread if it["component"] in keep]
    for s, it in sorted(_round_robin(comp_pools, TARGET_COMPONENT), key=lambda x: x[1]["id"]):
        yield Question(
            text=COMPONENT_TEXT,
            primitive="choice",
            hemisphere="machine",
            origin="dataset",
            source=NAME,
            options=comp_options[s],
            state={"system": COMPONENT_SYSTEMS[s], "log_message": _cut(it["msg"])},
            shape="classify",
            node_hint="machine.operations.logs_incidents",
            template_id="loghub.component",
            source_item_id=it["id"],
            license=LICENSE,
            truth=_slug(it["component"]),
            meta={"system": s, "component_raw": it["component"], "event_id": it["event"]},
        )
