"""Moral Machine (Awad et al. 2018, Nature): self-driving-car dilemmas rendered as text, with the share of
respondents choosing each outcome.

The per-outcome file with character counts (SharedResponses.csv, 3.2 GB gzipped, ~70M rows) is too big to keep,
so `fetch` streams it once (curl | tar -xzO, parsed in 64 MB chunks), pairs the two outcome rows of each scenario by
ResponseID, and keeps only aggregates: one row per distinct scenario configuration (stay-side outcome x
swerve-side outcome) with response counts, globally and for a few large countries. Scenarios with the "Criminal"
or "Homeless" characters and the Social Status / Social Value scenario type are dropped while streaming
(docs/03-questions.md §6).
"""

from __future__ import annotations

import io
import subprocess
from pathlib import Path
from typing import Iterator

import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "moral_machine"
URL = "https://osf.io/download/tdqrn/"  # Datasets/Moral Machine Data/SharedResponses.csv.tar.gz (OSF 3hvt2)
STREAM_CMD = f"curl -sfL '{URL}' | tar -xzO"
AGG = "aggregates.parquet"
AGG_C = "aggregates_country.parquet"
LICENSE = "Moral Machine public data (Awad et al. 2018, Nature 563:59-64; OSF 3hvt2); no license set on OSF, research use with citation"
TARGET = env_int("TARGET_MORAL_MACHINE", 3000)
MIN_N = 100
SALT = "moral_machine-20260924"
COUNTRIES = ["USA", "DEU", "FRA", "BRA", "GBR", "CAN", "RUS", "JPN", "ESP", "AUS"]
COUNTRY_NAMES = {"USA": "United States", "DEU": "Germany", "FRA": "France", "BRA": "Brazil", "GBR": "United Kingdom",
                 "CAN": "Canada", "RUS": "Russia", "JPN": "Japan", "ESP": "Spain", "AUS": "Australia"}

# (column, singular, plural), in the order characters are listed. Criminal and Homeless are excluded.
CHARS = [
    ("Stroller", "baby in a stroller", "babies in strollers"),
    ("Pregnant", "pregnant woman", "pregnant women"),
    ("Boy", "boy", "boys"),
    ("Girl", "girl", "girls"),
    ("Man", "man", "men"),
    ("Woman", "woman", "women"),
    ("MaleAthlete", "male athlete", "male athletes"),
    ("FemaleAthlete", "female athlete", "female athletes"),
    ("MaleDoctor", "male doctor", "male doctors"),
    ("FemaleDoctor", "female doctor", "female doctors"),
    ("MaleExecutive", "male executive", "male executives"),
    ("FemaleExecutive", "female executive", "female executives"),
    ("LargeMan", "large man", "large men"),
    ("LargeWoman", "large woman", "large women"),
    ("OldMan", "elderly man", "elderly men"),
    ("OldWoman", "elderly woman", "elderly women"),
    ("Dog", "dog", "dogs"),
    ("Cat", "cat", "cats"),
]
EXCLUDED_CHARS = ["Criminal", "Homeless"]
EXCLUDED_TYPES = ["Social Status", "Social Value", "SocialValue", "SocialStatus"]
NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


# ---------------------------------------------------------------- fetch (streaming aggregate)

def _outcome_expr() -> pl.Expr:
    # "<Barrier><CrossingSignal>:<count per CHARS column>", e.g. "02:0,0,1,0,..." (pedestrians on a red light).
    return pl.concat_str(
        [pl.col("Barrier").cast(pl.Int8).cast(pl.Utf8), pl.col("CrossingSignal").cast(pl.Int8).cast(pl.Utf8), pl.lit(":"),
         pl.concat_str([pl.col(c).cast(pl.Int8).cast(pl.Utf8) for c, _, _ in CHARS], separator=",")]
    )


