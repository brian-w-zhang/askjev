"""World Bank WDI country pairs: "Which country has a higher X: A or B?" factual Choices with truth.

Each template is one WDI indicator. Per country the value is the mean of its latest (up to 5) yearly values in
2016-2023; a pair qualifies only when the gap is clear (ratio and/or absolute gap per template) and the same
country is ahead in every year both report. Countries: World Bank economies that are not aggregates, not
dependent territories, and have >= 1 million people; West Bank and Gaza and Kosovo are left out (statehood
contested). Pairs with Israel, Russia, Ukraine or Iran carry meta.flags=["political"].
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "worldbank_pairs"
API = "https://api.worldbank.org/v2"
LICENSE = "CC BY 4.0 (World Bank World Development Indicators)"
TARGET = env_int("TARGET_WORLDBANK_PAIRS", 9000)
SALT = "worldbank_pairs.v1"
YEARS = "2016:2023"
LATEST = 5  # yearly values averaged per country
MIN_POP = 1_000_000

NON_SOVEREIGN = {"ABW", "ASM", "BMU", "CHI", "CUW", "CYM", "FRO", "GIB", "GRL", "GUM", "HKG", "IMN", "MAC", "MAF",
                 "MNP", "NCL", "PRI", "PYF", "SXM", "TCA", "VGB", "VIR"}
DROP = {"PSE": "statehood contested", "XKX": "statehood contested"}
POLITICAL = {"ISR", "RUS", "UKR", "IRN"}
NAMES = {  # WDI labels -> common English names
    "BHS": "the Bahamas", "GMB": "the Gambia", "COD": "the Democratic Republic of the Congo",
    "COG": "the Republic of the Congo", "EGY": "Egypt", "IRN": "Iran", "KGZ": "Kyrgyzstan", "KOR": "South Korea",
    "PRK": "North Korea", "LAO": "Laos", "SVK": "Slovakia", "SYR": "Syria", "VEN": "Venezuela", "YEM": "Yemen",
    "RUS": "Russia", "SOM": "Somalia", "TUR": "Turkey", "VNM": "Vietnam", "CIV": "Côte d'Ivoire",
    "FSM": "Micronesia", "NRU": "Nauru", "BRN": "Brunei", "USA": "the United States", "GBR": "the United Kingdom",
    "NLD": "the Netherlands", "PHL": "the Philippines", "ARE": "the United Arab Emirates",
    "CAF": "the Central African Republic", "DOM": "the Dominican Republic", "CZE": "the Czech Republic",
    "LCA": "Saint Lucia", "KNA": "Saint Kitts and Nevis", "VCT": "Saint Vincent and the Grenadines",
}

# key: (indicator, node_hint, question text, min ratio, min absolute gap, quota weight)
TEMPLATES: dict[str, tuple] = {
    # money
    "gdp_per_person": ("NY.GDP.PCAP.CD", "world.money.economics.macroeconomics",
                       "Which country has the higher GDP per person (economic output per resident, in US dollars): {a} or {b}?",
                       1.5, 0, 480),
    "gdp_total": ("NY.GDP.MKTP.CD", "world.money.economics.economy",
                  "Which country has the larger economy by total GDP in US dollars: {a} or {b}?", 2.0, 0, 480),
    "inflation": ("FP.CPI.TOTL.ZG", "world.money.economics.macroeconomics",
                  "Which country has had higher consumer price inflation in recent years: {a} or {b}?", 2.0, 5, 480),
    "unemployment": ("SL.UEM.TOTL.ZS", "world.money.economics.economics",
                     "Which country has had a higher unemployment rate in recent years: {a} or {b}?", 1.5, 4, 480),
    "exports_share": ("NE.EXP.GNFS.ZS", "world.money.economics.trade",
                      "Which country's exports of goods and services make up a larger share of its GDP: {a} or {b}?",
                      1.5, 10, 480),
    "tax_share": ("GC.TAX.TOTL.GD.ZS", "world.money.economics.tax",
                  "Which country's central government collects more tax revenue as a share of GDP: {a} or {b}?", 1.4, 4, 480),
    "remittances_share": ("BX.TRF.PWKR.DT.GD.ZS", "world.money.economics.economy",
                          "Which country's economy relies more on money sent home by its workers abroad "
                          "(remittances received as a share of GDP): {a} or {b}?", 2.0, 3, 480),
    "agriculture_share": ("NV.AGR.TOTL.ZS", "world.money.economics.agriculture",
                          "In which country do agriculture, forestry and fishing make up a larger share of the "
                          "economy: {a} or {b}?", 1.5, 4, 480),
    # health (+ alcohol under food)
    "life_expectancy": ("SP.DYN.LE00.IN", "world.health.fitness.ageing",
                        "In which country do people live longer on average (life expectancy at birth): {a} or {b}?",
                        1.0, 5, 360),
    "infant_mortality": ("SP.DYN.IMRT.IN", "world.health.sleep_aging.infant",
                         "Which country has a higher infant mortality rate: {a} or {b}?", 1.5, 3, 360),
    "physicians": ("SH.MED.PHYS.ZS", "world.health.medicine.medicine",
                   "Which country has more doctors relative to the size of its population: {a} or {b}?", 1.5, 0, 360),
    "health_spending": ("SH.XPD.CHEX.PC.CD", "world.health.medicine.hospital",
                        "Which country spends more on health care per person, in US dollars: {a} or {b}?", 1.5, 0, 360),
    "tobacco_use": ("SH.PRV.SMOK", "world.health.medicine.smoking",
                    "In which country does a larger share of adults use tobacco: {a} or {b}?", 1.3, 8, 360),
    "overweight": ("SH.STA.OWAD.ZS", "world.health.fitness.obesity",
                   "In which country is a larger share of adults overweight: {a} or {b}?", 1.2, 10, 360),
    "aged_65_share": ("SP.POP.65UP.TO.ZS", "world.health.sleep_aging.old_age",
                      "Which country has a larger share of its population aged sixty-five or older: {a} or {b}?",
                      1.5, 5, 360),
    "alcohol": ("SH.ALC.PCAP.LI", "world.food.alcoholic_drinks",
                "In which country do adults drink more alcohol per person on average: {a} or {b}?", 1.5, 2, 400),
    # nature
    "forest_cover": ("AG.LND.FRST.ZS", "world.nature.ecosystems_conservation.forest",
                     "Which country has a larger share of its land covered by forest: {a} or {b}?", 1.5, 15, 330),
    "precipitation": ("AG.LND.PRCP.MM", "world.nature.weather_climate.rain",
                      "Which country gets more rain and snow in an average year (average precipitation depth): "
                      "{a} or {b}?", 1.5, 0, 330),
    "protected_land": ("ER.LND.PTLD.ZS", "world.nature.ecosystems_conservation.biodiversity",
                       "Which country has a larger share of its land in protected areas such as national parks and "
                       "nature reserves: {a} or {b}?", 1.5, 10, 330),
    "co2_per_person": ("EN.GHG.CO2.PC.CE.AR5", "world.nature.weather_climate.climate_change",
                       "Which country emits more carbon dioxide per person: {a} or {b}?", 1.5, 0, 330),
    # tech
    "internet_use": ("IT.NET.USER.ZS", "world.tech.internet_web.internet",
                     "In which country does a larger share of the population use the internet: {a} or {b}?",
                     1.2, 20, 230),
    "mobile_subscriptions": ("IT.CEL.SETS.P2", "world.tech.telecom_networks.mobile_phone",
                             "Which country has more mobile phone subscriptions per person: {a} or {b}?", 1.25, 20, 230),
    "electricity_access": ("EG.ELC.ACCS.ZS", "world.tech.engineering_inventions.energy_power",
                           "In which country does a larger share of the population have access to electricity: "
                           "{a} or {b}?", 1.2, 20, 230),
    "renewable_electricity": ("EG.ELC.RNEW.ZS", "world.tech.engineering_inventions.renewable_energy",
                              "Which country generates a larger share of its electricity from renewable sources: "
                              "{a} or {b}?", 1.5, 25, 230),
}


def _get(url: str) -> list:
    for attempt in range(5):
        try:
            r = httpx.get(url, timeout=120)
            r.raise_for_status()
            d = r.json()
            if len(d) < 2 or d[1] is None:
                raise RuntimeError(f"no data: {url} {d[0]}")
            return d[1]
        except (httpx.HTTPError, ValueError):
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed: {url}")


def fetch(raw_dir: Path) -> None:
    jobs = {"countries.json": f"{API}/country?format=json&per_page=400",
            "population.json": f"{API}/country/all/indicator/SP.POP.TOTL?format=json&per_page=20000&date=2023"}
    for key, t in TEMPLATES.items():
        jobs[f"{t[0]}.json"] = f"{API}/country/all/indicator/{t[0]}?format=json&per_page=20000&date={YEARS}"
    for fname, url in jobs.items():
        out = raw_dir / fname
        if out.exists():
            continue
        out.write_text(json.dumps(_get(url)))
        time.sleep(0.5)


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"^the ", "", s)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _countries(raw_dir: Path) -> dict[str, str]:
    meta = json.loads((raw_dir / "countries.json").read_text())
    pop = {r["countryiso3code"]: r["value"] for r in json.loads((raw_dir / "population.json").read_text())}
    out = {}
    for c in meta:
        iso = c["id"]
        if c["region"]["value"].strip() == "Aggregates" or iso in NON_SOVEREIGN or iso in DROP:
            continue
        if (pop.get(iso) or 0) < MIN_POP:
            continue
        out[iso] = NAMES.get(iso, c["name"])
    return out


def _series(raw_dir: Path, code: str, countries: dict[str, str]) -> dict[str, dict[int, float]]:
    ser: dict[str, dict[int, float]] = {}
    for r in json.loads((raw_dir / f"{code}.json").read_text()):
        iso = r["countryiso3code"]
        if iso in countries and r["value"] is not None:
            ser.setdefault(iso, {})[int(r["date"])] = float(r["value"])
    return {iso: dict(sorted(v.items())[-LATEST:]) for iso, v in ser.items()}


def _clear(hi: float, lo: float, ratio: float, gap: float) -> bool:
    if hi - lo < gap:
        return False
    if ratio > 1.0:
        return lo > 0 and hi / lo >= ratio
    return True


def normalize(raw_dir: Path) -> Iterator[Question]:
    countries = _countries(raw_dir)
    total_w = sum(t[5] for t in TEMPLATES.values())
    for key, (code, node, text, ratio, gap, weight) in TEMPLATES.items():
        quota = round(TARGET * weight / total_w)
        ser = _series(raw_dir, code, countries)
        mean = {iso: sum(v.values()) / len(v) for iso, v in ser.items()}
        isos = sorted(ser)
        pairs = []
        for i, a in enumerate(isos):
            for b in isos[i + 1:]:
                hi, lo = (a, b) if mean[a] >= mean[b] else (b, a)
                if not _clear(mean[hi], mean[lo], ratio, gap):
                    continue
                shared = set(ser[a]) & set(ser[b])
                if len(shared) < min(2, len(ser[a]), len(ser[b])):
                    continue
                if any(ser[hi][y] <= ser[lo][y] for y in shared):
                    continue
                pairs.append((hi, lo))
        cap = math.ceil(2 * quota / max(1, len(isos))) + 2
        used: Counter = Counter()
        n = 0
        for hi, lo in hash_order(pairs, lambda p: f"{min(p)}|{max(p)}", f"{SALT}|{key}"):
            if n >= quota:
                break
            if used[hi] >= cap or used[lo] >= cap:
                continue
            used[hi] += 1
            used[lo] += 1
            n += 1
            first, second = sorted((hi, lo), key=lambda c: hashlib.sha256(f"{SALT}|order|{key}|{c}|{hi}{lo}".encode()).hexdigest())
            na, nb = countries[first], countries[second]
            meta = {"indicator": code, "values": {countries[hi]: round(mean[hi], 3), countries[lo]: round(mean[lo], 3)},
                    "years": {countries[hi]: sorted(ser[hi]), countries[lo]: sorted(ser[lo])}}
            if {hi, lo} & POLITICAL:
                meta["flags"] = ["political"]
            yield Question(
                text=text.format(a=na, b=nb),
                primitive="choice", hemisphere="world", origin="template", source=NAME, kind="factual",
                options={_slug(na): na, _slug(nb): nb}, node_hint=node, truth=_slug(countries[hi]),
                source_item_id=f"{key}|{min(hi, lo)}|{max(hi, lo)}", license=LICENSE,
                template_id=f"{NAME}.{key}", meta=meta,
            )
