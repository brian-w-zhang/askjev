"""MMLU (Hendrycks et al. 2021) multiple-choice knowledge questions, as World factual Choice with truth.

Also the shared helpers for the other science multiple-choice sources (arc, sciq, openbookqa, strategyqa):
HF parquet fetch, readable answer-text keys, the snap-judgment filters, near-duplicate keys, content flags,
and the keyword node hint (borrowed from the boolq adapter).
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Callable, Iterator

import httpx
import polars as pl

from askjev.config import RAW
from askjev.model import Question
from askjev.sampling import env_int, top_up

NAME = "mmlu"
HF = "https://huggingface.co/api/datasets"
LICENSE = "MIT"
TARGET = env_int("TARGET_MMLU", 12000)
PER_SUBJECT = 600
SALT = "mmlu-20260924"
SPLITS = ("test", "validation", "dev")

_spec = importlib.util.spec_from_file_location("sources.boolq", Path(__file__).parents[1] / "boolq" / "adapter.py")
BOOLQ = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BOOLQ)


# --- shared helpers -----------------------------------------------------------------------------------------
def hf_fetch(raw_dir: Path, dataset: str, files: dict[str, str]) -> None:
    """files: local name -> '<config>/<split>/<n>.parquet' under the HF parquet API. Idempotent."""
    for local, part in files.items():
        out = raw_dir / local
        if out.exists():
            continue
        r = httpx.get(f"{HF}/{dataset}/parquet/{part}", follow_redirects=True, timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)


def load(name: str):
    """Another adapter module (for cross-source dedupe); fetches its raw files if missing."""
    spec = importlib.util.spec_from_file_location(f"sources.{name}", Path(__file__).parents[1] / name / "adapter.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw = RAW / name
    raw.mkdir(parents=True, exist_ok=True)
    mod.fetch(raw)
    return mod, raw


def norm(text: str) -> str:
    """Near-duplicate key: lowercase letters and digits only, articles dropped."""
    toks = re.findall(r"[a-z0-9]+", text.lower().replace("’", "'").replace("'", ""))
    return " ".join(t for t in toks if t not in {"a", "an", "the"})


INSTRUCTION = re.compile(r"^\s*(use the (information|passage|table|data)[^.:]*[.:]|read the [^.:]*[.:])\s*", re.I)


def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text.replace(" ", " ")).strip()


STOP = {"a", "an", "at", "the", "of", "to", "in", "for", "and", "or", "but", "with", "on", "is", "are", "be", "by",
        "as", "from", "that", "its", "it", "their", "this"}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower().replace("’", "'").replace("'", ""))


def _slug(toks: list[str], words: int) -> str:
    if len(toks) > words:
        toks = toks[:words]
        while len(toks) > 1 and toks[-1] in STOP:
            toks.pop()
    return "_".join(toks)


def choice_keys(texts: list[str]) -> list[str] | None:
    """Shortest distinct word-prefix slugs (4..8 words; None if longer answers still collide) after dropping a leading phrase every answer shares
    ("because the conversion ..."); numbered suffix only if two texts slug identically."""
    toks = [_tokens(t) for t in texts]
    if any(not t for t in toks):
        return None
    n = 0
    while all(len(t) > n + 1 for t in toks) and len({t[n] for t in toks}) == 1:
        n += 1
    toks = [t[n:] for t in toks]
    for words in (4, 5, 6, 7, 8):
        keys = [_slug(t, words) for t in toks]
        if len(set(keys)) == len(keys):
            return keys
    if any(len(t) > 8 for t in toks):
        return None  # parallel answers that differ only late ("decrease X, increase Y, ..."): not a snap choice
    seen: dict[str, int] = {}
    out = []
    for k in keys:
        seen[k] = seen.get(k, 0) + 1
        out.append(k if seen[k] == 1 else f"{k}_{seen[k]}")
    return out


def stem_key(stem: str) -> str:
    return norm(INSTRUCTION.sub("", stem))


def item_key(stem: str, answer: str = "", context: str | None = None) -> str:
    """Near-duplicate key: the normalized stem (plus context); a generic stem ("Which of the following is
    true?", under 9 words) also keys on its correct answer."""
    k = stem_key(stem) + ("|" + norm(context[:300]) if context else "")
    return k + "|" + norm(answer) if len(stem_key(stem).split()) < 9 and not context else k


DIGIT = re.compile(r"\d")
# A number standing on its own (not inside a formula like H2SO4), once a parenthetical year like "(1896)" is dropped.
NUMBER = re.compile(r"(?<![A-Za-z\d])\d")
YEAR_PAREN = re.compile(r"\(\s*(c\.\s*)?\d{3,4}s?(\s*[-–]\s*\d{2,4})?\s*(BCE|BC|CE|AD)?\s*\)")
# Answers that point at the other answers: removable when they are not the correct one.
REF_OPTION = re.compile(
    r"^\s*(\(?[a-e]\)?\s*(,|and|&)\s*\(?[a-e]\)?|(both|all|none|neither|any) (of )?(the |these |those )?"
    r"(above|options|answers|choices|of these|of the above)?|both [a-e] and [a-e]|neither [a-e] nor [a-e]"
    r"|all of these|none of these|all the above|none|all|both|neither)\s*\.?\s*$",
    re.I,
)
# Answers that combine numbered statements (I only / I and II / True, False): the item is dropped.
COMBO_OPTION = re.compile(
    r"^\s*((i|ii|iii|iv|v|1|2|3|4)(\s*(,|and|&|or)\s*(i|ii|iii|iv|v|1|2|3|4))*(\s*,?\s*(and|or)\s*(i|ii|iii|iv|v))?"
    r"(\s+only)?|(true|false)\s*,\s*(true|false)|statement \d.*)\s*\.?\s*$",
    re.I,
)
# Needs a picture, table, or numbered statements.
VISUAL = re.compile(
    r"\b(diagram|figure|shown (below|above|here|in)|pictured|picture|graph below|table below|the table|the graph|"
    r"the map|the chart|illustration|image|drawing|below shows|above shows)\b|\bstatement\s*\d|^\s*i\.\s|\n\s*i\.\s",
    re.I,
)
# Arithmetic, counting, and computation (docs/01-jev.md section 7).
ARITH = re.compile(
    r"=|\^|√|\$(?!\d)|\bsqrt\b|\d\s*[-+*/×÷]\s*\d|\b(calculate|compute|how many|how much|what is the value|evaluate|"
    r"solve for|find the (value|sum|product|number|probability|area|volume|degree|order|index)|simplify)\b",
    re.I,
)


def snap_filter(stem: str, options: list[str], correct: int) -> tuple[list[str], int] | None:
    """Categorical, standalone, no arithmetic. Drops items with a picture/computation stem, numeric answers, or
    numbered-statement combos; removes a wrong "all/none of the above"-style answer (drops the item if it is
    the correct one); answers must stay distinct and at least 2."""
    if VISUAL.search(stem) or ARITH.search(stem):
        return None
    if any(not o.strip() or NUMBER.search(YEAR_PAREN.sub("", o)) or COMBO_OPTION.match(o) for o in options):
        return None
    if REF_OPTION.match(options[correct]):
        return None
    keep = [i for i, o in enumerate(options) if not REF_OPTION.match(o)]
    opts = [options[i] for i in keep]
    if len(opts) < 2 or len({norm(o) for o in opts}) != len(opts) or choice_keys(opts) is None:
        return None
    return opts, keep.index(correct)


POLITICIANS = re.compile(r"\b(biden|putin|pelosi|bernie sanders|desantis|kamala|netanyahu|zelensk\w+|bolsonaro|"
                         r"erdogan|xi jinping|maga|hillary|george w\.? bush|reagan|nixon|thatcher|boris johnson)\b", re.I)


BIO_SEX = re.compile(r"\b(a?sexual(ly)? reproduc\w*|a?sexual(ly)?|sexes|sex of|sex ratios?|sex attractants?|sex pheromones?|sex (cells?|chromosomes?|linked|determination|"
                     r"hormones?|organs?)|sex-linked)\b", re.I)


def flags(text: str, extra: tuple[str, ...] = ()) -> list[str]:
    """Shared content flags: boolq's political and sensitive patterns plus named modern politicians."""
    out = list(extra)
    if (BOOLQ.POLITICAL.search(text) or POLITICIANS.search(text)) and "political" not in out:
        out.append("political")
    if BOOLQ.SENSITIVE.search(BIO_SEX.sub(" ", text)) and "sensitive" not in out:
        out.append("sensitive")
    return out


def topic_hint(question: str, title: str = "", passage: str = "", within: str = "world",
               default: str | None = None) -> str:
    """boolq's keyword node hint, kept only if it falls under `within`; otherwise `default` (or `within`)."""
    h = BOOLQ.node_hint(question, title, passage)
    fallback = default or within
    if h == "world.society" and within != "world.society":  # boolq's nothing-matched fallback
        return fallback
    return h if h == within or h.startswith(within + ".") else fallback


# Keyword map for grade-school and intro science (arc, sciq, openbookqa); specific rules first, ties go earlier.
SCIENCE_RULES = [
    (r"astronauts?|space shuttle|spacecraft|rockets?|satellites?|space station|space probes?|spaceflight|nasa",
     "world.science.astronomy_space.rockets_spaceflight"),
    (r"moons?|planets?|the sun|sun'?s|sunlight|mars|jupiter|saturn|venus|neptune|uranus|pluto|comets?|asteroids?|"
     r"meteor\w*|eclipses?|orbit\w*|solar system|lunar|tides?|rotat\w+|revolv\w+|axis", 
     "world.science.astronomy_space.solar_system_bodies"),
    (r"stars?|galax\w+|universe|light.years?|big bang|constellations?|nebula\w*|telescopes?|supernova\w*",
     "world.science.astronomy_space.stars_cosmos"),
    (r"weather|clouds?|rain\w*|precipitation|humidity|storms?|hurricanes?|tornado\w*|winds?|air mass\w*|fronts?|"
     r"climate|atmospher\w*|thunder\w*|lightning|seasons?|water cycle|evaporat\w+|condens\w+|barometer|snow|hail|"
     r"drought|greenhouse", "world.nature.weather_climate"),
    (r"rocks?|minerals?|erosion|erode\w*|weathering|sediment\w*|volcan\w*|earthquakes?|tectonic|plates?|crust|mantle|"
     r"core|fossils?|glaciers?|soil|landforms?|magma|lava|igneous|metamorphic|canyons?|mountains?|continents?|"
     r"geolog\w+|faults?|seismic", "world.nature.geology"),
    (r"fish\w*|sharks?|whales?|coral\w*|marine|dolphins?|octopus\w*|jellyfish|ocean animals?|sea (animals?|life)|"
     r"plankton|algae", "world.nature.sea_life"),
    (r"birds?|feathers?|beaks?|nests?|owls?|eagles?|penguins?|hawks?|ducks?|robins?|chickens?|hens?",
     "world.nature.birds"),
    (r"insects?|butterfl\w+|bees?|ants?|spiders?|frogs?|toads?|snakes?|lizards?|turtles?|amphibians?|reptiles?|worms?|"
     r"caterpillars?|beetles?|mosquito\w*|moths?|tadpoles?|larva\w*|crickets?|grasshoppers?",
     "world.nature.reptiles_insects"),
    (r"mammals?|bears?|deer|wolf|wolves|rabbits?|elephants?|lions?|squirrels?|foxes|fox|mice|mouse|bats?|horses?|"
     r"cows?|dogs?|cats?|giraffes?|monkeys?|apes?|seals?|polar bears?", "world.nature.mammals"),
    (r"plants?|leaf|leaves|seeds?|flowers?|roots?|stems?|photosynthe\w+|trees?|pollen|pollinat\w+|fung\w+|mushrooms?|"
     r"chlorophyll|germinat\w+|moss\w*|ferns?", "world.nature.plants_fungi"),
    (r"ecosystems?|food chains?|food webs?|habitats?|predators?|prey|producers?|consumers?|decomposers?|pollut\w+|"
     r"recycl\w+|conservation|extinct\w*|endangered|biomes?|niche|deforestation|environment\w*|wetlands?|"
     r"populations?|invasive", "world.nature.ecosystems_conservation"),
    (r"diseases?|virus\w*|bacteri\w+|infections?|vaccin\w+|immun\w+|illness\w*|pathogens?|germs?|flu|cancer",
     "world.health.diseases"),
    (r"nutrients?|vitamins?|diet\w*|calories?|protein|carbohydrates?|healthy (food|eating)",
     "world.health.nutrition"),
    (r"human body|organs?|heart|lungs?|blood|bones?|muscles?|skin|brain|nerv\w+|digest\w+|stomach|kidneys?|breath\w*|"
     r"skeleto\w+|intestines?|liver|hormones?|glands?|circulatory|respiratory|eyes?|ears?|arter\w+|veins?|capillar\w+", "world.health.human_body"),
    (r"cells?|dna|genes?|genetic\w*|inherit\w*|traits?|chromosomes?|mitosis|meiosis|offspring|reproduc\w+|"
     r"evolution\w*|evolve\w*|adapt\w*|species|organisms?|natural selection|mutations?|nucleus|enzymes?|"
     r"heredit\w+|dominant|recessive|embryo\w*|biolog\w+|rna|exons?|introns?|splicing|ribosom\w+|mitochondri\w+|"
     r"cytoplasm|membranes?|photosynthe\w+|tissues?", "world.science.biology_genetics"),
    (r"elements?|periodic table|metals?|oxygen|hydrogen|carbon|nitrogen|iron|copper|sodium|chlorine|helium|"
     r"calcium|gold|silver|aluminum|mercury|lead", "world.science.chemistry.elements_metals"),
    (r"chemicals?|reactions?|compounds?|molecules?|mixtures?|solutions?|dissolv\w+|acids?|bases?|ph|"
     r"physical change|chemical change|bonds?|solvent|solute|salt|rust\w*|ions?|isotopes?|chemistry",
     "world.science.chemistry.chemistry_concepts"),
    (r"electrons?|protons?|neutrons?|nucle(us|i)|atoms?|atomic|subatomic|quarks?|forces?|gravit\w+|friction|"
     r"magnet\w*|motion|speed|velocity|acceleration|inertia|newton\w*|momentum|push|pull",
     "world.science.physics.particles_forces"),
    (r"energy|heat\w*|thermal|states? of matter|solids?|liquids?|gas(es)?|melt\w*|boil\w*|freez\w+|mass|density|"
     r"temperature|kinetic|potential energy|conduct\w+|convection|radiation", "world.science.physics.matter_energy"),
    (r"light|sound|waves?|reflect\w*|refract\w*|lens\w*|mirrors?|prisms?|vibrat\w+|frequency|pitch|echo\w*|"
     r"wavelength", "world.science.physics"),
    (r"circuits?|electric\w*|batter(y|ies)|current|insulators?|voltage|wires?|bulbs?",
     "world.tech.engineering_inventions.electrical_general"),
    (r"fossil fuels?|renewable|nonrenewable|solar (energy|panels?|power|cells?)|wind turbines?|coal|oil|natural gas|"
     r"power plants?|nuclear power|hydroelectric|fuels?|gasoline|biofuel\w*|dams?",
     "world.tech.engineering_inventions.energy_power"),
    (r"machines?|levers?|pulle\w+|engines?|gears?|inclined planes?|wheels?|wedges?|screws?",
     "world.tech.engineering_inventions.machines_engines"),
    (r"thermometers?|microscopes?|balances?|graduated cylinders?|rulers?|instruments?|compass\w*|scales?|"
     r"magnifying|stopwatch\w*|beakers?|goggles", "world.tech.engineering_inventions.optics_instruments"),
    (r"units?|meters?|grams?|liters?|kilograms?|centimeters?|measure\w*|metric", "world.science.physics.time_units"),
    (r"materials?|plastics?|wood|glass|fabric|rubber|clay|paper|steel|concrete",
     "world.tech.engineering_inventions.materials"),
    (r"farm\w*|crops?|agricultur\w+|livestock|irrigat\w+|fertiliz\w+|harvest\w*",
     "world.tech.engineering_inventions.agriculture_living"),
]
SCIENCE_RE = [(re.compile(r"\b(?:" + p + r")\b", re.I), n) for p, n in SCIENCE_RULES]


def science_hint(question: str, answer: str = "", default: str = "world.science") -> str:
    """Score every rule (question matches x2, correct answer x1); highest wins, ties to the earlier rule."""
    scores: dict[str, int] = {}
    order: dict[str, int] = {}
    for i, (rx, node) in enumerate(SCIENCE_RE):
        order.setdefault(node, i)
        s = 2 * len(rx.findall(question)) + len(rx.findall(answer))
        if s:
            scores[node] = scores.get(node, 0) + s
    if not scores:
        return default
    return min(scores, key=lambda n: (-scores[n], order[n]))


def choice_question(*, source: str, text: str, answers: list[str], correct: int, node: str, item_id: str,
                    license: str, meta: dict, state=None, origin: str = "dataset", kind: str = "factual",
                    hemisphere: str = "world") -> Question | None:
    keys = choice_keys(answers)
    if keys is None:
        return None
    return Question(
        text=text,
        primitive="choice",
        hemisphere=hemisphere,
        kind=kind,
        origin=origin,
        source=source,
        options={k: a for k, a in zip(keys, answers)},
        state=state,
        truth=keys[correct],
        node_hint=node,
        source_item_id=item_id,
        license=license,
        meta=meta,
    )


def completion_text(stem: str) -> tuple[str, str]:
    """(text, origin): a question as-is; a trailing sentence fragment wrapped in a fixed completion wording, with
    any leading context sentences kept in front of it."""
    s = INSTRUCTION.sub("", stem.strip()).strip()
    if re.search(r"[?]\s*$", s) or re.search(r"(_{2,}|\.\.\.)", s) or re.search(r"[.!:]\s*$", s):
        return s, "dataset"
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", s)
    context, last = " ".join(parts[:-1]), parts[-1]
    last = last[0].upper() + last[1:]
    wrapped = f'Which option best completes this statement: "{last} ..."?'
    return (f"{context} {wrapped}" if context else wrapped), "template"


# --- MMLU ---------------------------------------------------------------------------------------------------
# subject -> node (a keyword hint may refine it within this node). moral_scenarios is skipped (two-scenario format).
SUBJECTS = {
    "abstract_algebra": "world.science.mathematics",
    "anatomy": "world.health.human_body",
    "astronomy": "world.science.astronomy_space",
    "business_ethics": "world.money",
    "clinical_knowledge": "world.health.medicine",
    "college_biology": "world.science.biology_genetics",
    "college_chemistry": "world.science.chemistry.chemistry_concepts",
    "college_computer_science": "world.tech.software_programming",
    "college_mathematics": "world.science.mathematics",
    "college_medicine": "world.health.medicine",
    "college_physics": "world.science.physics",
    "computer_security": "world.tech.internet_web",
    "conceptual_physics": "world.science.physics",
    "econometrics": "world.money.economics",
    "electrical_engineering": "world.tech.engineering_inventions.electrical_general",
    "elementary_mathematics": "world.science.mathematics",
    "formal_logic": "world.society.philosophy_thinkers",
    "global_facts": "world",
    "high_school_biology": "world.science.biology_genetics",
    "high_school_chemistry": "world.science.chemistry.chemistry_concepts",
    "high_school_computer_science": "world.tech.software_programming",
    "high_school_european_history": "world.history",
    "high_school_geography": "world.places",
    "high_school_government_and_politics": "world.society.politics_government",
    "high_school_macroeconomics": "world.money.economics",
    "high_school_mathematics": "world.science.mathematics",
    "high_school_microeconomics": "world.money.economics",
    "high_school_physics": "world.science.physics",
    "high_school_psychology": "world.science.psychology_neuroscience",
    "high_school_statistics": "world.science.mathematics",
    "high_school_us_history": "world.history",
    "high_school_world_history": "world.history",
    "human_aging": "world.health.sleep_aging",
    "human_sexuality": "world.health",
    "international_law": "world.society.crime_law",
    "jurisprudence": "world.society.crime_law",
    "logical_fallacies": "world.society.philosophy_thinkers",
    "machine_learning": "world.tech.ai",
    "management": "world.money",
    "marketing": "world.money",
    "medical_genetics": "world.science.biology_genetics",
    "miscellaneous": "world",
    "moral_disputes": "world.society.philosophy_thinkers",
    "nutrition": "world.health.nutrition",
    "philosophy": "world.society.philosophy_thinkers",
    "prehistory": "world.history.ancient",
    "professional_accounting": "world.money",
    "professional_law": "world.society.crime_law",
    "professional_medicine": "world.health.medicine",
    "professional_psychology": "world.science.psychology_neuroscience",
    "public_relations": "world.society.media_news",
    "security_studies": "world.society.politics_government",
    "sociology": "world.society",
    "us_foreign_policy": "world.society.politics_government",
    "virology": "world.health.diseases",
    "world_religions": "world.society.world_religions",
}
SUBJECT_FLAGS = {
    "us_foreign_policy": ("political",),
    "high_school_government_and_politics": ("political",),
    "human_sexuality": ("sensitive",),
}
PARTIES = re.compile(r"\b(political part(y|ies)|parties|partisan\w*|liberals?|conservatives?|elections?)\b", re.I)
PASSAGE_HEAD = re.compile(r"^\s*(this question refers to the following information\.?|"
                          r"use the following (information|passage)[^\n]*)\s*\n", re.I)
MAX_STEM = 1200
MAX_PASSAGE = 2500


def fetch(raw_dir: Path) -> None:
    hf_fetch(raw_dir, "cais/mmlu", {f"{s}.parquet": f"all/{s}/0.parquet" for s in SPLITS})


def _split_stem(stem: str) -> tuple[str, str | None] | None:
    """(question, passage) for passage items, (stem, None) otherwise; None if unusable."""
    stem = stem.replace("\r", "").strip()
    m = PASSAGE_HEAD.match(stem)
    if m:
        body = stem[m.end():].strip()
        if "\n" not in body:
            return None
        passage, q = body.rsplit("\n", 1)
        passage, q = passage.strip(), clean(q)
        if not q or len(passage) > MAX_PASSAGE or len(q) > 400:
            return None
        return q, passage
    if len(stem) > MAX_STEM:
        return None
    return clean(stem), None


def _pool(raw_dir: Path) -> list[dict]:
    pool, seen = [], set()
    for split in SPLITS:
        df = pl.read_parquet(raw_dir / f"{split}.parquet").with_row_index("row")
        for row, q, subject, choices, ans in df.select("row", "question", "subject", "choices", "answer").iter_rows():
            if subject not in SUBJECTS:
                continue
            parts = _split_stem(q)
            if not parts:
                continue
            stem, passage = parts
            kept = snap_filter(stem, [clean(c) for c in choices], int(ans)) if stem else None
            if not kept:
                continue
            answers, correct = kept
            k = item_key(stem, answers[correct], passage)
            if k in seen:
                continue
            seen.add(k)
            pool.append({"id": f"{split}:{row}", "subject": subject, "q": stem, "passage": passage,
                         "answers": answers, "correct": correct, "norm": k})
    return pool


def selected(raw_dir: Path) -> list[dict]:
    """Per-subject cap (salted-hash order), then the overall target."""
    by_subject: dict[str, list[dict]] = {}
    for it in _pool(raw_dir):
        by_subject.setdefault(it["subject"], []).append(it)
    capped = []
    for s in sorted(by_subject):
        capped += top_up([], by_subject[s], PER_SUBJECT, lambda x: x["id"], SALT)
    return top_up([], capped, TARGET, lambda x: x["id"], SALT)


def _node(it: dict) -> str:
    base = SUBJECTS[it["subject"]]
    return topic_hint(it["q"] + " " + it["answers"][it["correct"]], within=base)


def normalize(raw_dir: Path) -> Iterator[Question]:
    for it in sorted(selected(raw_dir), key=lambda x: (x["subject"], x["id"])):
        extra = SUBJECT_FLAGS.get(it["subject"], ())
        blob = " ".join([it["q"], *it["answers"]])
        fl = flags(blob, extra)
        if PARTIES.search(blob) and "political" not in fl and it["subject"] in (
                "high_school_government_and_politics", "us_foreign_policy", "security_studies", "sociology"):
            fl.append("political")
        text, origin = completion_text(it["q"])
        meta = {"subject": it["subject"]}
        if fl:
            meta["flags"] = fl
        q = choice_question(
            source=NAME, text=text, answers=it["answers"], correct=it["correct"], node=_node(it),
            item_id=it["id"], license=LICENSE, meta=meta, origin=origin,
            state={"passage": it["passage"]} if it["passage"] else None,
        )
        if q:
            yield q