def fetch(raw_dir: Path) -> None:
    if (raw_dir / AGG).exists() and (raw_dir / AGG_C).exists():
        return
    import shutil

    raw_dir.mkdir(parents=True, exist_ok=True)
    parts = raw_dir / "parts"
    shutil.rmtree(parts, ignore_errors=True)
    parts.mkdir()
    num_cols = ["Intervention", "Barrier", "CrossingSignal", "Saved"] + [c for c, _, _ in CHARS] + EXCLUDED_CHARS
    # Everything read as text, numbers cast leniently: a few rows hold junk like "(nan, nan, nan, nan)".
    schema = {c: pl.Utf8 for c in num_cols + ["ResponseID", "ScenarioType", "ScenarioTypeStrict", "UserCountry3"]}
    proc = subprocess.Popen(STREAM_CMD, shell=True, stdout=subprocess.PIPE)

    def batches(chunk: int = 1 << 26) -> Iterator[pl.DataFrame]:
        header = proc.stdout.readline()
        rest = b""
        while True:
            buf = proc.stdout.read(chunk)
            if not buf:
                break
            buf = rest + buf
            cut = buf.rfind(b"\n") + 1
            buf, rest = buf[:cut], buf[cut:]
            if buf:
                yield pl.read_csv(io.BytesIO(header + buf), columns=list(schema), schema_overrides=schema,
                                  null_values=["", "NA"])
        if rest.strip():
            yield pl.read_csv(io.BytesIO(header + rest + b"\n"), columns=list(schema), schema_overrides=schema,
                              null_values=["", "NA"])

    # Pass 1: the file lists every stay-side outcome (sorted by ResponseID) and then every swerve-side outcome, so
    # the two rows of a scenario are ~35M rows apart. Stream once and keep a compact per-outcome table on disk.
    rows = 0
    for i, df in enumerate(batches()):
        df = df.with_columns([pl.col(c).cast(pl.Float64, strict=False) for c in num_cols])
        rows += df.height
        df.select(
            rid=pl.col("ResponseID").hash(),
            iv=pl.col("Intervention").cast(pl.Int8, strict=False),
            saved=pl.col("Saved").cast(pl.Int8, strict=False),
            country=pl.col("UserCountry3"),
            outcome=_outcome_expr(),
            stype=pl.coalesce(pl.col("ScenarioTypeStrict"), pl.col("ScenarioType")),
            bad=(pl.sum_horizontal([pl.col(c).fill_null(0) for c in EXCLUDED_CHARS]) > 0)
            | pl.col("ScenarioType").is_in(EXCLUDED_TYPES).fill_null(False)
            | pl.col("ScenarioTypeStrict").is_in(EXCLUDED_TYPES).fill_null(False)
            | pl.any_horizontal([pl.col(c).is_null() for c in num_cols]),
        ).write_parquet(parts / f"part_{i:05d}.parquet")
        if i % 10 == 0:
            print(f"moral_machine: {rows:,} rows streamed", flush=True)
    proc.wait()
    if proc.returncode != 0 or rows == 0:
        raise RuntimeError(f"moral_machine: stream failed (exit {proc.returncode}, {rows} rows)")

    # Pass 2: pair stay/swerve rows by ResponseID and aggregate per configuration.
    lf = pl.scan_parquet(parts / "*.parquet")
    stay = lf.filter(pl.col("iv") == 0).unique("rid", keep="none").select(
        "rid", pl.col("outcome").alias("o_stay"), "country", "stype", "bad")
    swerve = lf.filter(pl.col("iv") == 1).unique("rid", keep="none").select(
        "rid", pl.col("outcome").alias("o_swerve"), pl.col("saved").alias("swerve_saved"), pl.col("bad").alias("bad2"))
    sc = (stay.join(swerve, on="rid").filter(~pl.col("bad") & ~pl.col("bad2") & pl.col("swerve_saved").is_not_null())
          .select("o_stay", "o_swerve", "country", "stype", "swerve_saved").collect(engine="streaming"))
    key = ["o_stay", "o_swerve"]
    # Choosing "stay" kills the stay-side characters, i.e. saves the swerve side: stay share = mean(swerve_saved).
    g = sc.group_by(key).agg(n=pl.len(), stay=pl.col("swerve_saved").sum(), stype=pl.col("stype").drop_nulls().mode().first())
    c = (sc.filter(pl.col("country").is_in(COUNTRIES)).group_by(key + ["country"])
         .agg(n=pl.len(), stay=pl.col("swerve_saved").sum()).rename({"country": "UserCountry3"}))
    g.sort(key).write_parquet(raw_dir / AGG)
    c.sort(key + ["UserCountry3"]).write_parquet(raw_dir / AGG_C)
    (raw_dir / "stream_stats.txt").write_text(
        f"rows streamed: {rows}\npaired scenarios kept: {sc.height}\nconfigurations: {g.height}\n"
        f"configurations with n>={MIN_N}: {g.filter(pl.col('n') >= MIN_N).height}\n")
    shutil.rmtree(parts, ignore_errors=True)


