"""OECD PISA student questionnaires (2022 and 2018): general self-description items as Choice questions with
weighted answer shares of 15-year-old students.

Source: the PISA 2022 and PISA 2018 student questionnaire SPSS files, public no-login downloads from
webfs.oecd.org (linked from oecd.org's PISA database pages). Item wording is the file's variable label (the English
source version), rewritten into one standalone self-frame question.

Items: the 2022 social-emotional scales (persistence, impulse control, curiosity, cooperation, empathy, trust,
perspective taking, assertiveness, stress resistance, emotional control), creativity and openness items, growth
mindset, and overall life satisfaction; from 2018, fear of failure, competitiveness, work mastery, resilience,
meaning in life, reading enjoyment, and how often the student feels each emotion. Items about school, classes,
classmates, teachers, homework, or exams are skipped (no rewording into a general statement unless the item already
is one).

Human data: "15-year-old students, OECD average" = the unweighted mean over OECD countries of each country's
weighted (W_FSTUWT) shares, the PISA convention for OECD averages; n = valid answers in those countries. Plus a few
large countries (United States, Japan, Germany, Brazil, Indonesia, Mexico) as extra populations when they have at
least MIN_N answers. Non-substantive codes (valid skip, not applicable, invalid, no response) are dropped.
"""

from __future__ import annotations

import importlib.util
import re
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np

from askjev.model import HumanDist, Question

NAME = "pisa_questionnaire"
LICENSE = "OECD PISA data, free to use with attribution (OECD Terms and Conditions)"
FILES = {
    2022: ("https://webfs.oecd.org/pisa2022/STU_QQQ_SPSS.zip", "STU_QQQ_SPSS.zip", "CY08MSP_STU_QQQ.SAV", "CNTRYID"),
    2018: ("https://webfs.oecd.org/pisa2018/SPSS_STU_QQQ.zip", "SPSS_STU_QQQ_2018.zip", "CY07_MSU_STU_QQQ.sav",
           "CNTRYID"),
}
COUNTRIES = ["United States", "Japan", "Germany", "Brazil", "Indonesia", "Mexico"]
MIN_N = 300
MISSING = re.compile(r"^(valid skip|not applicable|invalid|no response|missing)", re.I)
SCHOOL = re.compile(r"\b(school|class|classes|classmates?|teachers?|students?|homework|exams?|tests?|lessons?|"
                    r"mathematics|subject|\[)", re.I)

C = "self.personality.big_five.conscientiousness"
N = "self.personality.big_five.neuroticism"
A = "self.personality.big_five.agreeableness"
E = "self.personality.big_five.extraversion"
O = "self.personality.big_five.openness"
EMP = "self.personality.emotions_stress.empathy_social_reading"
# variable prefix -> (year, node, kind, scale name)
SCALES = {
    "ST307": (2022, f"{C}.drive_self_discipline", "personality", "persistence"),
    "ST309": (2022, f"{C}.order_caution", "personality", "impulse control"),
    "ST301": (2022, f"{O}.ideas_imagination", "personality", "curiosity"),
    "ST343": (2022, f"{A}.kindness_cooperation", "personality", "cooperation"),
    "ST311": (2022, EMP, "personality", "empathy"),
    "ST315": (2022, f"{A}.trust_modesty_temper", "personality", "trust"),
    "ST303": (2022, EMP, "personality", "perspective taking"),
    "ST305": (2022, f"{E}.sociability_energy", "personality", "assertiveness"),
    "ST345": (2022, f"{N}.fear_worry", "personality", "stress resistance"),
    "ST313": (2022, f"{N}.temper_moodiness", "personality", "emotional control"),
    "ST340": (2022, f"{O}.ideas_imagination", "personality", "creative self-efficacy and problem solving"),
    "ST341": (2022, O, "personality", "artistic openness"),
    "ST342": (2022, f"{O}.ideas_imagination", "personality", "imagination and adventurousness"),
    "ST263": (2022, "self.mind.big_questions.meaning_human_nature", "social", "growth mindset"),
    "ST183": (2018, f"{N}.self_consciousness", "personality", "fear of failure"),
    "ST181": (2018, "self.personality.motivation_ambition", "personality", "competitiveness"),
    "ST182": (2018, "self.personality.motivation_ambition", "personality", "work mastery"),
    "ST188": (2018, "self.personality.emotions_stress.coping_expressing", "personality", "resilience"),
    "ST185": (2018, "self.mind.big_questions.meaning_human_nature", "personality", "meaning in life"),
    "ST160": (2018, "self.lifestyle.leisure_hobbies", "taste", "reading enjoyment"),
    "ST186": (2018, "self.personality.emotions_stress.recent_stress_mood", "personality", "subjective well-being"),
}
LIFE_SAT = {
    "ST016Q01NA": (2022, "Overall, how satisfied are you with your life as a whole these days? Answer on a scale from 0 "
                   "(not at all satisfied) to 10 (completely satisfied).", "self.mind.happiness_wellbeing"),
}
SAT_ENDS = {0: "not at all satisfied", 10: "completely satisfied"}


