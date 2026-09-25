"""Afrobarometer Round 9 (2021-2023, 39 countries): non-political items about the respondent as Choice questions
with weighted per-country answer shares.

Source: the merged Round 9 SPSS file, a direct public download from afrobarometer.org/data/merged-data/ (no
registration, login, or terms click-through). Question wording is authored from the R9 merged codebook (downloaded
alongside, not parsed at runtime); answer categories come from the file's value labels.

Each question is one R9 item in the self frame. Human data: one HumanDist per country (weighted by the within-country
household weight `withinwt_hh`; Refused / Don't know / Missing / Not applicable dropped and shares renormalized), plus
the pooled 39-country sample weighted by `Combinwt_new_hh`. Items: own living conditions, lived poverty, feeling
unsafe, news-media and phone/internet use, interpersonal trust, neighbour tolerance, family norms, and gender-norm /
physical-discipline items (flagged "sensitive"). Political items (elections, parties, government performance,
democracy, corruption, foreign influence, identity politics) are not taken.
"""

from __future__ import annotations

import re
import struct
from array import array
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np

from askjev.model import HumanDist, Question

NAME = "afrobarometer"
URL = ("https://www.afrobarometer.org/wp-content/uploads/2025/06/"
       "R9.Merge_39ctry.20Nov23.final_.release_Updated.4Jun25-3.sav")
CODEBOOK = "https://www.afrobarometer.org/wp-content/uploads/2025/07/AB_R9.MergeCodebook_25Jun24.final_.pdf"
R8_URL = ("https://www.afrobarometer.org/wp-content/uploads/2023/03/"
          "afrobarometer_release-dataset_merge-34ctry_r8_en_2023-03-01.sav")
R8_CODEBOOK = "https://www.afrobarometer.org/wp-content/uploads/2025/07/R8_Merge-Codebook_28May24.final_.pdf"
SAV = "R9.Merge_39ctry.sav"
ROUNDS = {9: (SAV, "Afrobarometer Round 9 merged data (39 countries, 2021-2023)", "R9 2021-2023", "39"),
          8: ("R8.Merge_34ctry.sav", "Afrobarometer Round 8 merged data (34 countries, 2019-2021)", "R8 2019-2021", "34")}
LICENSE = "Afrobarometer data, free for non-commercial use with citation (afrobarometer.org)"
MIN_N = 300
DROP = re.compile(r"^(missing|refused|don.?t know|not applicable|not asked)", re.I)

HW = "self.mind.happiness_wellbeing"
MONEY = "self.lifestyle.money_habits"
HOME = "self.lifestyle.home_living"
SCREENS = "self.lifestyle.screens_media"
TRUST = "self.personality.big_five.agreeableness.trust_modesty_temper"
NEIGH = "self.love.workplace_community.neighbors_roommates"
FAM = "self.love.family_parenting.family_rules_of_thumb"
FAMS = "self.love.family_parenting.family_situations"
CARE = "self.values.moral_foundations.care"
EQUAL = "self.values.moral_foundations.equality"
SENS = ["sensitive"]

# (round, var) -> (text, kind, node, flags, label overrides {code: label}, key overrides {label: key})
ITEMS: dict[tuple[int, str], tuple] = {}
ROUND = 9  # items are taken from their latest round: R9, then R8-only items below


def add(var, text, kind, node, flags=None, labels=None, keys=None):
    ITEMS[(ROUND, var)] = (text, kind, node, flags or [], labels or {}, keys or {})


def statements(text1: str, text2: str) -> str:
    return f'Which statement is closest to your view? Statement 1: "{text1}" Statement 2: "{text2}"'


AB_LABELS = {1: "Agree very strongly with statement 1", 2: "Agree with statement 1", 3: "Agree with statement 2",
             4: "Agree very strongly with statement 2", 5: "Agree with neither statement"}
AB_KEYS = {"Agree very strongly with statement 1": "strongly_statement_1", "Agree with statement 1": "statement_1",
           "Agree with statement 2": "statement_2", "Agree very strongly with statement 2": "strongly_statement_2",
           "Agree with neither statement": "neither"}


add("Q4B", "In general, how would you describe your own present living conditions?", "personality", HW)
WITHOUT = "Over the past year, how often, if ever, have you or anyone in your family gone without {}?"
for v, what in {"Q6A": "enough food to eat", "Q6B": "enough clean water for home use",
                "Q6C": "medicines or medical treatment", "Q6D": "enough fuel to cook your food",
                "Q6E": "a cash income"}.items():
    add(v, WITHOUT.format(what), "personality", MONEY)
add("Q7A", "Over the past year, how often, if ever, have you or anyone in your family felt unsafe walking in your "
    "neighbourhood?", "personality", HOME)
add("Q7B", "Over the past year, how often, if ever, have you or anyone in your family feared crime in your own home?",
    "personality", HOME)
