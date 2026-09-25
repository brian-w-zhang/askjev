"""GlobalOpinionQA (Anthropic/llm_global_opinions): Pew GAS + WVS items with per-country shares."""

from __future__ import annotations

import ast
import csv
import random
import re
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "globalopinionqa"
URL = "https://huggingface.co/datasets/Anthropic/llm_global_opinions/resolve/main/data/global_opinions.csv"
LICENSE = "CC BY-NC-SA 4.0"
POLITICAL_CAP = 170
SEED = 20260924
HUMAN_TEXT = "What would most people answer to this survey question?"

MISSING = re.compile(r"^(no answer|missing|other missing|inap|not asked|total\b|refused$)", re.I)
DK = re.compile(r"^(dk|don.?t know|dk/refused|don.?t know/refused|hard to say)\b", re.I)
NUMERIC = re.compile(r"^\d+(\.\d+)?$")
BAD_OPTION = re.compile(r"^statement #\d", re.I)
POLITICAL = re.compile(
    r"(\belect\w*|\bvot(e|es|ed|ing|ers?)\b|\bpart(y|ies)\b|government|\bpresident|prime minister|chancellor|"
    r"\bleaders?\b|democra\w*|immigra\w*|refugee|asylum|military|\bwars?\b|troops|\barmy\b|\bnato\b|"
    r"united nations|\bthe UN\b|european union|\bEU\b|terror\w*|abortion|homosexual\w*|\bgays?\b|lesbian|"
    r"same-sex|transgender|opposite sex|death penalty|politic\w*|parliament|congress|sanction|nuclear|islam\w*|"
    r"muslim|\bjews?\b|jewish|christians?\b|israel\w*|palestin\w*|putin|obama|trump|bush|merkel|modi|mubarak|"
    r"xi jinping|castro|fidel|chavez|maduro|iran|taliban|\bisis\b|al qaeda|drone|protest\w*|capitalis\w*|communis\w*|socialis\w*|"
    r"free market|market economy|trade union|international trade|tariff|\bborders?\b|entry into our country|minorit\w*|\brac(e|es|ial)\b|ethnic\w*|"
    r"crimea|ukrain\w*|syria\w*|iraq\w*|afghan\w*|brexit|superpower|\ballies\b|\bally\b|enemy|censor\w*|"
    r"\bguns?\b|opinion of|world affairs|foreign (aid|policy)|\bpartner of|"
    r"unification|independen\w*|constitution|referendum|\bveil\b|sharia|\barabs?\b|religious leaders|"
    r"the press|\bthe state\b|state.controlled|dictator\w*|human rights|welfare state|biden|annan|"
    r"in power|\bprogram\b|influence in the world|\bu\.s\.|united states|americans?\b|china|"
    r"chinese|russia\w*|german\w*|japan\w*|india\b|pakistan\w*|europe\w*|groups of people in your country)",
    re.I,
)
SENSITIVE = re.compile(r"\b(sex|sexual\w*|menstruat\w*|suicide)\b", re.I)
VALUES = re.compile(
    r"(moral\w*|justif\w*|\bshould\b|\bduty\b|acceptable|\bright\b|\bwrong\b|qualities that children|"
    r"important in (your )?life|agree|believe in)",
    re.I,
)
TOPICS = [
    (r"(health|disease|flu|hospital|doctor|medic\w*|hiv|aids)", "world.health"),
    (r"(god|heaven|hell|religio\w*|pray\w*|church|mosque|spirit\w*)", "world.society.world_religions"),
    (r"(school|educat\w*|universit\w*|teacher)", "world.society.education"),
    (r"(news|newspaper|television|radio|internet|social media)", "world.society.media_news"),
    (r"(crime|violence|violent|police|safety|security|stolen|robber\w*)", "world.society.crime_law"),
    (r"(robot|computer|technolog\w*|smartphone|cell phone|mobile phone|landline)", "world.tech"),
    (r"(climate change|global warming|droughts?|floods?|weather)", "world.nature.weather_climate"),
    (r"(pollution|environment\w*|air|water|earthquake|tsunami|hurricane)", "world.nature.ecosystems_conservation"),
    (r"(job|employment|work|econom\w*|income|poor|rich|wealth|price|money|bank|business|compan\w*|standard of living)", "world.money.economics"),
    (r"(science|scientif\w*)", "world.science"),
    (r"(sport|olympic|world cup)", "world.sports"),
]


