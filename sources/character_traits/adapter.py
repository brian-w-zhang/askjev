"""Open Psychometrics Statistical "Which Character" Personality Quiz (SWCPQ) character ratings: after the quiz,
volunteers who knew a fictional work rated its characters on bipolar adjective pairs with a 1-100 slider
(1 = the first word, 100 = the second). One Choice per (character, adjective pair): "Which describes <character>
from <work> better: "<a>" or "<b>"?", with the raters' split as the human distribution.

Individual ratings come from the Features Survey dataset (Nov 2019 - Nov 2023, 1.2 GB zip / 3.5 GB csv), which
`fetch` streams once and reduces to per (character, pair) counts (below 50 / exactly 50 / above 50) plus mean and
SD; the zip is then deleted. Character display names and works come from the Features Aggregated dataset
(January 2025) codebook, which uses the same character ids.
"""

# no `from __future__ import annotations`: the CLI loads adapters without registering them in sys.modules.

import html
import io
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import polars as pl

from askjev.model import HumanDist, Question
from askjev.sampling import env_int, hash_order

NAME = "character_traits"
BASE = "https://openpsychometrics.org/tests/characters/data/"
SURVEY = "SWCPQ-Features-Survey-Dataset-November2023"
AGGR = "SWCPQ-Features-Aggregated-Dataset-January2025"
AGG_FILE = "char_ratings_agg.parquet"
LICENSE = "CC BY-NC-SA 4.0 (Open Psychometrics, Statistical 'Which Character' Personality Quiz data)"
TARGET = env_int("TARGET_CHARACTER_TRAITS", 19000)
SALT = "character_traits-v1"
MIN_N = 15  # raters per (character, pair)
MIN_CHAR_N = 20  # median raters per pair for the character: a proxy for a well-known work
PER_CHAR = 12
N_DECISIVE = 9  # of the 12: the most decisive pairs; the rest are the pairs closest to an even split
HEADERS = {"User-Agent": "Mozilla/5.0 (askjev research)"}


# ---------------------------------------------------------------- fetch

def _download(url: str, dest: Path) -> None:
    with httpx.stream("GET", url, headers=HEADERS, follow_redirects=True, timeout=1800) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes(1 << 20):
                f.write(chunk)


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not (raw_dir / AGGR / "codebook.html").exists():
        z = raw_dir / f"{AGGR}.zip"
        cached = raw_dir.parent / "openpsych" / f"{AGGR}.zip"
        if not z.exists():
            if cached.exists():
                shutil.copy(cached, z)
            else:
                _download(BASE + z.name, z)
        zipfile.ZipFile(z).extractall(raw_dir)
    if (raw_dir / AGG_FILE).exists():
        return
    z = raw_dir / f"{SURVEY}.zip"
    if not z.exists():
        _download(BASE + z.name, z)
    with zipfile.ZipFile(z) as zf:
        for m in ("codebook.html", "resources/key.js"):
            (raw_dir / SURVEY / m).parent.mkdir(parents=True, exist_ok=True)
            (raw_dir / SURVEY / m).write_bytes(zf.read(f"{SURVEY}/{m}"))
    cols = ["universe_assigned", "char_ratings"]
    schema = {c: pl.Utf8 for c in cols}
    proc = subprocess.Popen(["unzip", "-p", str(z), f"{SURVEY}/data files/features-survey-dataset.csv"],
                            stdout=subprocess.PIPE)

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
                yield pl.read_csv(io.BytesIO(header + buf), separator="\t", columns=cols, schema_overrides=schema,
                                  quote_char=None, infer_schema_length=0)
        if rest.strip():
            yield pl.read_csv(io.BytesIO(header + rest + b"\n"), separator="\t", columns=cols,
                              schema_overrides=schema, quote_char=None, infer_schema_length=0)

    parts, users, nested = [], 0, 0
    for df in batches():
        users += df.height
        # An entry is [character, feature, rating 1-100, ms]. Some late rows carry a nested feature
        # ([character, [feature, k], rating, ms]) that the codebook does not document; those entries are skipped.
        nested += int(df["char_ratings"].str.count_matches(r"\[\d+, \[").sum() or 0)
        x = (df.select(u=pl.col("universe_assigned"),
                       r=pl.col("char_ratings").str.extract_all(r"\[\d+, \d+, \d+, -?\d+\]"))
             .explode("r").drop_nulls()
             .select("u", *(pl.col("r").str.extract(r"\[(\d+), (\d+), (\d+),", i + 1).cast(pl.Int64).alias(k)
                            for i, k in enumerate(("c", "f", "v"))))
             .filter(pl.col("v").is_between(1, 100)))
        parts.append(x.group_by("u", "c", "f").agg(
            n=pl.len(), lo=(pl.col("v") < 50).sum(), mid=(pl.col("v") == 50).sum(), hi=(pl.col("v") > 50).sum(),
            s=pl.col("v").sum(), ss=(pl.col("v") ** 2).sum()))
    proc.wait()
    if proc.returncode != 0 or users == 0:
        raise RuntimeError(f"character_traits: stream failed (exit {proc.returncode}, {users} rows)")
    agg = (pl.concat(parts).group_by("u", "c", "f").agg(pl.col(k).sum() for k in ("n", "lo", "mid", "hi", "s", "ss"))
           .sort("u", "c", "f"))
    agg.write_parquet(raw_dir / AGG_FILE)
    (raw_dir / "stream_stats.txt").write_text(
        f"survey rows: {users}\nratings: {agg['n'].sum()}\nnested-feature entries skipped: {nested}\n(character, pair) cells: {agg.height}\n")
    z.unlink()  # 1.2 GB; the per-cell aggregate above is all normalize() needs


