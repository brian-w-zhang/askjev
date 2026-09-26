"""Basel-Berlin Risk Study (Frey, Pedroni, Mata, Rieskamp & Hertwig 2017; OSF rce7g, CC BY 4.0): 1,500+ adults in
Basel and Berlin answered a German-language battery of risk-taking questionnaires. This adapter uses the
self-report instruments that ask about stable tendencies, not personal history: DOSPERT-40 (likelihood, perceived
risk, expected benefit), the Sensation Seeking Scale V (forced choice), the Barratt Impulsiveness Scale, SOEP
general and domain risk-willingness items, the SOEP lottery-investment item, a pension-fund choice, and eight
risky everyday scenarios. Item texts are English translations of the German wording the respondents saw; each
question carries the item's answer shares from the raw data."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "bbrs_risk"
URL = "https://osf.io/download/hb2mu/"  # data/main/quest/quest_raw.csv
LICENSE = "CC BY 4.0 (The Basel-Berlin Risk Study, OSF rce7g; Frey et al. 2017, Science Advances 3:e1701381)"
POP = "Adults in Basel and Berlin (Basel-Berlin Risk Study, German-language questionnaire)"
SRC = "Basel-Berlin Risk Study, data/main/quest/quest_raw.csv"
NODE_RISK = "self.personality.risk_decision_style"

# ---------- DOSPERT-40 (Weber, Blais & Betz 2002; German version as administered) ----------
DOSPERT = [
    "Admitting that your tastes are different from those of your friends",
    "Camping in the wilderness, far away from civilization and campgrounds",
    "Betting a day's income at the horse races",
    "Buying an illegal drug for your own use",
    "Cheating on an exam",
    "Chasing a tornado by car to take dramatic photos",
    "Investing 10% of your annual income in a moderately growing investment fund",
    "Having five or more alcoholic drinks in a single evening",
    "Not declaring a significant amount of your income on your tax return",
    "Disagreeing with your father on a major issue",
    "Betting a day's income in a poker game",
    "Having an affair with a married man or woman",
    "Forging somebody's signature",
    "Passing off somebody else's work as your own",
    "Going on vacation in a developing country without having arranged travel and hotel accommodation in advance",
    "Arguing with a friend about an issue on which he or she has a different opinion",
    "Going down a ski run that is beyond your ability or closed",
    "Investing 5% of your annual income in a very speculative stock",
    "Asking your boss for a raise",
    "Illegally copying a piece of software",
    "Going whitewater rafting during the strong spring currents",
    "Betting a day's income on the outcome of a sporting event (soccer, basketball, etc.)",
    "Telling a friend that his or her partner has made a pass at you",
    "Investing 5% of your annual income in a conservative stock",
    "Shoplifting a small item (a lipstick, a pen, etc.)",
    "Occasionally wearing provocative or unconventional clothes",
    "Having unprotected sex",
    "Illegally splitting off an extra TV cable connection from the one you pay for",
    "Not wearing a seatbelt when riding in the front passenger seat",
    "Investing 10% of your annual income in government bonds",
    "Regularly doing a dangerous sport (such as climbing or skydiving)",
    "Riding a motorcycle without a helmet",
    "Gambling away a week's income at a casino",
    "Choosing a job you enjoy over one that is prestigious but less enjoyable",
    "Defending a controversial cause you believe in at a public event",
    "Exposing yourself to the sun without sunscreen",
    "Trying bungee jumping at least once",
    "Flying your own small plane, if you had the chance",
    "Walking home alone at night through an unsafe part of town",
    "Regularly eating food high in cholesterol",
]
DOSPERT_SENSITIVE = {4, 12, 27}  # illegal drug, affair, unprotected sex
LIKELY5 = ["I am very unlikely to do this", "I am unlikely to do this", "I am not sure whether I would do this",
           "I am likely to do this", "I am very likely to do this"]
RISK5 = ["It is not risky at all", "It is slightly risky", "It is somewhat risky", "It is very risky",
         "It is extremely risky"]
BENEFIT5 = ["I would get no benefit at all from it", "I would get a little benefit from it",
            "I would get some benefit from it", "I would get a lot of benefit from it",
            "I would get a great deal of benefit from it"]
DOSPERT_FRAMES = {
    "DOSPERT": ('How likely would you be to do this: "{s}"?', LIKELY5, "likelihood",
                "1 very unlikely, 2 unlikely, 3 not sure, 4 likely, 5 very likely"),
    "DOSPERTrisk": ('How risky would it be for you to do this: "{s}"?', RISK5, "risk perception",
                    "1 not risky at all, 3 some risk, 5 very high risk (2 and 4 unlabeled)"),
    "DOSPERTnutz": ('How much benefit would you expect to get from doing this: "{s}"?', BENEFIT5, "expected benefit",
                    "1 no benefit at all, 3 some benefit, 5 great benefit (2 and 4 unlabeled)"),
}
DOSPERT_DOMAIN = {  # Weber et al. 2002 domain of each item (E ethical, F financial, H health/safety, R recreational, S social)
    1: "S", 2: "R", 3: "F", 4: "H", 5: "E", 6: "R", 7: "F", 8: "H", 9: "E", 10: "S", 11: "F", 12: "E", 13: "E",
    14: "E", 15: "R", 16: "S", 17: "R", 18: "F", 19: "S", 20: "E", 21: "R", 22: "F", 23: "S", 24: "F", 25: "E",
    26: "S", 27: "H", 28: "E", 29: "H", 30: "F", 31: "R", 32: "H", 33: "F", 34: "S", 35: "S", 36: "H", 37: "R",
    38: "R", 39: "H", 40: "H",
}

# ---------- Sensation Seeking Scale form V (Zuckerman), German version as administered ----------
SSSV = [
    ("I like wild, uninhibited parties.", "I prefer quiet parties with good conversation."),
    ("There are some movies I would watch a second or third time.", "Watching a movie I have already seen usually bores me."),
    ("I often wish I could be a mountain climber.", "I can't understand people who risk their lives climbing mountains."),
    ("I find body odors unpleasant.", "I like some body smells."),
    ("I get bored seeing the same faces all the time.", "I like the comfortable familiarity of the people I deal with every day."),
    ("I like exploring a strange city, even if I might get lost.", "In places I don't know well, I try to join a tour group."),
    ("I dislike people who do or say things that shock or hurt others.", "If you can predict almost everything a person will do or say, he or she must be boring."),
    ("I usually don't enjoy a movie or game where I can tell what will happen next.", "I don't mind watching a movie or playing a game where I can predict what will happen next."),
    ("I have smoked marijuana or would like to.", "I would never smoke marijuana."),
    ("I would not take drugs that might cause unknown or dangerous reactions in me.", "I would like to try one of the drugs that cause hallucinations, such as LSD."),
    ("A sensible person avoids activities that are dangerous.", "I sometimes like to do things that are a little frightening."),
    ("I dislike people who have overly loose views about sex.", "I like being around uninhibited people."),
    ("Intoxicants make me feel uncomfortable.", "I like being high (on alcohol or other drugs)."),
    ("I like hot, spicy foreign food.", "I don't much like spicy, unfamiliar dishes."),
    ("I like looking at friends' souvenir photos.", "Other people's souvenir photos bore me."),
    ("I would like to learn to water-ski.", "I have no desire to learn to water-ski."),
    ("I would like to try surfing.", "I have no desire to try surfing."),
    ("On vacation I like to just set off, stop where I like, and stay as long as I feel like it.", "When I travel, I like to plan my route and how long I stay fairly precisely."),
    ("I prefer down-to-earth people as friends.", "I like making friends with people considered unconventional (such as artists or hippies)."),
    ("I have no desire to learn to fly a plane.", "I would like to learn to fly a plane."),
    ("Diving is not for me.", "I would like to go deep-sea diving."),
    ("I don't mind getting to know gay people.", "I feel uncomfortable getting to know gay people."),
    ("I would like to try parachute jumping.", "I would never jump out of a plane, not even with a parachute."),
    ("I prefer friends whose behavior I sometimes find hard to predict.", "I prefer friends who are predictable."),
    ("I am not interested in experiences for their own sake.", "I love new and exciting experiences, even if they are sometimes a little unconventional or illegal."),
    ("Good art is clear, symmetrical in form and harmonious in color.", "I often find beauty in the clashing colors and unusual shapes of modern painting."),
    ("I like spending time in the familiar surroundings of my home.", "I get very restless if I have to stay at home for a while."),
    ("I would like to jump from a high diving board at a swimming pool.", "I am afraid of jumping from high diving boards at swimming pools."),
    ("I like going out with people of the other sex whom I find physically attractive.", "I like meeting people of the other sex who share my values."),
    ("Heavy drinking usually ruins a party because some people get loud and unpleasant.", "Full glasses guarantee a successful party."),
    ("Overexcited people get on my nerves.", "I can't stand boring people."),
    ("Everyone should have as many sexual experiences as possible.", "One can have enough sexual experience with one or a few partners."),
    ("Even if I had enough money, I would not mix with people who lead a jet-set life.", "I can imagine enjoying the life of a jet-setter."),
    ("I like witty, clever people even if they sometimes make jokes at other people's expense.", "I dislike people who have fun at the expense of other people's feelings."),
    ("Seeing so many sex scenes in movies makes me uncomfortable.", "I can't get enough of sex scenes in movies."),
    ("I feel best after a few drinks.", "Something is wrong with people who need alcohol to feel good."),
    ("People should dress according to certain standards of taste and style.", "Everyone should dress however they like."),
    ("Sailing long distances in a sailboat is very reckless.", "I would like to sail a long distance in a small but seaworthy boat."),
    ("I have no patience with dull and boring people.", "I find something interesting in almost everyone."),
    ("Skiing down a high mountain is pointless and dangerous.", "I enjoy skiing fast down a high mountain."),
]
SSSV_SENSITIVE = {9, 10, 12, 13, 32, 35}
SSSV_POLITICAL = {22}

# ---------- Barratt Impulsiveness Scale (BIS-11), German version as administered ----------
BIS = [
    "I plan my tasks carefully.", "I often do things without thinking first.", "I often make up my mind quickly.",
    "I am happy-go-lucky.", "I am inattentive.", "My thoughts race.", "I plan trips well ahead of time.",
    "I have good self-control.", "I concentrate easily.", "I make sure I am covered against every eventuality in life.",
    "I often squirm in my seat at plays or lectures.", "I think things through carefully.",
    "I make plans to keep my job secure.", "I say things without thinking.", "I like to think about complex things.",
    None, "I act on impulse.", "I get bored quickly when solving mental puzzles.", "I like to act on the spur of the moment.",
    "I am a steady thinker.", None, "I buy things on impulse.", "I can't keep my thoughts on just one thing.",
    "I change hobbies often.", "I spend more money than I earn.", "I often think about unimportant things.",
    "I am more interested in the present than the future.", "I get restless quickly at the theater or at lectures.",
    "I like puzzles.", "I am future-oriented.",
]  # None: "I change jobs often" / "I change where I live often" (personal history, skipped)
FREQ4 = ["This is rarely or never true of me", "This is occasionally true of me", "This is often true of me",
         "This is almost always or always true of me"]
BIS_NODE = {
    "plan": "self.personality.big_five.conscientiousness.order_caution",
    "impulse": "self.personality.big_five.neuroticism.impulses_coping",
    "attention": "self.personality.big_five.conscientiousness.drive_self_discipline",
}

# ---------- SOEP risk willingness (0-10) ----------
RISK_LEVELS = [
    "I am not at all willing to take risks (0-1 on a 0-10 scale)",
    "I am rarely willing to take risks (2-3 on a 0-10 scale)",
    "I am moderately willing to take risks (4-6 on a 0-10 scale)",
    "I am quite willing to take risks (7-8 on a 0-10 scale)",
    "I am very willing to take risks (9-10 on a 0-10 scale)",
]
RLRQ_DOMAINS = ["while driving", "in financial investments", "in leisure and sports", "in your career",
                "with your health", "in trusting strangers"]


def _bin11(v: int) -> int:  # raw 1..11 = 0..10
    x = v - 1
    return 0 if x <= 1 else 1 if x <= 3 else 2 if x <= 6 else 3 if x <= 8 else 4


LOTTERY = ("Imagine you win 100,000 euros in a lottery. Right after you receive it, a reputable bank offers you an "
           "investment: there is a chance to double the money within two years, and an equally large risk of losing "
           "half of the amount invested. You can invest all of the money, part of it, or turn the offer down. How much "
           "of your lottery winnings would you put into this risky but potentially profitable investment?")
LOTTERY_LEVELS = [  # raw 6 (nothing) .. 1 (all), low -> high
    "I would invest nothing and turn the offer down", "I would invest 20,000 euros", "I would invest 40,000 euros",
    "I would invest 60,000 euros", "I would invest 80,000 euros", "I would invest the whole 100,000 euros",
]
FUND_TEXT = "How would you invest additional savings for your retirement?"
FUND_OPTS = {
    "fund_with_25_percent_stocks": "A fund for risk-aware investors who accept moderate short-term price swings: "
                                   "mostly bonds, with a small share of stocks (25%)",
    "fund_with_45_percent_stocks": "A fund for investors with a higher appetite for risk who accept larger price "
                                   "swings: stocks traded worldwide (45%) and bonds",
}

# ---------- risky everyday scenarios (PRI, choice columns PRI_1, 3, ..., 15) ----------
PRI = [
    ("You are very eager to see a film that is showing only once, at a local cinema. When you arrive, you realize "
     "you forgot to lock your front door. Going home to lock it would take 20 minutes, so you would miss 15 minutes "
     "of the film. What do you do?", ["go_back_and_lock_the_door", "stay_and_watch_the_film"]),
    ("You have overslept and risk being late for an important work meeting. You have to drive through a residential "
     "area with a 30 km/h speed limit. The street is well lit and there are only a few people about. What do you do?",
     ["drive_faster_than_the_limit", "keep_to_the_speed_limit"]),
    ("Some wealthy friends you haven't seen for a long time have invited you to an expensive restaurant. You know the "
     "meal will be very expensive and you are afraid you can't afford it. Do you go and hope you can somehow pay, or "
     "stay home and make up an excuse?", ["go_to_the_restaurant", "stay_home_with_an_excuse"]),
    ("You want to visit a close relative in hospital and manage to leave work during rush hour. As usual, the small "
     "visitor car park is full, and you know you would have to wait at least 15 minutes for a space. You could park "
     "in the staff car park, but it is checked now and then and cars are sometimes towed. What do you do?",
     ["park_in_the_staff_car_park", "wait_for_a_visitor_space"]),
    ("You started a new job on Friday and overhear your new colleagues talking about going to the pub after work. "
     "You would like to get to know them better, but you weren't invited, and you don't know whether that was an "
     "oversight or on purpose. On your way home you pass the pub. What do you do?",
     ["go_into_the_pub", "keep_walking_home"]),
    ("You disagree with your colleagues on almost every political issue. During a discussion, a colleague asks what "
     "you think about a specific political issue. You could say what you think, but doing so in front of everyone "
     "could embarrass you. What do you do?", ["say_what_you_think", "keep_quiet"]),
    ("You have suffered from severe headaches for a long time. Your doctor tells you about a new experimental "
     "medicine and asks whether you want to try it, even though its side effects could be dangerous for you. What "
     "do you do?", ["try_the_new_medicine", "decline_the_new_medicine"]),
    ("Your doctor tells you that you have a viral infection and must rest and keep warm; otherwise it could get worse "
     "and even put you in hospital. But you have an important work meeting you very much want to attend, which could "
     "significantly affect your future. What do you do?", ["stay_home_and_rest", "go_to_the_meeting"]),
]


def fetch(raw_dir: Path) -> None:
    p = raw_dir / "quest_raw.csv"
    if not p.exists():
        r = httpx.get(URL, follow_redirects=True, timeout=300)
        r.raise_for_status()
        p.write_bytes(r.content)


def _slug(s: str, maxlen: int = 48) -> str:
    words = re.findall(r"[a-z0-9]+", s.lower().replace("'", ""))
    k, cut = "", False
    for w in words:
        if len(k) + len(w) + 1 > maxlen:
            cut = True
            break
        k = f"{k}_{w}" if k else w
    parts = k.split("_")
    while cut and len(parts) > 3 and parts[-1] in TRAILING:  # a cut key shouldn't end on "the", "or", ...
        parts.pop()
    return "_".join(parts)


TRAILING = {"a", "an", "the", "or", "and", "of", "with", "to", "in", "on", "at", "for", "by", "who", "whom", "that",
            "if", "my", "me", "makes", "is", "be", "usually", "i", "even", "than"}


def _dist(rows: list[dict], col: str, conv) -> tuple[dict[str, float], int] | None:
    c = Counter()
    for r in rows:
        v = (r.get(col) or "").strip()
        if not v:
            continue
        k = conv(int(v))
        if k is not None:
            c[str(k)] += 1
    n = sum(c.values())
    if n < 100:
        return None
    return {k: round(v / n, 4) for k, v in sorted(c.items())}, n


def _q(text, prim, opts, dist, n, sid, node, kind="personality", meta=None, flags=()):
    meta = dict(meta or {})
    if flags:
        meta["flags"] = sorted(set(flags))
    return Question(
        text=text, primitive=prim, hemisphere="self", kind=kind, origin="dataset", source=NAME, options=opts,
        node_hint=node, source_item_id=sid, license=LICENSE,
        human=[HumanDist(population=POP, distribution=dist, n=n, source=SRC)], meta=meta,
    )


def _bis_node(i: int) -> str:
    if i in (1, 7, 8, 10, 12, 13, 20, 30):
        return BIS_NODE["plan"]
    if i in (5, 6, 9, 11, 18, 23, 26, 28):
        return BIS_NODE["attention"]
    if i in (15, 29):
        return "self.personality.big_five.openness.ideas_imagination"
    return BIS_NODE["impulse"]


def normalize(raw_dir: Path) -> Iterator[Question]:
    rows = list(csv.DictReader(open(raw_dir / "quest_raw.csv", encoding="utf-8")))

    for col, (frame, levels, what, raw) in DOSPERT_FRAMES.items():
        for i, item in enumerate(DOSPERT, 1):
            d = _dist(rows, f"{col}_{i}", lambda v: v - 1 if 1 <= v <= 5 else None)
            if not d:
                continue
            flags = ["sensitive"] if i in DOSPERT_SENSITIVE else []
            yield _q(frame.format(s=item), "score", levels, d[0], d[1], f"{col}_{i}", NODE_RISK,
                     meta={"instrument": f"DOSPERT-40 ({what})", "domain": DOSPERT_DOMAIN[i], "scale_raw": raw},
                     flags=flags)

    for i, (a, b) in enumerate(SSSV, 1):
        ka, kb = _slug(a), _slug(b)
        d = _dist(rows, f"SSSV{i:02d}", lambda v: {1: ka, 2: kb}.get(v))
        if not d or ka == kb:
            continue
        flags = (["sensitive"] if i in SSSV_SENSITIVE else []) + (["political"] if i in SSSV_POLITICAL else [])
        yield _q(f'Which of these two statements describes you better: "{a}" or "{b}"?', "choice", {ka: a, kb: b},
                 d[0], d[1], f"SSSV{i:02d}", "self.personality.big_five.extraversion.sociability_energy"
                 if i not in (26, 37, 19) else "self.personality.big_five.openness",
                 meta={"instrument": "Sensation Seeking Scale V (German version), forced choice"}, flags=flags)

    for i, s in enumerate(BIS, 1):
        if s is None:
            continue
        d = _dist(rows, f"BARRATimp{i:02d}", lambda v: v - 1 if 1 <= v <= 4 else None)
        if not d:
            continue
        yield _q(f'How often is this statement true of you: "{s}"', "score", FREQ4, d[0], d[1], f"BARRATimp{i:02d}",
                 _bis_node(i), meta={"instrument": "Barratt Impulsiveness Scale BIS-11 (German version)",
                                     "scale_raw": "1 rarely/never, 2 occasionally, 3 often, 4 almost always/always"})

    general = [("RLRQ_1", "In general, are you a person who is willing to take risks, or do you try to avoid risks?"),
               ("RLRQ_2", "Compared with the general population, are you a person who is willing to take risks, or "
                          "do you try to avoid risks?")]
    general += [(f"RLRQ_{3 + j}", f"How willing are you to take risks {dom}?") for j, dom in enumerate(RLRQ_DOMAINS)]
    general += [(f"RLRQ_{9 + j}", f"Compared with the general population, how willing are you to take risks {dom}?")
                for j, dom in enumerate(RLRQ_DOMAINS)]
    for col, text in general:
        d = _dist(rows, col, lambda v: _bin11(v) if 1 <= v <= 11 else None)
        if d:
            yield _q(text, "score", RISK_LEVELS, d[0], d[1], col, NODE_RISK,
                     meta={"instrument": "SOEP risk-willingness items (0-10)",
                           "level_map": "0-1 -> 0, 2-3 -> 1, 4-6 -> 2, 7-8 -> 3, 9-10 -> 4"})

    d = _dist(rows, "RLRQ_Risiko_Bank_15", lambda v: 6 - v if 1 <= v <= 6 else None)
    if d:
        yield _q(LOTTERY, "score", LOTTERY_LEVELS, d[0], d[1], "RLRQ_Risiko_Bank_15", NODE_RISK,
                 meta={"instrument": "SOEP hypothetical lottery investment", "level_map": "raw 6 (nothing) .. 1 (all)"})
    keys = list(FUND_OPTS)
    d = _dist(rows, "RLRQ_Risiko_Altersvorsorge_16", lambda v: {1: keys[0], 2: keys[1]}.get(v))
    if d:
        yield _q(FUND_TEXT, "choice", FUND_OPTS, d[0], d[1], "RLRQ_Risiko_Altersvorsorge_16", NODE_RISK,
                 meta={"instrument": "pension fund choice (PostFinance fund descriptions)"})

    for j, (text, (k1, k2)) in enumerate(PRI):
        col = f"PRI_{2 * j + 1}"
        d = _dist(rows, col, lambda v: {1: k1, 2: k2}.get(v))
        if d:
            opts = {k1: None, k2: None}
            yield _q(text, "choice", opts, d[0], d[1], col, NODE_RISK,
                     meta={"instrument": "risky everyday scenarios (PRI), choice part only"})
