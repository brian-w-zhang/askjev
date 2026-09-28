"""Do people know it? The NSF science-literacy items (Science and Engineering Indicators).

Human data: National Science Board, Science & Engineering Indicators 2018, Appendix Table 7-9, "Correct answers to
factual knowledge questions in physical and biological sciences: 1985-2016" (percent correct; US adults; NSF surveys
1985-2001, University of Michigan 2004, General Social Survey 2006-16; "don't know" counts as incorrect). The
percentages below are transcribed from that table (fetch() downloads it for reference). US government work, public
domain.

Three kinds of question per item: the item itself as the survey asked it (with the 2016 share correct as the human
distribution: correct vs not); what share of US adults answered it correctly in 2016; and, where it was asked, what
share did in 1988. The evolution and big-bang items are left out: they are contested on religious grounds, and
their answers measure belief as much as knowledge (NSF reports them separately for that reason).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "science_literacy"
NODE = "world.society.education.public_science_knowledge"
LICENSE = "Public domain (US Government work: National Science Board, Science & Engineering Indicators 2018)"
URL = "https://ncses.nsf.gov/statistics/2018/nsb20181/assets/404/tables/at07-09.pdf"
TF = {"true": "True", "false": "False"}
# id: (question as asked, options, correct key, % correct 1988, % correct 2016)  -- Appendix Table 7-9
ITEMS = {
    "earth_core": ('True or false: "The center of the Earth is very hot."', TF, "true", 80, 85),
    "continents": ('True or false: "The continents on which we live have been moving their locations for millions of '
                   'years and will continue to move in the future."', TF, "true", 80, 81),
    "earth_sun": ("Does the Earth go around the Sun, or does the Sun go around the Earth?",
                  {"earth_around_sun": "The Earth goes around the Sun", "sun_around_earth": "The Sun goes around the Earth"},
                  "earth_around_sun", 73, 73),
    "year": ("How long does it take for the Earth to go around the Sun: one day, one month, or one year?",
             {"one_day": "One day", "one_month": "One month", "one_year": "One year"}, "one_year", 45, 51),
    "radioactivity": ('True or false: "All radioactivity is man-made."', TF, "false", 65, 70),
    "electrons": ('True or false: "Electrons are smaller than atoms."', TF, "true", 43, 48),
    "lasers": ('True or false: "Lasers work by focusing sound waves."', TF, "false", 36, 45),
    "fathers_gene": ('True or false: "It is the father\'s gene that decides whether the baby is a boy or a girl."', TF,
                     "true", None, 59),
    "antibiotics": ('True or false: "Antibiotics kill viruses as well as bacteria."', TF, "false", 25, 51),
}
SHARE = {f"s{v:02d}": f"{v}-{v + 10}%" for v in range(0, 100, 10)}


def fetch(raw_dir: Path) -> None:
    if not (raw_dir / "at07-09.pdf").exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        (raw_dir / "at07-09.pdf").write_bytes(urllib.request.urlopen(req).read())


def _bin(pct: int) -> str:
    return f"s{min(90, pct // 10 * 10):02d}"


def _q(text, options, set_, item, **kw) -> Question:
    human = kw.pop("human", [])
    truth = kw.pop("truth", None)
    return Question(text=text, primitive="noul" if options is TF else "choice", hemisphere="world", kind="factual",
                    origin="dataset", source=NAME, options=options, node_hint=NODE, license=LICENSE, truth=truth,
                    human=human, source_item_id=f"{set_}:{item}", meta={"experiment": "science_literacy", "set": set_,
                                                                       "item": item, **kw})


def normalize(raw_dir: Path) -> Iterator[Question]:
    for item, (text, opts, key, p88, p16) in ITEMS.items():
        dist = {key: p16 / 100, **{k: (1 - p16 / 100) / (len(opts) - 1) for k in opts if k != key}}
        yield _q(text, opts, "item", item, truth=(key == "true") if opts is TF else key, pct_2016=p16, pct_1988=p88,
                 human=[HumanDist(population="US adults, 2016 General Social Survey", distribution=dist, n=1390,
                                  source="Science & Engineering Indicators 2018, Appendix Table 7-9 (share correct; "
                                         "'don't know' counted as incorrect; the rest split evenly over the wrong answers)")])
        stem = ("whether this is true or false: " + text.replace("True or false: ", "")) if opts is TF else f'"{text}"'
        answer = opts[key]
        for year, pct, n in ((2016, p16, 1390), (1988, p88, 2041)):
            if pct is None:
                continue
            yield _q(f"In a {year} national survey, US adults were asked {stem} (The correct answer is: {answer}.) "
                     f"What share of them answered correctly?", SHARE, f"share_{year}", item, truth=_bin(pct),
                     pct=pct, year=year, n=n, ordered=True)