# ---------------------------------------------------------------- items and works

# Adjective pairs (SWCPQ measure ids) left out. Emoji pairs: 235-266, 333-335. Sexual or innuendo: 6, 33, 45, 175,
# 222, 282, 303, 323, 332, 336, 359, 378, 395, 435, 440, 451, 483, 155 (deviant), 64 (debased). Slurs, slurs-adjacent,
# mental-health or disability labels: 80, 201, 206, 279, 321, 348, 139 (alpha/beta), 234 (trash), 324, 314, 313, 268,
# 205, 93, 287, 106, 369, 286, 274 (traumatized), 406 (junkie), 290 (geriatric). Body-shaming or appearance ratings:
# 40, 148, 184, 267, 498, 108, 176, 276. Loaded politics: 96, 116, 138, 149, 226, 227, 284, 421, 429, 83. No clear
# contrast, nonsense or obscure: 68, 342, 343, 346, 436, 312, 398, 478, 479, 480, 306, 307, 309, 310, 356, 293, 327,
# 55, 65, 105, 118, 152, 157, 172, 185, 192, 194, 210, 300, 328, 330, 331, 382, 408, 426, 437, 462, 466, 467, 474,
# 475, 476, 481, 491, 89-92 and 362 (pairs made of words from other items), 373; duplicates of another pair: 183.
DROP = ({6, 33, 45, 175, 222, 282, 303, 323, 332, 336, 359, 378, 395, 435, 440, 451, 483, 155, 64,
         80, 201, 206, 279, 321, 348, 139, 234, 324, 314, 313, 268, 205, 93, 287, 106, 369, 286, 274, 406, 290,
         40, 148, 184, 267, 498, 108, 176, 276,
         96, 116, 138, 149, 226, 227, 284, 421, 429, 83,
         68, 342, 343, 346, 436, 312, 398, 478, 479, 480, 306, 307, 309, 310, 356, 293, 327, 55, 65, 105, 118, 152,
         157, 172, 185, 192, 194, 210, 300, 328, 330, 331, 382, 408, 426, 437, 462, 466, 467, 474, 475, 476, 481, 491,
         89, 90, 91, 92, 362, 373, 183}
        | set(range(235, 267)) | {333, 334, 335})
POLITICAL = {20, 48, 61, 63, 190, 202, 216, 220, 387, 412, 473, 497}  # kept, flagged
WORD_FIX = {"down2earth": "down-to-earth", "head@clouds": "head in the clouds",
            "open to new experinces": "open to new experiences", "'right-brained'": "right-brained",
            "'left-brained'": "left-brained", "boy/girl-next-door": "girl or boy next door",
            "engineerial": "engineer-minded"}