def fetch(raw_dir: Path) -> None:
    out = raw_dir / "global_opinions.csv"
    if out.exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=300)
    r.raise_for_status()
    out.write_bytes(r.content)


def _question_text(q: str | None) -> str | None:
    q = (q or "").strip()
    if not q:
        return None
    if re.search(r"_{3,}", q):
        m = re.search(r"\s[a-z]\.\s*\.?(.+)$", q)
        if not m:
            return None
        item = m.group(1).strip().rstrip(".?")
        q = re.sub(r"_{3,}", item, q[: m.start()]).strip()
    q = re.sub(r"\s+", " ", q).strip()
    if re.match(r"^do you think this is\b", q, re.I) or re.search(r"\b[a-z]\.$", q):
        return None
    return q


def _option_text(o: str) -> str:
    o = re.sub(r"\((vol|do not read|volunteered)\.?\)", "", o, flags=re.I)
    o = re.sub(r"\(survey country\)", "this country", o, flags=re.I)
    return re.sub(r"\s+", " ", o).strip()


STOP = {"a", "an", "at", "the", "of", "to", "in", "for", "and", "or", "but", "with", "on", "is", "are", "be"}


def _slug(text: str, words: int) -> str:
    toks = re.findall(r"[a-z0-9]+", text.lower().replace("’", "'").replace("'", ""))
    if len(toks) > 5:
        toks = toks[:words]
        while len(toks) > 1 and toks[-1] in STOP:
            toks.pop()
    return "_".join(toks) or "option"


def _keys(opts: list[str]) -> list[str]:
    """Short readable keys: 'dont_know' for DK, else the shortest distinct word-prefix slug (max 5 words)."""
    for words in (4, 5, 6):
        keys = ["dont_know" if DK.match(o) else _slug(o, words) for o in opts]
        if len(set(keys)) == len(keys):
            return keys
    return [f"{k}_{i}" for i, k in enumerate(keys)]


def _population(country: str, taken: set[str]) -> str:
    c = re.sub(r"\s*\((current|old|new)[^)]*\)", "", country, flags=re.I).strip()
    return country.strip() if c in taken else c


def _node(text: str) -> str:
    for pat, node in TOPICS:
        if re.search(r"\b" + pat + r"\b", text, re.I):
            return node
    return "world.society"