# ---------------------------------------------------------------- render

def _people(counts: list[int]) -> tuple[str, int]:
    parts, total = [], 0
    for (_, one, many), k in zip(CHARS, counts):
        if k:
            total += k
            parts.append((f"a {one}" if one[0] not in "aeiou" else f"an {one}") if k == 1 else f"{NUM[k]} {many}")
    if len(parts) == 1:
        return parts[0], total
    return ", ".join(parts[:-1]) + " and " + parts[-1], total


def _side(outcome: str) -> tuple[str, int, bool, int]:
    """(who dies, how many, passengers?, crossing signal)."""
    head, counts = outcome.split(":")
    passengers, signal = head[0] == "1", int(head[1])
    who, total = _people([int(x) for x in counts.split(",")])
    return who, total, passengers, signal


def _where(k: int, passengers: bool, signal: int) -> str:
    if passengers:
        return "the passenger inside the car" if k == 1 else "the passengers inside the car"
    who = "a pedestrian" if k == 1 else "pedestrians"
    return who + {0: " crossing the road", 1: " crossing legally on a green signal",
                  2: " crossing illegally on a red signal"}[signal]


def render(o_stay: str, o_swerve: str) -> tuple[str, dict]:
    ws, ks, ps, ss = _side(o_stay)
    ww, kw, pw, sw = _side(o_swerve)
    if ps:
        stay = f"crash into a concrete barrier ahead and kill {ws}, {_where(ks, True, 0)}"
    else:
        stay = f"hit and kill {ws}, {_where(ks, False, ss)} ahead"
    if pw:
        swerve = f"crash into a concrete barrier in the other lane and kill {ww}, {_where(kw, True, 0)}"
    else:
        swerve = f"hit and kill {ww}, {_where(kw, False, sw)} in the other lane"
    text = (
        "A self-driving car with sudden brake failure cannot stop. "
        f"If it stays on course, it will {stay}. If it swerves, it will {swerve}. "
        "Should the car stay on course or swerve?"
    )
    die = lambda k: "dies" if k == 1 else "die"  # noqa: E731
    options = {"stay": f"Stay on course: {ws} {die(ks)}", "swerve": f"Swerve: {ww} {die(kw)}"}
    return text, options


# ---------------------------------------------------------------- normalize

def normalize(raw_dir: Path) -> Iterator[Question]:
    g = pl.read_parquet(raw_dir / AGG).filter(pl.col("n") >= MIN_N)
    c = pl.read_parquet(raw_dir / AGG_C).filter(pl.col("n") >= MIN_N)
    by_c: dict[tuple[str, str], list[dict]] = {}
    for r in c.iter_rows(named=True):
        by_c.setdefault((r["o_stay"], r["o_swerve"]), []).append(r)
    rows = hash_order(g.iter_rows(named=True), lambda r: f"{r['o_stay']}|{r['o_swerve']}", SALT)[:TARGET]
    for r in rows:
        text, options = render(r["o_stay"], r["o_swerve"])
        share = r["stay"] / r["n"]
        human = [HumanDist(
            population="Moral Machine respondents (global)",
            distribution={"stay": round(share, 4), "swerve": round(1 - share, 4)},
            n=r["n"],
            source="Moral Machine SharedResponses.csv (Awad et al. 2018), share choosing each outcome for this configuration",
        )]
        for cr in sorted(by_c.get((r["o_stay"], r["o_swerve"]), []), key=lambda x: COUNTRIES.index(x["UserCountry3"])):
            s = cr["stay"] / cr["n"]
            human.append(HumanDist(
                population=f"Moral Machine respondents ({COUNTRY_NAMES[cr['UserCountry3']]})",
                distribution={"stay": round(s, 4), "swerve": round(1 - s, 4)},
                n=cr["n"],
                source=f"Moral Machine SharedResponses.csv, UserCountry3={cr['UserCountry3']}",
            ))
        yield Question(
            text=text,
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="template",
            source=NAME,
            options=options,
            node_hint="self.values.sacrificial_dilemmas",
            human_text=text.replace("Should the car stay on course or swerve?",
                                    "Would most people say the car should stay on course or swerve?"),
            source_item_id=f"{r['o_stay']}|{r['o_swerve']}",
            license=LICENSE,
            template_id="moral_machine.av",
            human=human,
            meta={"scenario_type": r["stype"], "encoding": "<Barrier><CrossingSignal>:<counts in CHARS order>"},
        )
