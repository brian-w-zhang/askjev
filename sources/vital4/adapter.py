"""Wikipedia Vital Articles Level 4 -> G6 entity judgments (docs/03-questions.md): 2 questions per article.

  g6.recognize  Noul   'Would most adults have heard of "<X>"?'               kind social
  g6.importance Score  'How important is "<X>" to understanding <domain>?'    kind evaluative

<X> is the article title quoted (titles are sentence case, so unquoted "heard of Stone Age" reads wrong) with any
trailing "(disambiguator)" dropped; state carries the full title and the Wikipedia short description.

The list (with section paths, short descriptions, QIDs, sitelinks, pageviews) is fetched by fetch_vital.py into
data/raw/vital/. Excluded: People > Politicians and leaders, and Politics and government > Ideology and political
theory. Other politics, social issues and activists are kept and flagged "political"; religion-as-belief is
flagged "sensitive", as is sexuality.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Iterator

from askjev.model import Question

NAME = "vital4"
HERE = Path(__file__).resolve().parent
LICENSE = "CC BY-SA 4.0 (Wikipedia: Vital articles list, short descriptions); Wikidata CC0"

EXCLUDE = (
    "People > Politicians and leaders",
    "Society and social sciences > Politics and government > Ideology and political theory",
)
POLITICAL = (
    "People > Rebels, revolutionaries and activists",
    "People > Philosophers, historians, political and social scientists > Political writers",
    "Society and social sciences > Politics and government",
    "Society and social sciences > Society > Issues",
    "Society and social sciences > Society > Social status",
)
SENSITIVE = (
    "People > Religious figures",
    "Philosophy and religion > Religion and spirituality > Religion and spirituality: General",
    "Philosophy and religion > Religion and spirituality > Abrahamic religions",
    "Philosophy and religion > Religion and spirituality > Eastern religions",
    "Philosophy and religion > Religion and spirituality > Other religions",
    "Philosophy and religion > Religion and spirituality > Mythology > Abrahamic mythology",
    "Everyday life > Sexuality and gender",
)

_P = "People > "
_PH = "People > Philosophers, historians, political and social scientists > "
_SC = "People > Scientists, inventors and mathematicians > "
_H = "History > "
_G = "Geography > "
_A = "Arts > "
_R = "Philosophy and religion > "
_E = "Everyday life > "
_S = "Society and social sciences > "
_B = "Biology and health sciences > "
_BA = "Biology and health sciences > Organisms > Animals > "
_BH = "Biology and health sciences > Health, medicine and disease > "
_F = "Physical sciences > "
_T = "Technology > "
_TC = "Technology > Computing and information technology > "

# Vital section prefix -> (World node hint, readable domain for the importance question). Longest prefix wins.
# A few era-less or catch-all sections point at an L1 (world.history, world.sports, world.arts) on purpose:
# no single L2 fits, and placement walks down from the deepest existing ancestor.
SECTION_TO_NODE: dict[str, tuple[str, str]] = {
    # People
    _P + "Entertainers > Actors": ("world.arts.film", "film"),
    _P + "Entertainers > Dancers and choreographers": ("world.arts.theatre_dance", "dance"),
    _P + "Entertainers > Comedians": ("world.arts.comedy", "comedy"),
    _P + "Entertainers > Hosts and performers": ("world.arts.television", "television"),
    _P + "Visual artists": ("world.arts.visual_art", "visual art"),
    _P + "Writers": ("world.arts.books", "literature"),
    _P + "Journalists": ("world.society.media_news", "journalism"),
    _P + "Musicians and composers": ("world.arts.music", "music"),
    _P + "Directors, producers and screenwriters": ("world.arts.film", "film"),
    _P + "Businesspeople": ("world.money.companies_brands", "business history"),
    _P + "Explorers": ("world.history.figures", "the history of exploration"),
    _PH + "Philosophers": ("world.society.philosophy_thinkers", "philosophy"),
    _PH + "Historians and archaeologists": ("world.history.figures", "the study of history"),
    _PH + "Political writers": ("world.society.politics_government", "political thought"),
    _PH + "Economists": ("world.money.economics", "economics"),
    _PH + "Social scientists": ("world.society.philosophy_thinkers", "the social sciences"),
    _PH + "Linguists": ("world.society.languages", "linguistics"),
    _PH + "Psychologists": ("world.science.psychology_neuroscience", "psychology"),
    _P + "Religious figures": ("world.society.world_religions", "religion"),
    _P + "Military leaders and theorists": ("world.history.wars_battles", "military history"),
    _P + "Rebels, revolutionaries and activists": ("world.history.figures", "the history of social movements"),
    _SC + "Pre-modern figures": ("world.science.scientists_discoveries", "the history of science"),
    _SC + "Physics": ("world.science.physics", "physics"),
    _SC + "Astronomy": ("world.science.astronomy_space", "astronomy"),
    _SC + "Chemistry": ("world.science.chemistry", "chemistry"),
    _SC + "Biology": ("world.science.biology_genetics", "biology"),
    _SC + "Medicine": ("world.health.medicine", "medicine"),
    _SC + "Earth science and physical geography": ("world.nature.geology", "earth science"),
    _SC + "Inventors and engineers": ("world.tech.engineering_inventions", "the history of technology"),
    _SC + "Mathematicians": ("world.science.mathematics", "mathematics"),
    _SC + "Computer scientists": ("world.tech.software_programming", "computer science"),
    _P + "Sports figures": ("world.sports.individual_sports", "sports"),
    _P + "Criminals": ("world.society.crime_law", "the history of crime"),
    # History
    _H + "Basics": ("world.history", "world history"),
    _H + "History by continent and region": ("world.history", "world history"),
    _H + "History by country": ("world.history", "world history"),
    _H + "Prehistory": ("world.history.ancient", "prehistory"),
    _H + "Ancient": ("world.history.ancient", "ancient history"),
    _H + "Post-classical": ("world.history.medieval", "medieval history"),
    _H + "Early modern": ("world.history.early_modern", "early modern history"),
    _H + "Modern": ("world.history.modern", "modern history"),
    _H + "Historical cities": ("world.history.ancient", "ancient and pre-modern history"),
    _H + "History by subject matter > History of art": ("world.arts.visual_art", "art history"),
    _H + "History by subject matter > History of everyday life": ("world.history", "social history"),
    _H + "History by subject matter > History of philosophy and religion": (
        "world.society.philosophy_thinkers",
        "the history of ideas",
    ),
    _H + "History by subject matter > History of science and technology": (
        "world.science.scientists_discoveries",
        "the history of science and technology",
    ),
    _H + "History by subject matter > History of society and the social sciences": ("world.history", "social history"),
    _H + "History by subject matter > History of games and sport": ("world.sports", "sports history"),
    _H + "Auxiliary historical sciences": ("world.history", "the study of history"),
    # Geography
    _G + "Basics > Basics: General": ("world.places.continents_regions", "geography"),
    _G + "Basics > Continents": ("world.places.continents_regions", "world geography"),
    _G + "Basics > Cartography": ("world.places.continents_regions", "geography"),
    _G + "Basics > Earth": ("world.places.physical_geography", "physical geography"),
    _G + "Physical geography": ("world.places.physical_geography", "physical geography"),
    _G + "Countries and other regions > Countries": ("world.places.countries", "world geography"),
    _G + "Countries and other regions > Regions and country subdivisions": (
        "world.places.continents_regions",
        "world geography",
    ),
    _G + "Cities": ("world.places.cities", "world geography"),
    _G + "Cities > Urban studies and planning": ("world.places.cities", "cities and urban life"),
    # Arts
    _A + "Arts: General": ("world.arts", "the arts"),
    _A + "Architecture": ("world.arts.architecture_design", "architecture"),
    _A + "Architecture > Specific structures": ("world.places.landmarks", "architecture"),
    _A + "Cultural venues": ("world.places.landmarks", "the arts"),
    _A + "Literature": ("world.arts.books", "literature"),
    _A + "Music": ("world.arts.music", "music"),
    _A + "Performing arts": ("world.arts.theatre_dance", "the performing arts"),
    _A + "Visual arts": ("world.arts.visual_art", "visual art"),
    _A + "Film and television": ("world.arts.film", "film"),
    _A + "Film and television > Specific television shows": ("world.arts.television", "television"),
    _A + "Fictional and legendary characters > Western folklore": ("world.society.mythology_folklore", "folklore"),
    _A + "Fictional and legendary characters > Eastern folklore": ("world.society.mythology_folklore", "folklore"),
    _A + "Fictional and legendary characters > Literature and drama": ("world.arts.books", "literature"),
    _A + "Fictional and legendary characters > Film, television, and games": ("world.arts.film", "popular culture"),
    _A + "Fictional and legendary characters > Superheroes": ("world.arts.film", "popular culture"),
    # Philosophy and religion
    _R + "Philosophy": ("world.society.philosophy_thinkers", "philosophy"),
    _R + "Religion and spirituality": ("world.society.world_religions", "religion"),
    _R + "Religion and spirituality > Mythology": ("world.society.mythology_folklore", "mythology"),
    # Everyday life
    _E + "Clothing and fashion": ("world.arts.fashion", "clothing and fashion"),
    _E + "Cooking, food and drink > Basics": ("world.food.cooking", "food and cooking"),
    _E + "Cooking, food and drink > Cuisine": ("world.food.cuisines", "food and cooking"),
    _E + "Cooking, food and drink > Preparation and serving": ("world.food.cooking", "food and cooking"),
    _E + "Cooking, food and drink > Food types": ("world.food.dishes_ingredients", "food and cooking"),
    _E + "Cooking, food and drink > Drinks": ("world.food.nonalcoholic_drinks", "food and drink"),
    _E + "Family, kinship and interpersonal relationships": (
        "world.society.identity_demographics",
        "family and relationships",
    ),
    _E + "Family, kinship and interpersonal relationships > Marriage and parenting": (
        "world.society.holidays_traditions",
        "family and relationships",
    ),
    _E + "Household items > Furniture and interior design": ("world.arts.architecture_design", "the home"),
    _E + "Household items > Cooking and eating": ("world.food.cooking", "food and cooking"),
    _E + "Housing > Residential and housing units": ("world.money.real_estate", "housing"),
    _E + "Housing > Rooms and spaces": ("world.arts.architecture_design", "the home"),
    _E + "Sexuality and gender": ("world.society.identity_demographics", "human sexuality and gender"),
    _E + "Stages of life": ("world.health.sleep_aging", "the human life course"),
    _E + "Sports and recreation > Entertainment > Entertainment and leisure": ("world.arts.celebrities", "leisure"),
    _E + "Sports and recreation > Entertainment > Recreation and tourism": ("world.places.travel", "leisure and travel"),
    _E + "Sports and recreation > Entertainment > Toys": ("world.sports.board_card_games", "play and games"),
    _E + "Sports and recreation > Entertainment > Games": ("world.sports.board_card_games", "games"),
    _E + "Sports and recreation > Sports > Basics": ("world.sports", "sports"),
    _E + "Sports and recreation > Sports > Team sports": ("world.sports.other_team_sports", "sports"),
    _E + "Sports and recreation > Sports > Athletics": ("world.sports.individual_sports", "sports"),
    _E + "Sports and recreation > Sports > Skating": ("world.sports.individual_sports", "sports"),
    _E + "Sports and recreation > Sports > Water sports": ("world.sports.individual_sports", "sports"),
    _E + "Sports and recreation > Sports > Combat sport and martial arts": ("world.sports.combat_sports", "sports"),
    _E + "Sports and recreation > Sports > Other individual sports": ("world.sports.individual_sports", "sports"),
    # Society and social sciences
    _S + "Society and social sciences: General": ("world.society.identity_demographics", "the social sciences"),
    _S + "Anthropology": ("world.society.identity_demographics", "anthropology"),
    _S + "Business and economics": ("world.money.economics", "economics"),
    _S + "Business and economics > Banking and finance": ("world.money.investing", "finance"),
    _S + "Business and economics > Employment": ("world.money.careers", "work and employment"),
    _S + "Business and economics > Companies": ("world.money.companies_brands", "business"),
    _S + "Culture": ("world.society.holidays_traditions", "culture"),
    _S + "Culture > Festivals, holidays, and observances": ("world.society.holidays_traditions", "holidays and festivals"),
    _S + "Education": ("world.society.education", "education"),
    _S + "Ethnology": ("world.society.identity_demographics", "ethnology"),
    _S + "International organizations": ("world.society.politics_government", "international relations"),
    _S + "Language": ("world.society.languages", "language and linguistics"),
    _S + "Law": ("world.society.crime_law", "law"),
    _S + "Mass media": ("world.society.media_news", "the media"),
    _S + "Mass media > Internet media": ("world.tech.social_media", "the internet"),
    _S + "Politics and government": ("world.society.politics_government", "politics and government"),
    _S + "Psychology": ("world.science.psychology_neuroscience", "psychology"),
    _S + "Society": ("world.society.identity_demographics", "society"),
    _S + "Sociology": ("world.society.identity_demographics", "sociology"),
    _S + "War and military": ("world.history.wars_battles", "warfare"),
    # Biology and health sciences
    _B + "Biology and health sciences: General": ("world.science.biology_genetics", "biology"),
    _B + "Anatomy and morphology": ("world.science.biology_genetics", "biology"),
    _B + "Anatomy and morphology > Animal": ("world.health.human_body", "anatomy"),
    _B + "Anatomy and morphology > Plant anatomy": ("world.nature.plants_fungi", "botany"),
    _B + "Anatomy and morphology > Fungus": ("world.nature.plants_fungi", "biology"),
    _B + "Biochemistry and molecular biology": ("world.science.biology_genetics", "biochemistry"),
    _B + "Biological processes and physiology": ("world.science.biology_genetics", "biology"),
    _B + "Botany": ("world.nature.plants_fungi", "botany"),
    _B + "Cell biology": ("world.science.biology_genetics", "cell biology"),
    _B + "Ecology": ("world.nature.ecosystems_conservation", "ecology"),
    _B + "Zoology": ("world.science.biology_genetics", "zoology"),
    _B + "Organisms": ("world.science.biology_genetics", "biology"),
    _BA + "Vertebrates > Mammals": ("world.nature.mammals", "zoology"),
    _BA + "Vertebrates > Birds": ("world.nature.birds", "zoology"),
    _BA + "Vertebrates > Fishes": ("world.nature.sea_life", "zoology"),
    _BA + "Vertebrates > Agnatha": ("world.nature.sea_life", "zoology"),
    _BA + "Vertebrates > Reptiles": ("world.nature.reptiles_insects", "zoology"),
    _BA + "Vertebrates > Amphibians": ("world.nature.reptiles_insects", "zoology"),
    _BA + "Vertebrates > Vertebrates, general classification": ("world.science.biology_genetics", "zoology"),
    _BA + "Arthropods": ("world.nature.reptiles_insects", "zoology"),
    _BA + "Arthropods > Crustaceans": ("world.nature.sea_life", "zoology"),
    _BA + "Cnidarians": ("world.nature.sea_life", "zoology"),
    _BA + "Echinoderms": ("world.nature.sea_life", "zoology"),
    _BA + "Mollusks": ("world.nature.sea_life", "zoology"),
    _BA + "Porifera": ("world.nature.sea_life", "zoology"),
    _BA + "Invertebrates, others": ("world.nature.reptiles_insects", "zoology"),
    _BA + "General classification": ("world.science.biology_genetics", "zoology"),
    _BA + "Animal breeds and hybrids": ("world.nature.pets_breeds", "domestic animals"),
    _B + "Organisms > Animals": ("world.science.biology_genetics", "zoology"),
    _B + "Organisms > Plants": ("world.nature.plants_fungi", "botany"),
    _B + "Organisms > Fungi": ("world.nature.plants_fungi", "biology"),
    _B + "Organisms > Other eukaryotes": ("world.science.biology_genetics", "microbiology"),
    _B + "Organisms > Prokaryotes": ("world.science.biology_genetics", "microbiology"),
    _BH + "Health and fitness": ("world.health.fitness", "health"),
    _BH + "Drugs and pharmacology": ("world.health.medicine", "medicine"),
    _BH + "Medicine": ("world.health.medicine", "medicine"),
    _BH + "Medicine > Human anatomy": ("world.health.human_body", "human anatomy"),
    _BH + "Morbidity": ("world.health.diseases", "medicine"),
    _BH + "Morbidity > Mental disorder": ("world.health.mental_health", "mental health"),
    # Physical sciences
    _F + "Science basics": ("world.science.scientists_discoveries", "science"),
    _F + "Measurement": ("world.science.physics", "measurement"),
    _F + "Astronomy": ("world.science.astronomy_space", "astronomy"),
    _F + "Chemistry": ("world.science.chemistry", "chemistry"),
    _F + "Earth science": ("world.nature.geology", "earth science"),
    _F + "Earth science > Earth > Biomes": ("world.nature.ecosystems_conservation", "ecology"),
    _F + "Earth science > Air": ("world.nature.weather_climate", "weather and climate"),
    _F + "Earth science > Water > Glaciology": ("world.nature.weather_climate", "earth science"),
    _F + "Physics": ("world.science.physics", "physics"),
    # Technology
    _T + "Technology: General": ("world.tech.engineering_inventions", "technology"),
    _T + "Agriculture": ("world.tech.engineering_inventions", "agriculture"),
    _T + "Biotechnology": ("world.science.biology_genetics", "biotechnology"),
    _TC + "Basics": ("world.tech.computers_hardware", "computing"),
    _TC + "Computer science": ("world.tech.software_programming", "computer science"),
    _TC + "Computer hardware": ("world.tech.computers_hardware", "computing"),
    _TC + "Computer software": ("world.tech.software_programming", "computing"),
    _TC + "Operating systems": ("world.tech.software_programming", "computing"),
    _TC + "User interface": ("world.tech.software_programming", "computing"),
    _TC + "Cryptography": ("world.tech.software_programming", "computer science"),
    _TC + "Data storage": ("world.tech.computers_hardware", "computing"),
    _TC + "Networks": ("world.tech.telecom_networks", "computer networking"),
    _TC + "Internet": ("world.tech.internet_web", "the internet"),
    _TC + "Programming": ("world.tech.software_programming", "computer programming"),
    _T + "Electronics": ("world.tech.engineering_inventions", "electronics"),
    _T + "Engineering": ("world.tech.engineering_inventions", "engineering"),
    _T + "Industry": ("world.tech.engineering_inventions", "industry"),
    _T + "Industry > Energy and fuel": ("world.tech.engineering_inventions", "energy"),
    _T + "Infrastructure": ("world.tech.engineering_inventions", "infrastructure"),
    _T + "Machinery and tools": ("world.tech.engineering_inventions", "technology"),
    _T + "Media and communication": ("world.tech.telecom_networks", "communication technology"),
    _T + "Medical technology": ("world.health.medicine", "medicine"),
    _T + "Military technology": ("world.history.wars_battles", "military technology"),
    _T + "Navigation and timekeeping": ("world.tech.engineering_inventions", "technology"),
    _T + "Optical technology": ("world.tech.engineering_inventions", "optics"),
    _T + "Space": ("world.science.astronomy_space", "space exploration"),
    _T + "Textiles": ("world.arts.fashion", "textiles"),
    _T + "Transportation": ("world.tech.vehicles", "transportation"),
    # Mathematics
    "Mathematics": ("world.science.mathematics", "mathematics"),
}

# Title-level overrides where a Vital section mixes several World L2s (node only; domain stays the section's).
TITLE_NODE = {
    **dict.fromkeys(
        ["Alcoholic beverage", "Beer", "Wine", "Cider", "Cocktail", "Liquor", "Brandy", "Gin", "Rum", "Sake",
         "Tequila", "Vodka", "Whisky"],
        "world.food.alcoholic_drinks",
    ),
    **dict.fromkeys(["Basketball", "National Basketball Association"], "world.sports.basketball"),
    **dict.fromkeys(
        ["Association football", "Copa América", "FIFA World Cup", "La Liga", "Premier League",
         "UEFA Champions League"],
        "world.sports.soccer",
    ),
    **dict.fromkeys(["American football", "National Football League"], "world.sports.american_football"),
    **dict.fromkeys(["Baseball", "Major League Baseball", "Softball"], "world.sports.baseball"),
    **dict.fromkeys(["Auto racing", "Formula One"], "world.sports.motorsport"),
    **dict.fromkeys(
        ["Video game", "Video game console", "Esports", "Final Fantasy", "Grand Theft Auto", "The Legend of Zelda",
         "Minecraft", "Pokémon", "Tetris", "Arcade game"],
        "world.sports.video_games",
    ),
    **dict.fromkeys(
        ["Alibaba Group", "Amazon (company)", "Apple Inc.", "Google", "IBM", "Microsoft", "Samsung", "Tencent",
         "Nintendo", "AT&T"],
        "world.tech.companies",
    ),
    # Sports figures in team sports
    **dict.fromkeys(
        ["Alfredo Di Stéfano", "Pelé", "Franz Beckenbauer", "Johan Cruyff", "Diego Maradona", "Zinedine Zidane",
         "Cristiano Ronaldo", "Marta (footballer)", "Lionel Messi"],
        "world.sports.soccer",
    ),
    **dict.fromkeys(["Babe Ruth", "Jackie Robinson"], "world.sports.baseball"),
    **dict.fromkeys(["Kareem Abdul-Jabbar", "Michael Jordan", "LeBron James"], "world.sports.basketball"),
    "Tom Brady": "world.sports.american_football",
    **dict.fromkeys(["Enzo Ferrari", "Juan Manuel Fangio", "Michael Schumacher"], "world.sports.motorsport"),
    **dict.fromkeys(["Joe Louis", "Sugar Ray Robinson", "Muhammad Ali", "Kanō Jigorō", "Bruce Lee",
                     "Aleksandr Karelin"], "world.sports.combat_sports"),
    **dict.fromkeys(["Bobby Fischer", "Garry Kasparov"], "world.sports.board_card_games"),
    **dict.fromkeys(["W. G. Grace", "Don Bradman", "Sachin Tendulkar", "Dhyan Chand", "Gordie Howe", "Wayne Gretzky",
                     "Jonah Lomu"], "world.sports.other_team_sports"),
}

IMPORTANCE_LEVELS = [
    "A minor detail that most overviews of the field skip",
    "Worth a sentence in an overview of the field",
    "Deserves its own paragraph in an overview of the field",
    "A central topic of the field",
    "One of the defining topics of the field",
]

_KEYS = sorted(SECTION_TO_NODE, key=len, reverse=True)


def lookup(section: str) -> tuple[str, str] | None:
    for k in _KEYS:
        if section == k or section.startswith(k + " > "):
            return SECTION_TO_NODE[k]
    return None


def _starts(section: str, prefixes: tuple[str, ...]) -> bool:
    return any(section == p or section.startswith(p + " > ") for p in prefixes)


def display(title: str) -> str:
    """Drop a trailing disambiguator: "Mercury (element)" -> "Mercury" (state.description disambiguates)."""
    return re.sub(r"\s*\([^)]*\)$", "", title) or title


def fetch(raw_dir: Path) -> None:
    vital = raw_dir.parent / "vital"
    if (vital / "level4.jsonl").exists():
        return
    spec = importlib.util.spec_from_file_location("vital4_fetch", HERE / "fetch_vital.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()


def articles(raw_dir: Path) -> Iterator[dict]:
    with open(raw_dir.parent / "vital" / "level4.jsonl") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def normalize(raw_dir: Path) -> Iterator[Question]:
    unmapped = set()
    for a in articles(raw_dir):
        section, title = a["section"], a["title"]
        if _starts(section, EXCLUDE):
            continue
        hit = lookup(section)
        if hit is None:
            unmapped.add(section)
            continue
        node, domain = hit
        node = TITLE_NODE.get(title, node)
        flags = []
        if _starts(section, POLITICAL):
            flags.append("political")
        if _starts(section, SENSITIVE):
            flags.append("sensitive")
        name = display(title)
        state = {"topic": title, "description": a.get("shortdesc")}
        base_meta = {
            "sitelinks": a.get("sitelinks"),
            "pageviews": a.get("pageviews_60d"),
            "pageviews_window": "2026-07/2026-08",
            "qid": a.get("qid"),
            "vital_level": 4,
            "vital_section": section,
            **({"flags": flags} if flags else {}),
        }
        sid = a.get("qid") or title
        recognize = f'Would most adults have heard of "{name}"?'
        yield Question(
            text=recognize,
            primitive="noul",
            hemisphere="world",
            kind="social",
            origin="template",
            source=NAME,
            template_id="g6.recognize",
            state=state,
            node_hint=node,
            human_text=recognize,
            source_item_id=f"{sid}:recognize",
            license=LICENSE,
            meta=base_meta,
        )
        yield Question(
            text=f'How important is "{name}" to understanding {domain}?',
            primitive="score",
            hemisphere="world",
            kind="evaluative",
            origin="template",
            source=NAME,
            template_id="g6.importance",
            options=IMPORTANCE_LEVELS,
            state=state,
            node_hint=node,
            source_item_id=f"{sid}:importance",
            license=LICENSE,
            meta={**base_meta, "domain": domain},
        )
    if unmapped:
        raise ValueError(f"vital sections missing from SECTION_TO_NODE: {sorted(unmapped)}")
