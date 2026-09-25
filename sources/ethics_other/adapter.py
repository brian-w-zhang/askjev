"""ETHICS virtue and deontology subsets (Hendrycks et al. 2021, MIT).

- Virtue: a short scenario plus 2-5 candidate character traits, exactly one of which the person shows.
  Asked as a Choice over the candidate traits; truth = the trait labeled 1.
- Deontology: (a) a request plus an excuse for not doing it, and (b) a role ("I am a ...") plus a claimed
  duty ("So I should ..."). Each is a Noul with truth = the label (1 = reasonable).
"""

from __future__ import annotations

import csv
import importlib.util
import re
import tarfile
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "ethics_other"
URL = "https://people.eecs.berkeley.edu/~hendrycks/ethics.tar"
LICENSE = "MIT (hendrycks/ethics)"
SALT = "ethics_other-20260924"
TARGET_VIRTUE = env_int("TARGET_ETHICS_OTHER_VIRTUE", 3000)
TARGET_EXCUSE = env_int("TARGET_ETHICS_OTHER_EXCUSE", 2000)
TARGET_ROLE = env_int("TARGET_ETHICS_OTHER_ROLE", 1000)
MAX_PER_SCENARIO = 2  # deontology scenarios come with 2-8 excuses/duties; keep at most one true + one false
SPLITS = ("train", "test")
DIR = Path("ethics")

# Content filters shared with scruples / ethics_cs.
_spec = importlib.util.spec_from_file_location(
    "sources.scruples_anecdotes", Path(__file__).parents[1] / "scruples_anecdotes" / "adapter.py"
)
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
F = A.F

# Gendered or body "traits" that read as stereotypes: skip the whole item.
SKIP_TRAITS = {"effeminate", "manly", "masculine", "fat", "thin", "terroristic", "narcoleptic"}

P = "self.personality."
KC = P + "big_five.agreeableness.kindness_cooperation"
TMT = P + "big_five.agreeableness.trust_modesty_temper"
CDR = P + "big_five.conscientiousness.drive_self_discipline"
COR = P + "big_five.conscientiousness.order_caution"
SOC = P + "big_five.extraversion.sociability_energy"
FEAR = P + "big_five.neuroticism.fear_worry"
IMP = P + "big_five.neuroticism.impulses_coping"
SELFC = P + "big_five.neuroticism.self_consciousness"
TEMPER = P + "big_five.neuroticism.temper_moodiness"
IDEAS = P + "big_five.openness.ideas_imagination"
CONV = P + "big_five.openness.convention_politics"
DARK = P + "dark_side"
MOT = P + "motivation_ambition"
RISK = P + "risk_decision_style"
SELF = P + "self_concept"
HUMOR = P + "humor_style.humor_habits_tastes"
EMP = P + "emotions_stress.empathy_social_reading"