def _sav_module():
    path = Path(__file__).resolve().parents[1] / "afrobarometer" / "adapter.py"
    spec = importlib.util.spec_from_file_location("sources.afrobarometer", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for url, zname, sav, _ in FILES.values():
        if (raw_dir / sav).exists():
            continue
        z = raw_dir / zname
        if not z.exists():
            with httpx.stream("GET", url, follow_redirects=True, timeout=1800) as r:
                r.raise_for_status()
                with open(z, "wb") as fh:
                    for chunk in r.iter_bytes(1 << 22):
                        fh.write(chunk)
        with zipfile.ZipFile(z) as zf:
            member = next(m for m in zf.namelist() if m.lower().endswith(".sav"))
            with zf.open(member) as src, open(raw_dir / sav, "wb") as dst:
                while chunk := src.read(1 << 22):
                    dst.write(chunk)


def _slug(s: str) -> str:
    s = s.lower().replace("’", "").replace("'", "")
    return "_".join(re.sub(r"[^a-z0-9]+", "_", s).strip("_").split("_")[:6])


def _statement(label: str) -> tuple[str, str] | None:
    """(stem kind, statement) from a PISA variable label, or None if not a general self-description."""
    label = re.sub(r"\s+", " ", label).strip().replace("\u2019", "'")
    m = re.match(r"^(Agree/disagree|Agree|Disagree/agree)\s*:\s*(.+)$", label, re.I)
    m2 = re.match(r"^How much do you agree or disagree\?\s*(.+)$", label, re.I)
    m3 = re.match(r"^.*how often do you feel as described below\?\s*(.+)$", label, re.I)
    if m:
        kind, stmt = "agree", m.group(2).strip()
    elif m2:
        kind, stmt = "agree", m2.group(1).strip()
    elif m3:
        kind, stmt = "often", m3.group(1).strip()
    else:
        return None
    if SCHOOL.search(stmt) or len(stmt) < 4:
        return None
    stmt = stmt[0].upper() + stmt[1:]
    if kind == "agree" and not stmt.endswith((".", "!", "?")):
        stmt += "."
    return kind, stmt


def _dists(col, cntry, oecd, w, codes, names):
    """OECD-average shares (mean of country shares) and per-country shares for the chosen large countries."""
    valid = np.isin(col, codes)
    out = []
    shares, n_oecd = [], 0
    per = {}
    for c in np.unique(cntry[valid]):
        m = valid & (cntry == c)
        n = int(m.sum())
        if n < MIN_N:
            continue
        tot = w[m].sum()
        sh = np.array([w[m & (col == k)].sum() / tot for k in codes])
        if np.nanmax(oecd[m]) == 1:
            shares.append(sh)
            n_oecd += n
        per[names.get(c, str(c))] = (sh, n)
    if len(shares) >= 5:
        out.append(("15-year-old students, OECD average", np.mean(shares, axis=0), n_oecd, len(shares)))
    for name in COUNTRIES:
        if name in per:
            out.append((f"15-year-old students, {name}", per[name][0], per[name][1], 1))
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    sav = _sav_module()
    for year, (_, _, fname, cvar) in sorted(FILES.items(), reverse=True):
        prefixes = {p for p, s in SCALES.items() if s[0] == year}
        life = {v: s for v, s in LIFE_SAT.items() if s[0] == year}
        _, _, labels = sav.read_sav(raw_dir / fname, set())
        items = [v for v in labels if v[:5] in prefixes and re.match(r"^ST\d{3}Q\d{2}", v)] + list(life)
        cols, vlabels, labels = sav.read_sav(raw_dir / fname, set(items) | {cvar, "OECD", "W_FSTUWT"})
        cntry, oecd = cols[cvar], np.nan_to_num(cols["OECD"], nan=0)
        w = np.nan_to_num(cols["W_FSTUWT"], nan=0.0)
        names = vlabels[cvar]
        wave = f"PISA {year}"
        source = f"OECD PISA {year} student questionnaire, weighted by W_FSTUWT"
        for var in items:
            if var not in cols:
                continue
            vl = {c: l for c, l in vlabels.get(var, {}).items() if not MISSING.match(l)}
            if var in life:
                _, text, node = life[var]
                codes = list(range(0, 11))
                keys = [f"{c}_{_slug(SAT_ENDS[c])}" if c in SAT_ENDS else str(c) for c in codes]
                options = dict.fromkeys(keys)
                kind, scale, stmt = "personality", "life satisfaction", None
            else:
                st = _statement(labels[var] or "")
                if st is None or len(vl) < 2:
                    continue
                how, stmt = st
                _, node, kind, scale = SCALES[var[:5]]
                codes = sorted(vl)
                texts = [vl[c] for c in codes]
                keys = [_slug(t) for t in texts]
                if len(set(keys)) != len(keys):
                    continue
                options = {k: (t if len(t.split()) > 6 else None) for k, t in zip(keys, texts)}
                if how == "agree":
                    text = f'How much do you agree or disagree with this statement: "{stmt}"'
                else:
                    text = ("Thinking about yourself and how you normally feel, how often do you feel "
                            f"{stmt.rstrip('.').lower()}?")
            human = []
            for pop, sh, n, k in _dists(cols[var], cntry, oecd, w, codes, names):
                src = source + (f"; mean of {k} OECD country shares" if k > 1 else "")
                human.append(HumanDist(population=pop, distribution={kk: round(float(s), 4) for kk, s in zip(keys, sh)},
                                       n=n, source=src, wave=wave))
            if not human:
                continue
            yield Question(
                text=text,
                primitive="choice",
                hemisphere="self",
                kind=kind,
                origin="dataset",
                source=NAME,
                options=options,
                node_hint=node,
                human_text=None,
                source_item_id=f"PISA{year}.{var}",
                license=LICENSE,
                human=human,
                meta={"pisa_var": var, "pisa_year": year, "scale": scale, "label": labels[var]},
            )