def _parse(raw_dir: Path) -> list[tuple[bool, Question]]:
    out = []
    with open(raw_dir / "global_opinions.csv", newline="", encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh)):
            text = _question_text(r["question"])
            if not text:
                continue
            opts = [str(o) for o in ast.literal_eval(r["options"])]
            sel = ast.literal_eval(r["selections"].removeprefix("defaultdict(<class 'list'>, ").removesuffix(")"))
            if any(len(v) != len(opts) for v in sel.values()):
                continue
            idx = [j for j, o in enumerate(opts) if not MISSING.match(o.strip())]
            if len(idx) < 2 or any(NUMERIC.match(opts[j].strip()) or BAD_OPTION.match(opts[j].strip()) for j in idx):
                continue
            # Garbled rows merge several questions: countries answer disjoint option sets.
            supports = [frozenset(j for j in idx if v[j] > 0 and not DK.match(opts[j])) for v in sel.values()]
            supports = [s for s in supports if s]
            if any(not (a & b) for a in supports for b in supports):
                continue
            used = [j for j in idx if any(v[j] > 0 for v in sel.values())]
            if len(used) < 2:
                continue
            if any(re.match(r"^\d", opts[j].strip()) for j in used):
                continue
            # Some rows repeat an option text (e.g. two "Don't know" codes): merge them.
            texts: list[str] = []
            slot = {}
            for j in used:
                t = _option_text(opts[j])
                norm = "dont_know" if DK.match(t) else t.lower()
                if norm not in [("dont_know" if DK.match(x) else x.lower()) for x in texts]:
                    texts.append(t)
                slot[j] = next(n for n, x in enumerate(texts) if ("dont_know" if DK.match(x) else x.lower()) == norm)
            if len(texts) < 2:
                continue
            keys = _keys(texts)
            options = {k: t for k, t in zip(keys, texts)}
            human, taken = [], set()
            for country, v in sel.items():
                tot = sum(v[j] for j in used)
                if tot <= 0:
                    continue
                pop = _population(country, taken)
                taken.add(pop)
                dist = dict.fromkeys(keys, 0.0)
                for j in used:
                    dist[keys[slot[j]]] += v[j] / tot
                human.append(HumanDist(population=pop, distribution=dist,
                                       source=f"{r['source']} via Anthropic/llm_global_opinions"))
            if not human:
                continue
            blob = text + " " + " ".join(texts)
            political = bool(POLITICAL.search(blob))
            flags = (["political"] if political else []) + (["sensitive"] if SENSITIVE.search(blob) else [])
            meta = {"source_survey": r["source"]}
            if flags:
                meta["flags"] = flags
            out.append((political, Question(
                text=text,
                primitive="choice",
                hemisphere="world",
                kind="values" if VALUES.search(text) else "social",
                origin="dataset",
                source=NAME,
                options=options,
                node_hint=_node(text),
                human_text=HUMAN_TEXT,
                source_item_id=f"row{i}",
                license=LICENSE,
                human=human,
                meta=meta,
            )))
    return out


def _base(parsed: list[tuple[bool, Question]]) -> list[Question]:
    seen = set()
    nonpol, pol = [], []
    for political, q in parsed:
        if q.id in seen:
            continue
        seen.add(q.id)
        (pol if political else nonpol).append(q)
    rng = random.Random(SEED)
    pol = rng.sample(pol, min(POLITICAL_CAP, len(pol)))
    return sorted(nonpol + pol, key=lambda q: int(q.source_item_id[3:]))


# ---------------------------------------------------------------------------------------------------------------------
# Expansion (wave 6): the non-political rows the original parser rejected. Unset ASKJEV_TARGET_GLOBALOPINIONQA keeps
# the original 815 rows byte-identical; a larger target appends up to (target - 815) of these in salted-hash order.
# They are mostly 0-10 / 1-10 rating scales (Choice over the scale points, endpoint keys carry their label, as the
# GSS adapter does), rows whose option list merges several Pew questions (repaired by keeping the options quoted in
# the question and the countries that answered only those), and one age-bracket item. Items about the respondent's
# own life, priorities, and values are hemisphere self. Still non-political only (same POLITICAL regex).
EXTRA_SALT = "globalopinionqa-extra-v1"
NOT_SUBSTANTIVE = re.compile(r"^(no answer|missing|other missing|inap|not asked|not applicable|total\b|refused$)", re.I)
VOL = re.compile(r"\((vol|do not read|volunteered)\.?\)", re.I)
SENSITIVE_EXTRA = re.compile(r"\b(sex|sexual\w*|suicide|euthanasia|prostitution|beat\w*)\b", re.I)
POLITICAL_EXTRA = re.compile(r"incomes should be made more equal", re.I)  # WVS left-right economic item
LADDER = {0: "worst possible life", 10: "best possible life"}
SKIP_TEXTS = {"I refuse things that bad for me"}  # ungrammatical source wording

JUST = "Please tell me for each of the following statements whether you think it can always be justified"
AGREE10 = "Now, I would like to read some statements and ask how much you agree or disagree"
VIEWS10 = "Now I'd like you to tell me your views on various issues"