_GROUPS = {
    KC: "generous generosity giving share caring kind kindness nice warm good-hearted goodwill benevolent benevolence "
    "humane charitable altruistic selfless helpful helpfulness nurturing affection affectionate hospitable merciful "
    "compassionate forgiving grateful appreciative loyal loyalty faithful selfish selfishness callous coldhearted "
    "ironhearted pitiless merciless mean meanness cruel brutal abusive violent unhelpful unhelpfulness unkindness "
    "stinginess stingy cheap penny-pinching greedy ungrateful unappreciative unforgiving spiteful malice malicious "
    "avenging revenging hateful disloyal traitorous insulting derogatory rude rudeness discourteous abrasive "
    "disrespect disrespectful respect respectful respectul courteous courtesy courtliness civility polite "
    "considerate gracious decent",
    TMT: "trusting trustful distrustful oversuspicious paranoid cynical modest modesty humble humbleness humility "
    "boastful conceit arrogant prideful pompous pretentious patient patience impatience good_temper good-humored "
    "easygoing peaceful pacifist calm calmness balanced measured truthful honest honesty trustworthy dishonest "
    "dishonesty deceptive fibbing dodgy candid forthright direct sincere genuine earnest principled unprincipled "
    "honorable dishonorable showing_integrity unethical just justice fair fairness injustice partiality "
    "disagreeable aggressive fierce tough rough",
    TEMPER: "angry furious wrathful ballistic ill_temper ill-tempered irritable short-tempered easy_to_make_angry "
    "volatile resentful gloomy complaining righteous_indignation emotional",
    CDR: "lazy laziness diligent dedicated committed hard-working productive efficient professional unprofessional "
    "irresponsible responsible reliable unreliable unreliability dependable undependable procrastinating "
    "halfheartedness lax conscientious neglecting incompetent ineffectual skilled",
    COR: "careless carefulness cautious prudent rashness reckless organized disorganized messy sloppy neat tidy "
    "punctual forgetful attentive vigilant alertness observant focused distracted mindful sensible",
    SOC: "friendly friendliness sociable personable amiable outgoing chatty wordy noisy distant impersonal unfriendly "
    "unfriendliness ignoring cheerful energetic active low-energy tired popular lighthearted optimistic",
    FEAR: "coward cowardice cowardly courage courageous possessing_courage brave bold boldness heroic timid timidity "
    "faintheartedness cold_feet scared nervousness anxious worried stoic resilient strong",
    IMP: "gluttonous gluttony self-indulgence self-indulgent over-indulgence lustful licentious hedonistic "
    "extravagant_with_money frugal self-control self-restraint sober obsessed",
    SELFC: "shy meek socially_incompetent shameless brazen apologetic",
    DARK: "narcissistic egocentric domineering ruthless calculating bully",
    MOT: "ambition ambitious unambitious driven competitive complacent apathetic apathy eager inspired satisfied "
    "bored",
    RISK: "adventurous adventuresome decisive",
    IDEAS: "curiosity creative imaginative intelligent smart clever wise well-read rational logical irrational "
    "reasonable realistic tasteful tasteless classy elegance graceful vulgarity boorishness buffoonery crude "
    "open-minded open versatile",
    CONV: "prejudiced biased intolerant patriotic patriotism conservative extremist nonpartisan superstitious "
    "flexible",
    SELF: "independent mature childish immature foolish helpless",
    HUMOR: "wittiness good_humored humorless playful",
    EMP: "empathetic empathy insensitive thoughtful delicate",
}
NODE = {t.replace("_", " "): node for node, words in _GROUPS.items() for t in words.split()}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def fetch(raw_dir: Path) -> None:
    want = [DIR / sub / f"{sub}_{sp}.csv" for sub in ("virtue", "deontology") for sp in SPLITS]
    if all((raw_dir / w).exists() for w in want):
        return
    raw_dir.mkdir(parents=True, exist_ok=True)
    tar = raw_dir.parent / "ethics_cs" / "ethics.tar"  # already downloaded for ethics_cs
    if not tar.exists():
        tar = raw_dir / "ethics.tar"
        if not tar.exists():
            r = httpx.get(URL, follow_redirects=True, timeout=600)
            r.raise_for_status()
            tar.write_bytes(r.content)
    with tarfile.open(tar) as tf:
        members = [m for m in tf.getmembers() if m.name.startswith(("ethics/virtue/", "ethics/deontology/"))]
        tf.extractall(raw_dir, members=members, filter="data")


def _flags(s: str, sexual: bool) -> list[str]:
    flags = ["sensitive"] if (sexual or F.SELF_HARM.search(s) or F.VIOLENT.search(s)) else []
    if A.POLITICAL.search(s):
        flags.append("political")
    return flags