NEWS = "How often do you get news from {}?"
for v, what in {"Q74A": "the radio", "Q74B": "television", "Q74C": "newspapers", "Q74D": "the internet",
                "Q74E": "social media such as Facebook, Twitter, WhatsApp, or others"}.items():
    add(v, NEWS.format(what), "taste", SCREENS)
add("Q90H", "How often do you use a mobile phone?", "taste", SCREENS)
add("Q90I", "How often do you use the Internet?", "taste", SCREENS)
TRUSTQ = "How much do you trust {}?"
for v, what in {"Q86A": "other people from your own country", "Q86B": "your relatives", "Q86C": "your neighbours",
                "Q86D": "other people you know", "Q86E": "people from other religions",
                "Q86F": "people from other ethnic groups"}.items():
    add(v, TRUSTQ.format(what), "social", TRUST)
NB = ("Would you like having {} as neighbours, dislike it, or not care?")
add("Q87A", NB.format("people of a different religion"), "social", NEIGH, SENS)
add("Q87B", NB.format("people from other ethnic groups"), "social", NEIGH, SENS)
add("Q88A", "Would you like having a family member marry a person from a different ethnic group, dislike it, or not "
    "care?", "values", FAMS, SENS)
add("Q85B", "In your family, do the children belong more to the mother's side, more to the father's side, or to both "
    "sides equally?", "social", FAMS, labels={0: "Neither side", 1: "Mother's side", 2: "Father's side"},
    keys={"Mother's side": "mothers_side", "Father's side": "fathers_side"})
JUST = "Do you think it can always be justified, sometimes be justified, or never be justified {}?"
add("Q52A", JUST.format("for parents to use physical force to discipline their children"), "values", CARE, SENS)
add("Q52B", JUST.format("for a man to use physical discipline on his wife if she has done something he doesn't like "
                        "or thinks is wrong"), "values", CARE, SENS)
AGREE = 'Do you agree or disagree with this statement: "{}"'
add("Q21A", AGREE.format("When jobs are scarce, men should have more rights to a job than women."), "values", EQUAL,
    SENS)
add("Q21B", AGREE.format("Women should have the same rights as men to own and inherit land."), "values", EQUAL, SENS)
add("Q54", statements("Domestic violence is a private matter that needs to be handled and resolved within the family.",
                      "Domestic violence is a criminal matter whose full resolution requires the involvement of law "
                      "enforcement agencies."), "values", CARE, SENS, labels=AB_LABELS, keys=AB_KEYS)

ROUND = 8  # not asked in Round 9
add("Q83", "Generally speaking, would you say that most people can be trusted or that you must be very careful in "
    "dealing with people?", "social", "self.mind.big_questions.meaning_human_nature")
add("Q23", statements("In order for our country to do well, we should listen more to the wisdom of our elders.",
                      "In order for our country to do well, we should listen more to fresh ideas from young people."),
    "values", "self.values.moral_foundations.authority", labels=AB_LABELS, keys=AB_KEYS)
add("Q68", statements("Communities are stronger when they are made up of people from different ethnic groups, races, "
                      "or religions.",
                      "Communities are stronger when they are made up of people who are similar to each other, that "
                      "is, people from the same ethnic group, race, or religion."),
    "values", "self.values.moral_foundations.loyalty", SENS, labels=AB_LABELS, keys=AB_KEYS)
add("Q82C", "Do you feel comfortable speaking your mother tongue in public?", "social", "self.personality.self_concept")
add("Q82D", "Do you feel comfortable wearing your traditional or cultural dress in public?", "social",
    "self.personality.self_concept")
add("Q54A", "In the past two years, have you ever personally feared violence among people in your neighbourhood or "
    "village? If so, have you actually experienced it?", "personality", HOME,
    labels={0: "No, never", 1: "Yes, feared but did not experience it", 2: "Yes, feared and experienced it"},
    keys={"No, never": "never_feared", "Yes, feared but did not experience it": "feared_not_experienced",
          "Yes, feared and experienced it": "feared_and_experienced"})