# (pattern on the rewritten text, hemisphere, kind, node); first match wins, else world/social/_node().
PLACES = [
    (r"ladder", "self", "personality", "self.mind.happiness_wellbeing"),
    (r"to you personally", "self", "values", "self.values.life_values.personal_priorities"),
    (r"financial situation of your household", "self", "personality", "self.lifestyle.money_habits"),
    (r"satisfied are you with .*(neighborhood|schools where you live)", "self", "personality",
     "self.lifestyle.home_living"),
    (r"getting ahead in life", "world", "evaluative", "world.money.careers"),
    (r"justifi.*\"(suicide|euthanasia)\"", "self", "values", "self.mind.time_mortality.death_legacy"),
    (r"justifi.*\"(sex before|having casual sex|prostitution|divorce)", "self", "values",
     "self.values.moral_foundations.purity"),
    (r"justifi.*\"(for a man to beat|parents beating|violence against)", "self", "values",
     "self.values.moral_foundations.care"),
    (r"justifi", "self", "values", "self.values.honesty_trust"),
    (r"moral rules", "self", "values", "self.mind.epistemics.knowledge_certainty"),
    (r"incomes should be made more equal", "self", "values", "self.values.moral_foundations.equality"),
    (r"competition is good", "self", "values", "self.values.moral_foundations.proportionality"),
    (r"hard work", "self", "values", "self.mind.luck_fate.luck_and_fate"),
    (r"(science|technology)", "world", "evaluative", "world.science"),
    (r"(corruption|bribe)", "world", "evaluative", "world.society.crime_law"),
    (r"(stop myself|refuse things|bad habits)", "self", "personality",
     "self.personality.big_five.neuroticism.impulses_coping"),
    (r"consider a person old", "self", "social", "self.mind.time_mortality.aging_lifespan"),
    (r"air pollution", "self", "values", "self.values.animals_environment"),
    (r"religions", "world", "social", "world.society.world_religions"),
    (r"world cup", "world", "evaluative", "world.sports"),
    (r"global economy", "world", "evaluative", "world.money.economics"),
]


def _is_num(o: str) -> bool:
    return bool(NUMERIC.match(o.strip()))


def _clean_extra_text(q: str) -> str | None:
    """Rewrite the WVS/GAS battery stems into one standalone question; None if the item is not recoverable."""
    q = q.replace("\r", "")
    if "\n\n" in q:
        head, item = [x.strip() for x in q.split("\n\n", 1)]
        item = re.sub(r"\s+", " ", item).rstrip(".")
        if head.startswith(JUST):
            return (f'Do you think this can always be justified, never be justified, or something in between: "{item}"? '
                    "(1 means never justifiable, 10 means always justifiable)")
        if head.startswith(AGREE10):
            return (f'On a scale from 1 (completely disagree) to 10 (completely agree), how much do you agree or disagree '
                    f'with this statement: "{item}"?')
        if head.startswith(VIEWS10):
            return VIEWS10  # filled in from the endpoint labels once the scale is parsed
        q = head
    q = re.sub(r"\s+", " ", q).strip()
    # GAS batteries: "... very important….To own a cell phone?" / "how important is it...to know the right people"
    m = re.search(r"(…\.?|\.{3})\s*(.+)$", q)
    if m:
        stem, item = q[: m.start()].rstrip(" ?"), m.group(2).strip()
        if item[:1].isupper():
            q = f"{stem}: {item[0].lower()}{item[1:]}"
        else:
            q = f"{stem} {item}"
        if not q.endswith("?"):
            q = q.rstrip(".,") + "?"
    q = re.sub(r"^\((.+?)\)\s*", r"\1 ", q)
    return q


def _scale_values(opts: list[str], idx: list[int]) -> dict[int, int] | None:
    """Option index -> scale value for a numeric rating scale whose endpoints may be labels."""
    vals: dict[int, int] = {}
    for j in idx:
        if _is_num(opts[j]):
            vals[j] = int(float(opts[j]))
    labels = [j for j in idx if j not in vals]
    if not vals or len(labels) > 2:
        return None
    lo, hi = min(vals.values()), max(vals.values())
    free = [v for v in (lo - 1, hi + 1) if v not in vals.values()]
    pending = []
    for j in labels:
        near = {vals[k] for k in (j - 1, j + 1) if k in vals}
        cand = [v for v in free if (v + 1 in near or v - 1 in near)]
        if len(cand) == 1:
            vals[j] = cand[0]
            free.remove(cand[0])
        else:
            pending.append(j)
    for j in pending:
        if len(free) != 1 and not (len(free) == 2 and len(pending) == 1):
            return None
        vals[j] = free.pop(0) if len(free) == 1 else None
        if vals[j] is None:
            return None
    got = sorted(vals.values())
    if got != list(range(got[0], got[-1] + 1)) or not (2 <= len(got) <= 11):
        return None
    return vals