# Works whose characters are real people (ratings of a portrayal read as ratings of the person), and one
# character written as a racial stereotype.
EXCLUDED_WORKS = {"The Social Network", "The Crown", "Catch Me If You Can", "Hustlers", "House of Gucci", "8 Mile",
                  "Mindhunter", "American Sniper", "Green Book", "Band of Brothers", "Baby Reindeer", "Oppenheimer",
                  "Hamilton", "Penny Arcade", "Ctrl+Alt+Del"}
EXCLUDED_CHARS = {("Gone With the Wind", "Mammy")}

# How the work is named in the question.
WORK_TEXT = {
    "Marvel Cinematic Universe": "the Marvel Cinematic Universe", "Lord of the Rings": "The Lord of the Rings",
    "LOST": "Lost", "Two and Half Men": "Two and a Half Men", "Tommorrow Never Dies": "Tomorrow Never Dies",
    "Firefly + Serenity": "Firefly", "American Horror Story: Season 1": "American Horror Story",
    "True Detective: Season 1": "True Detective", "Star Wars: Episode IV - A New Hope": "Star Wars: A New Hope",
    "Ocean's 11": "Ocean's Eleven", "Terminator 2: Judgement Day": "Terminator 2: Judgment Day",
    "X-Men": "the X-Men films", "Fast & Furious": "the Fast & Furious films", "Harry Potter": "the Harry Potter books",
    "Pirates of the Caribbean": "the Pirates of the Caribbean films", "Law & Order: SVU": "Law & Order: SVU",
    "Twilight": "the Twilight books", "The Hunger Games": "the Hunger Games books",
}