def _virtue(raw_dir: Path) -> Iterator[Question]:
    groups = []  # (split, first_row, scenario, [(trait, label)])
    seen = set()
    for split in SPLITS:
        with open(raw_dir / DIR / "virtue" / f"virtue_{split}.csv", encoding="utf-8", newline="") as fh:
            cur = None
            for i, r in enumerate(csv.DictReader(fh)):
                sc, _, trait = r["scenario"].partition(" [SEP] ")
                sc, trait = clean(sc), clean(trait).lower().rstrip(".:")
                if cur is None or cur[2] != sc:
                    cur = (split, i, sc, [])
                    groups.append(cur)
                cur[3].append((trait, r["label"] == "1"))
    pool = []
    for split, i, sc, cands in groups:
        traits = [t for t, _ in cands]
        right = [t for t, y in cands if y]
        keys = [slug(t) for t in traits]
        if (
            not (3 <= len(cands) <= 5) or len(right) != 1 or len(set(keys)) != len(keys) or not all(keys)
            or SKIP_TRAITS & set(traits) or sc.lower() in seen
        ):
            continue
        sexual = A.is_sexual(sc)
        if A.drop(sc, sexual):
            continue
        seen.add(sc.lower())
        pool.append((split, i, sc, traits, right[0], sexual))
    picked = hash_order(pool, lambda g: f"{g[0]}:{g[1]}", SALT + "|virtue")[:TARGET_VIRTUE]
    picked.sort(key=lambda g: (g[0] != "train", g[1]))
    for split, i, sc, traits, right, sexual in picked:
        flags = _flags(sc, sexual)
        yield Question(
            text="Which character trait does the person in `scenario` show?",
            primitive="choice",
            hemisphere="self",
            kind="personality",
            origin="dataset",
            source=NAME,
            options={slug(t): None for t in sorted(traits)},
            state={"scenario": sc},
            node_hint=NODE.get(right, "self.personality"),
            human_text="Which character trait would most people say the person in `scenario` shows?",
            source_item_id=f"virtue_{split}:{i}",
            license=LICENSE,
            truth=slug(right),
            template_id="ethics_other.virtue",
            meta={"subset": "virtue", "split": split, "trait": right} | ({"flags": flags} if flags else {}),
        )


def _deontology(raw_dir: Path) -> Iterator[Question]:
    pools = {"excuse": [], "role": []}
    seen = set()
    for split in SPLITS:
        with open(raw_dir / DIR / "deontology" / f"deontology_{split}.csv", encoding="utf-8", newline="") as fh:
            for i, r in enumerate(csv.DictReader(fh)):
                sc, ex = clean(r["scenario"]), clean(r["excuse"])
                if not sc or not ex or (sc.lower(), ex.lower()) in seen:
                    continue
                if re.match(r"(?i)i am |i'm ", sc):
                    kind = "role"
                    if not re.match(r"(?i)so i should", ex):
                        continue
                elif sc.endswith("?"):
                    kind = "excuse"
                else:
                    continue
                both = f"{sc} {ex}"
                sexual = A.is_sexual(both)
                if A.drop(both, sexual):
                    continue
                seen.add((sc.lower(), ex.lower()))
                pools[kind].append((split, i, sc, ex, r["label"] == "1", sexual))

    for kind, target in (("excuse", TARGET_EXCUSE), ("role", TARGET_ROLE)):
        # Balanced true/false; at most MAX_PER_SCENARIO rows (one per label) per scenario.
        per: dict[tuple[str, bool], int] = {}
        by_label: dict[bool, list] = {True: [], False: []}
        for row in hash_order(pools[kind], lambda x: f"{x[0]}:{x[1]}", f"{SALT}|{kind}"):
            k = (row[2].lower(), row[4])
            if per.get(k):
                continue
            per[k] = 1
            by_label[row[4]].append(row)
        half = target // 2
        picked = by_label[True][:half] + by_label[False][:half]
        rest = by_label[True][half:] + by_label[False][half:]
        picked += hash_order(rest, lambda x: f"{x[0]}:{x[1]}", f"{SALT}|{kind}|rest")[: target - len(picked)]
        picked.sort(key=lambda x: (x[0] != "train", x[1]))
        for split, i, sc, ex, ok, sexual in picked:
            flags = _flags(f"{sc} {ex}", sexual)
            if kind == "excuse":
                q = dict(
                    text="Is `excuse` a reasonable excuse for not doing what `request` asks?",
                    human_text="Would most people say `excuse` is a reasonable excuse for not doing what `request` asks?",
                    state={"request": sc, "excuse": ex},
                    node_hint="self.values.honesty_trust",
                )
            else:
                q = dict(
                    text="Is `duty` a reasonable duty for the person described in `role`?",
                    human_text="Would most people say `duty` is a reasonable duty for the person described in `role`?",
                    state={"role": sc, "duty": ex},
                    node_hint="self.values",
                )
            yield Question(
                primitive="noul",
                hemisphere="self",
                kind="values",
                origin="dataset",
                source=NAME,
                source_item_id=f"deontology_{split}:{i}",
                license=LICENSE,
                truth=ok,
                template_id=f"ethics_other.{kind}",
                meta={"subset": "deontology", "split": split} | ({"flags": flags} if flags else {}),
                **q,
            )


def normalize(raw_dir: Path) -> Iterator[Question]:
    yield from _virtue(raw_dir)
    yield from _deontology(raw_dir)