def _extra_row(i: int, r: dict) -> Question | None:
    opts = [str(o) for o in ast.literal_eval(r["options"])]
    sel = ast.literal_eval(r["selections"].removeprefix("defaultdict(<class 'list'>, ").removesuffix(")"))
    if not sel or any(len(v) != len(opts) for v in sel.values()):
        return None
    raw_q = (r["question"] or "").strip()
    # Single-country national WVS modules (South Korea) have machine-translated stems and truncated scales.
    if set(sel) == {"South Korea"} or raw_q in SKIP_TEXTS:
        return None
    if not raw_q or re.search(r"_{3,}", raw_q) or re.match(r"^do you think this is\b", raw_q, re.I):
        return None
    if POLITICAL.search(raw_q + " " + " ".join(opts)):
        return None
    idx = [j for j, o in enumerate(opts) if not NOT_SUBSTANTIVE.match(o.strip())]
    dk = [j for j in idx if DK.match(opts[j].strip())]
    sub = [j for j in idx if j not in dk]
    text = _clean_extra_text(raw_q)
    if not text:
        return None
    countries = dict(sel)
    order: list[int]
    labels: dict[int, str]
    descs: dict[int, str | None] = {}
    if any(_is_num(opts[j]) for j in sub) or re.search(r"^\d+$", "".join(opts[j].strip() for j in sub[1:2])):
        vals = _scale_values(opts, sub)
        if vals is None:
            return None
        order = sorted(sub, key=lambda j: vals[j])
        labels = {}
        for j in order:
            v = vals[j]
            if _is_num(opts[j]) or re.fullmatch(r"\d+", opts[j].strip()):
                lab = LADDER.get(v) if "ladder" in text.lower() and v in LADDER else None
            else:
                lab = re.sub(r"^\d+\s+", "", _option_text(opts[j]))
            labels[j] = f"{v}_{_slug(lab, 5)}" if lab else str(v)
            descs[j] = lab[0].upper() + lab[1:] if lab and len(_slug(lab, 5).split("_")) < len(lab.split()) else None
    elif re.match(r"^\d", opts[sub[0]].strip()):  # age brackets ("18 to 49", "90+")
        order = sub
        labels = {j: _slug(_option_text(opts[j]).replace("+", " plus"), 5) for j in sub}
    else:
        # Garbled Pew rows: keep the options quoted in the question, plus volunteered/DK codes; keep the countries
        # whose answers fall only on those.
        norm_q = re.sub(r"[^a-z ]+", " ", raw_q.lower().replace("(survey country)", "your country"))
        norm_q = re.sub(r"\s+", " ", norm_q)

        def quoted(o: str) -> bool:
            o = re.sub(r"(,?\s*\[?or\]?)$", "", o.lower().replace("(survey country)", "your country")).strip()
            o = re.sub(r"\s+", " ", re.sub(r"[^a-z ]+", " ", o)).strip()
            return bool(o) and o[:40] in norm_q

        main = [j for j in sub if not VOL.search(opts[j]) and quoted(opts[j])]
        if len(main) < 2:
            return None
        keep_c = {c: v for c, v in sel.items() if sum(v[j] for j in main) > 0}
        side = [j for j in sub if VOL.search(opts[j]) and any(v[j] > 0 for v in keep_c.values())]
        allowed = set(main + side + dk)
        if any(v[j] > 0 for v in keep_c.values() for j in range(len(opts)) if j not in allowed and j in idx):
            return None
        countries = keep_c
        # Merge volunteered codes that differ only in case; drop ones nobody chose.
        merged: dict[str, int] = {}
        for j in side:
            t = VOL.sub("", opts[j]).strip().lower()
            if max(v[j] for v in keep_c.values()) < 0.005:
                continue
            merged.setdefault(t, j)
        side = [j for j in side if j in merged.values()]
        order = main + side
        texts = [_option_text(opts[j]).removesuffix(", OR").rstrip(".").strip() for j in order]
        texts = [re.sub(r"^this country", "Your country", t) for t in texts]
        keys = _keys(texts)
        labels = {j: k for j, k in zip(order, keys)}
        descs = {j: t for j, t in zip(order, texts)}
    if text == VIEWS10:
        lo, hi = labels[order[0]], labels[order[-1]]
        if not (descs.get(order[0]) or "_" in lo) or not (descs.get(order[-1]) or "_" in hi):
            return None
        lo_t = descs.get(order[0]) or re.sub(r"^\d+\s*", "", _option_text(opts[order[0]]))
        hi_t = descs.get(order[-1]) or re.sub(r"^\d+\s*", "", _option_text(opts[order[-1]]))
        text = (f'Where would you place your view on a scale from 1 to 10, where 1 means you agree completely with '
                f'"{lo_t.rstrip(".")}" and 10 means you agree completely with "{hi_t.rstrip(".")}"?')
    elif not text.endswith("?"):
        if [labels[j] for j in (order[0], order[-1])] == ["1_not_at_all", "4_very_much"]:
            text = f'How well does this statement describe you, from 1 (not at all) to 4 (very much): "{text}"?'
        else:
            return None
    order = order + dk[:1]
    if dk:
        labels[dk[0]] = "dont_know"
        descs[dk[0]] = None
    keys = [labels[j] for j in order]
    if len(set(keys)) != len(keys) or len(keys) < 2:
        return None
    slot = {j: labels[j] for j in order}
    for j in dk[1:]:
        slot[j] = "dont_know"
    human, taken = [], set()
    for country, v in countries.items():
        tot = sum(v[j] for j in slot)
        if tot <= 0:
            continue
        pop = _population(country, taken)
        taken.add(pop)
        dist = dict.fromkeys(keys, 0.0)
        for j, k in slot.items():
            dist[k] += v[j] / tot
        human.append(HumanDist(population=pop, distribution=dist,
                               source=f"{r['source']} via Anthropic/llm_global_opinions"))
    if not human:
        return None
    options = {labels[j]: descs.get(j) for j in order}
    hemi, kind, node = next(((h, k, n) for pat, h, k, n in PLACES if re.search(pat, text, re.I)),
                            ("world", "values" if VALUES.search(text) else "social", _node(text)))
    blob = text + " " + " ".join(opts[j] for j in order)
    flags = (["political"] if POLITICAL_EXTRA.search(blob) else []) + \
        (["sensitive"] if SENSITIVE_EXTRA.search(blob) else [])
    meta = {"source_survey": r["source"], "expansion": "wave6"}
    if flags:
        meta["flags"] = flags
    return Question(
        text=text,
        primitive="choice",
        hemisphere=hemi,
        kind=kind,
        origin="dataset",
        source=NAME,
        options=options,
        node_hint=node,
        human_text=HUMAN_TEXT,
        source_item_id=f"row{i}",
        license=LICENSE,
        human=human,
        meta=meta,
    )


def _extras(raw_dir: Path, parsed_ids: set[str], taken_ids: set[str]) -> list[Question]:
    out = []
    with open(raw_dir / "global_opinions.csv", newline="", encoding="utf-8") as fh:
        for i, r in enumerate(csv.DictReader(fh)):
            if f"row{i}" in parsed_ids:
                continue
            q = _extra_row(i, r)
            if q is not None and q.id not in taken_ids:
                taken_ids.add(q.id)
                out.append(q)
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    parsed = _parse(raw_dir)
    base = _base(parsed)
    yield from base
    k = env_int("TARGET_GLOBALOPINIONQA", len(base)) - len(base)
    if k <= 0:
        return
    extras = _extras(raw_dir, {q.source_item_id for _, q in parsed}, {q.id for _, q in parsed})
    yield from hash_order(extras, lambda q: q.source_item_id, EXTRA_SALT)[:k]