# --- SPSS .sav reader (numpy; no pyreadstat/pandas) ---------------------------------------------------------------
def read_sav(path: Path, want: set[str] | None = None):
    """Read an SPSS system file (uncompressed or bytecode-compressed).

    Returns (columns, value_labels, var_labels): numeric columns for the variables in `want` (all numeric variables
    when None) as float64 arrays (system-missing = NaN), value labels {var: {code: label}}, and variable labels.
    Decompression is vectorized: one short Python loop finds the control blocks, numpy gathers the cells."""
    mm = np.memmap(path, dtype=np.uint8, mode="r")
    head = bytes(mm[:176])
    if head[:4] != b"$FL2":
        raise ValueError(f"{path.name}: not an uncompressed/bytecode SPSS file ({head[:4]!r})")
    _layout, _ncase_size, compression, _weight, ncases = struct.unpack("<5i", head[64:84])
    bias = struct.unpack("<d", head[84:92])[0]
    p = 176
    slots: list[tuple[str, int, str | None]] = []  # (short name, type, label) per 8-byte slot
    vl_pending: list[dict[float, bytes]] = []
    vlabels_by_slot: dict[int, dict[float, bytes]] = {}
    long_names: dict[str, str] = {}
    encoding = "utf-8"

    def i32(n=1):
        nonlocal p
        v = struct.unpack(f"<{n}i", bytes(mm[p:p + 4 * n]))
        p += 4 * n
        return v if n > 1 else v[0]

    while True:
        rt = i32()
        if rt == 2:
            typ, has_label, n_miss, _pr, _wr = i32(5)
            name = bytes(mm[p:p + 8]).decode("latin-1").strip()
            p += 8
            label = None
            if has_label:
                ln = i32()
                label = bytes(mm[p:p + ln])
                p += (ln + 3) // 4 * 4
            p += abs(n_miss) * 8
            slots.append((name, typ, label))
        elif rt == 3:
            cnt = i32()
            labs = {}
            for _ in range(cnt):
                val = struct.unpack("<d", bytes(mm[p:p + 8]))[0]
                ln = int(mm[p + 8])
                labs[val] = bytes(mm[p + 9:p + 9 + ln])
                p += (9 + ln + 7) // 8 * 8
            assert i32() == 4
            nv = i32()
            for idx in i32(nv) if nv > 1 else (i32(),):
                vlabels_by_slot[idx - 1] = labs
        elif rt == 6:
            p += i32() * 80
        elif rt == 7:
            sub, size, count = i32(3)
            body = bytes(mm[p:p + size * count])
            p += size * count
            if sub == 13:
                for kv in body.decode("utf-8", "replace").split("\t"):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        long_names[k] = v
            elif sub == 20:
                encoding = body.decode("ascii", "replace").strip() or encoding
        elif rt == 999:
            i32()
            break
        else:
            raise ValueError(f"{path.name}: unknown record type {rt} at {p}")
    enc = "utf-8" if encoding.upper().replace("-", "") == "UTF8" else encoding
    dec = lambda b: b.decode(enc, "replace").strip() if b is not None else None  # noqa: E731
    nslot = len(slots)
    cols_by_slot = {}
    var_labels, value_labels = {}, {}
    for s, (name, typ, label) in enumerate(slots):
        if typ == -1:
            continue
        full = long_names.get(name, name)
        var_labels[full] = dec(label)
        if s in vlabels_by_slot:
            value_labels[full] = {v: dec(t) for v, t in vlabels_by_slot[s].items()}
        if typ == 0 and (want is None or full in want):
            cols_by_slot[s] = full
    data = mm[p:]
    want_slots = np.array(sorted(cols_by_slot), dtype=np.int64)
    out = {cols_by_slot[s]: np.full(ncases, np.nan) for s in want_slots}
    if not len(want_slots):  # dictionary only
        return out, value_labels, var_labels
    if compression == 0:
        rec = np.ndarray((ncases, nslot), dtype="<f8", buffer=data[: ncases * nslot * 8])
        for s in want_slots:
            col = rec[:, s].astype(float)
            col[col <= -1.7976931348623157e308] = np.nan
            out[cols_by_slot[s]] = col
        return out, value_labels, var_labels
    if compression != 1:
        raise ValueError(f"{path.name}: unsupported compression {compression}")
    nw = len(data) // 8
    words = data[: nw * 8].reshape(nw, 8)
    # Count the 253 (raw value follows) codes each word would hold if it were a control block.
    cnt = np.empty(nw, dtype=np.uint8)
    step = 1 << 24
    for a in range(0, nw, step):
        cnt[a:a + step] = (words[a:a + step] == 253).sum(1)
    eof = None
    c = cnt.tobytes()
    blocks = array("Q")
    k = 0
    append = blocks.append
    while k < nw:
        append(k)
        k += 1 + c[k]
    blocks = np.frombuffer(blocks, dtype=np.uint64).astype(np.int64)
    # Trim at the end-of-data code (252), if any.
    want_mask = np.zeros(nslot, dtype=bool)
    want_mask[want_slots] = True
    names = [cols_by_slot.get(s) for s in range(nslot)]
    cell0 = 0
    total = ncases * nslot if ncases >= 0 else None
    bstep = 1 << 22
    for a in range(0, len(blocks), bstep):
        b = blocks[a:a + bstep]
        codes = np.asarray(words[b])  # (m, 8)
        if eof is None:
            hit = np.nonzero(codes == 252)
            if len(hit[0]):
                r0, c0 = hit[0][0], hit[1][0]
                codes = codes[: r0 + 1].copy()
                codes[r0, c0:] = 0
                b = b[: r0 + 1]
                eof = True
        is253 = codes == 253
        raw_idx = b[:, None] + np.cumsum(is253, axis=1)  # word index of the raw value for 253 codes
        flat = codes.ravel()
        nz = flat != 0
        cells = np.cumsum(nz) - 1 + cell0
        cell0 = int(cells[-1]) + 1 if len(cells) else cell0
        sel = nz & want_mask[cells % nslot]
        if total is not None:
            sel &= cells < total
        cc = flat[sel]
        cl = cells[sel]
        vals = cc.astype(np.float64) - bias
        vals[cc >= 254] = np.nan
        m253 = cc == 253
        if m253.any():
            ri = raw_idx.ravel()[sel][m253]
            vals[m253] = np.asarray(words[ri]).view("<f8").ravel()
        rows, slot = np.divmod(cl, nslot)
        for s in np.unique(slot):
            m = slot == s
            out[names[s]][rows[m]] = vals[m]
        if eof:
            break
    for col in out.values():
        col[col <= -1.7976931348623157e308] = np.nan
    return out, value_labels, var_labels


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for url, name in ((URL, SAV), (CODEBOOK, "R9_codebook.pdf"), (R8_URL, ROUNDS[8][0]),
                      (R8_CODEBOOK, "R8_codebook.pdf")):
        out = raw_dir / name
        if out.exists():
            continue
        with httpx.stream("GET", url, follow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            with open(out, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)


def _key(label: str, overrides: dict) -> str:
    if label in overrides:
        return overrides[label]
    s = label.lower().replace("’", "").replace("'", "")
    return "_".join(re.sub(r"[^a-z0-9]+", "_", s).strip("_").split("_")[:6])


def _shares(col, w, mask, codes):
    m = mask & np.isin(col, codes)
    n = int(m.sum())
    if n < MIN_N:
        return None, n
    tot = w[m].sum()
    return [float(w[m & (col == c)].sum() / tot) for c in codes], n


def normalize(raw_dir: Path) -> Iterator[Question]:
    for rnd, (sav, source, wave, nctry) in ROUNDS.items():
        items = {v: it for (r, v), it in ITEMS.items() if r == rnd}
        want = set(items) | {"COUNTRY", "withinwt_hh", "withinwt_ea", "Combinwt_new_hh"}
        cols, vlabels, _ = read_sav(raw_dir / sav, want)
        country = cols["COUNTRY"]
        w_in = np.nan_to_num(cols["withinwt_hh"], nan=0.0)
        w_in = np.where(w_in > 0, w_in, np.nan_to_num(cols["withinwt_ea"], nan=0.0))
        w_all = np.nan_to_num(cols["Combinwt_new_hh"], nan=0.0)
        names = vlabels["COUNTRY"]
        ctry = sorted({c for c in np.unique(country) if np.isfinite(c)}, key=lambda c: names[c])
        for var, (text, kind, node, flags, lab_over, key_over) in items.items():
            labs = {c: l for c, l in vlabels[var].items() if not DROP.match(l)}
            labs.update(lab_over)
            codes = sorted(labs)
            texts = [labs[c].replace("’", "'") for c in codes]
            low = [t.lower() for t in texts]
            if sorted(low) == ["no", "yes"]:
                prim, options = "noul", None
                keys = ["true" if t == "yes" else "false" for t in low]
            else:
                prim = "choice"
                keys = [_key(t, key_over) for t in texts]
                assert len(set(keys)) == len(keys), (var, keys)
                options = {k: (t if _key(t, {}) != k or len(t.split()) > 6 else None) for k, t in zip(keys, texts)}
            col = cols[var]
            human = []
            sh, n = _shares(col, w_all, w_all > 0, codes)
            if sh:
                human.append(HumanDist(population=f"Africa ({nctry} countries, pooled)",
                                       distribution={k: round(x, 4) for k, x in zip(keys, sh)}, n=n,
                                       source=source + ", weighted by Combinwt_new_hh", wave=wave))
            for c in ctry:
                sh, n = _shares(col, w_in, country == c, codes)
                if sh:
                    human.append(HumanDist(population=names[c], distribution={k: round(x, 4) for k, x in zip(keys, sh)},
                                           n=n, source=source + ", weighted by withinwt_hh", wave=wave))
            meta = {"ab_var": var, "round": rnd}
            if flags:
                meta["flags"] = flags
            yield Question(
                text=text,
                primitive=prim,
                hemisphere="self",
                kind=kind,
                origin="dataset",
                source=NAME,
                options=options,
                node_hint=node,
                source_item_id=f"R{rnd}.{var}",
                license=LICENSE,
                human=human,
                meta=meta,
            )