ARTS = "world.arts."
BOOKS = """The Hunger Games|The Great Gatsby|Little Women|Twilight|Romeo and Juliet|Harry Potter|Lord of the Rings|
The Perks of Being a Wallflower|Macbeth|To Kill a Mockingbird|Pride and Prejudice|The Odyssey|Les Misérables|Jane Eyre|
Gone With the Wind|A Series of Unfortunate Events|Sense and Sensibility|Anna Karenina|Ender's Game|Hamlet|
Calvin and Hobbes|Dune|Beowulf|Don Quixote|Atlas Shrugged|Nineteen Eighty-Four|Fahrenheit 451|A Tale of Two Cities|
Mrs Dalloway|The Scarlet Letter|Adventures of Huckleberry Finn|Twelfth Night"""
CARTOONS = """Avatar: The Last Airbender|Rick and Morty|The Simpsons|Cowboy Bebop|Naruto|My Little Pony: Friendship Is Magic|
Bob's Burgers|South Park|Pokémon|Futurama|Sailor Moon|SpongeBob SquarePants|One Punch Man|Death Note|Hazbin Hotel|
Arcane|Attack on Titan|Fullmetal Alchemist: Brotherhood|Neon Genesis Evangelion|Steins;Gate|Archer"""
TV = """Friends|Brooklyn Nine-Nine|Parks and Recreation|The Office|Grey's Anatomy|Sherlock|That 70's Show|The Good Place|
The Queen's Gambit|WandaVision|The Big Bang Theory|Gossip Girl|Firefly + Serenity|Orange is the New Black|The Flash|
The Vampire Diaries|Sex and the City|Two and Half Men|The Umbrella Academy|Glee|How I Met Your Mother|Criminal Minds|NCIS|
30 Rock|Outer Banks|Shameless|Dexter|The Walking Dead|The 100|Law & Order: SVU|Arrow|Stranger Things|Seinfeld|New Girl|
Lucifer|Schitt's Creek|Supernatural|Jane the Virgin|House, M.D.|Breaking Bad|Community|Chilling Adventures of Sabrina|
The Boys|The X-Files|Arrested Development|Game of Thrones|How To Get Away With Murder|Killing Eve|Twin Peaks|
The Good Doctor|This Is Us|LOST|M*A*S*H|Scrubs|Buffy the Vampire Slayer|Modern Family|It's Always Sunny in Philadelphia|
Crazy Ex-Girlfriend|You|Bones|Cobra Kai|Fleabag|Mr. Robot|Normal People|Euphoria|Hannibal|Girls|The Handmaid's Tale|
Space Force|Once Upon a Time|Agents of S.H.I.E.L.D.|Silicon Valley|Peaky Blinders|Castle|Suits|Downton Abbey|
Money Heist|The Mentalist|Outlander|Stargate SG-1|Westworld|CSI: Crime Scene Investigation|Dr. Horrible's Sing-Along Blog|
Friday Night Lights|Unbreakable Kimmy Schmidt|Ozark|Prison Break|Gilmore Girls|Broad City|Star Trek: Deep Space Nine|
Supergirl|Mad Men|Gotham|Superstore|Battlestar Galactica|Psych|Desperate Housewives|The West Wing|The Fall|Veep|
Vikings|Squid Game|Scandal|True Detective: Season 1|Sense8|The Sopranos|Sex Education|Elementary|Dark|Boston Legal|
Emily in Paris|Star Trek: The Next Generation|Shadow and Bone|Better Call Saul|Riverdale|The Wire|Smallville|
Pretty Little Liars|Baywatch|The Good Wife|Locke & Key|American Horror Story: Season 1|The Last of Us|Manifest|
The Bear|Curb Your Enthusiasm|Ahsoka|Virgin River|Yellowstone|Ted Lasso|Succession|Abbott Elementary|The Witcher|
Wheel of Time|Chicago Fire|Blue Bloods|ER|White Collar|Farscape|Wynonna Earp|The Blacklist|Sons of Anarchy|Entourage|
Degrassi: The Next Generation|Ginny & Georgia|The Man in the High Castle|Damages|Tom Clancy's Jack Ryan|Poker Face|
The OA|The Marvelous Mrs. Maisel|Yellowjackets|Star Trek: Voyager|The Americans|Bloodline|The Expanse|After Life|
Your Honor|CSI: Vegas|House of the Dragon|The Fall of the House of Usher|Fallout|Only Murders in the Building|
Malcolm in the Middle|Unbreakable Kimmy Schmidt"""
THEATRE = "Hamilton"
NODE_BY_WORK = {
    **{w.strip(): ARTS + "books.specific_books" for w in BOOKS.split("|")},
    **{w.strip(): ARTS + "television.cartoons_anime" for w in CARTOONS.split("|")},
    **{w.strip(): ARTS + "television.tv_series" for w in TV.split("|")},
    THEATRE: ARTS + "theatre_dance",
}
FILM = ARTS + "film.specific_films"  # every other work is a film (live-action or animated feature)


def _slug(s: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", s.lower().replace("'", ""))).strip("_")


def _pairs(key_js: Path) -> dict[int, tuple[str, str]]:
    t = key_js.read_text(encoding="utf-8").split("var subjects")[0]
    out = {}
    seen = set()
    for m in re.finditer(r'^(\d+)\s*:\s*\["(.*?)",\s*"(.*?)"\]', t, re.M):
        i, a, b = int(m.group(1)), html.unescape(m.group(2)).strip(), html.unescape(m.group(3)).strip()
        a, b = WORD_FIX.get(a, a), WORD_FIX.get(b, b)
        pair = tuple(sorted((a.lower(), b.lower())))
        if i in DROP or pair in seen or not re.search(r"[A-Za-z]", a + b):
            continue
        seen.add(pair)
        out[i] = (a, b)
    return out


def _characters(codebook: Path) -> dict[tuple[str, int], tuple[str, str]]:
    t = codebook.read_text(encoding="utf-8")
    return {(u, int(c)): (html.unescape(n).strip(), html.unescape(w).strip())
            for u, c, n, w in re.findall(r"<td>([A-Za-z0-9]+)/(\d+)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>", t)}


# ---------------------------------------------------------------- normalize

def _pool(raw_dir: Path) -> list[dict]:
    pairs = _pairs(raw_dir / SURVEY / "resources" / "key.js")
    chars = _characters(raw_dir / AGGR / "codebook.html")
    agg = pl.read_parquet(raw_dir / AGG_FILE)
    med = agg.group_by("u", "c").agg(med=pl.col("n").median())
    cells = (agg.join(med, on=["u", "c"]).filter((pl.col("med") >= MIN_CHAR_N) & (pl.col("n") >= MIN_N)
                                                  & pl.col("f").is_in(list(pairs)))
             .with_columns(share_a=(pl.col("lo") + pl.col("mid") / 2) / pl.col("n"))
             .with_columns(maj=pl.max_horizontal("share_a", 1 - pl.col("share_a")))
             # decisive = Wilson 95% lower bound of the majority share, so a 95% split among 300 raters outranks
             # a unanimous 15
             .with_columns(decisive=(pl.col("maj") + 1.92 / pl.col("n")
                                     - 1.96 * (pl.col("maj") * (1 - pl.col("maj")) / pl.col("n")
                                               + 0.96 / pl.col("n") ** 2).sqrt()) / (1 + 3.84 / pl.col("n"))))
    out = []
    for (u, c), g in cells.group_by("u", "c", maintain_order=True):
        name, work = chars[(u, c)]
        if work in EXCLUDED_WORKS or (work, name) in EXCLUDED_CHARS:
            continue
        top = g.sort(["decisive", "f"], descending=[True, False]).head(N_DECISIVE)
        # balanced: the pairs closest to an even split, among pairs rated at least as often as the character's
        # median pair and not politically flagged
        rest = (g.filter(~pl.col("f").is_in(top["f"]) & (pl.col("n") >= pl.col("med"))
                         & ~pl.col("f").is_in(list(POLITICAL)))
                .with_columns(gap=(pl.col("share_a") - 0.5).abs()).sort(["gap", "f"]).head(PER_CHAR - N_DECISIVE)
                .drop("gap"))
        for r in pl.concat([top, rest]).iter_rows(named=True):
            out.append({**r, "name": name, "work": work, "pick": "decisive" if r["f"] in top["f"] else "balanced",
                        "a": pairs[r["f"]][0], "b": pairs[r["f"]][1]})
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    for r in hash_order(_pool(raw_dir), key=lambda r: f"{r['u']}/{r['c']}|{r['f']}", salt=SALT)[:TARGET]:
        name, work, a, b = r["name"], r["work"], r["a"], r["b"]
        wt = WORK_TEXT.get(work, work)
        who = f"the title character of {wt}" if name == work else f"{name} from {wt}"
        ka, kb = _slug(a), _slug(b)
        n = r["n"]
        mean = r["s"] / n
        sd = max(r["ss"] / n - mean ** 2, 0) ** 0.5
        meta = {"character_id": f"{r['u']}/{r['c']}", "character": name, "work": work, "measure_id": r["f"],
                "pick": r["pick"], "mean": round(mean, 2), "sd": round(sd, 2),
                "counts": {"below_50": r["lo"], "at_50": r["mid"], "above_50": r["hi"]},
                "scale_raw": f"slider 1-100, 1 = \"{a}\", 100 = \"{b}\", starts at 50"}
        if r["f"] in POLITICAL:
            meta["flags"] = ["political"]
        yield Question(
            text=f'Which describes {who} better: "{a}" or "{b}"?',
            primitive="choice", hemisphere="world", kind="evaluative", origin="template", source=NAME,
            options={ka: None, kb: None},
            node_hint=NODE_BY_WORK.get(work, FILM),
            human_text=f'Which would most people who know {wt} say describes {name if name != work else "its title character"} better: "{a}" or "{b}"?',
            source_item_id=f"{r['u']}/{r['c']}|{r['f']}",
            license=LICENSE,
            template_id="character_traits.pair",
            human=[HumanDist(
                population=f"OpenPsychometrics web (Which Character quiz volunteers who know {work})",
                distribution={ka: round(r["share_a"], 4), kb: round(1 - r["share_a"], 4)},
                n=n,
                source=f"openpsychometrics.org/tests/characters/data {SURVEY} char_ratings {r['u']}/{r['c']} "
                       f"feature {r['f']}; individual slider ratings: <50 -> first word, >50 -> second, 50 split evenly",
                wave="2019-2023")],
            meta=meta,
        )
