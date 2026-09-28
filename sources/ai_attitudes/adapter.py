"""An AI's feelings about AI (docs/15 E18): Pew Research Center's 2025 AI survey items, asked of Jev.

Human data: Pew Research Center, American Trends Panel wave 173 (June 9-15, 2025; N=5,023 US adults), topline
"How Americans View AI and Its Impact on People and Society" (September 17, 2025). Shares transcribed from the
topline; "No answer" is dropped and the rest renormalized. Items about government, elections, courts, policing and
religion are left out (politics stays off the map); so are items that only make sense for a person (how often you
use AI, how much you've heard about it, control over AI in your life). Where Pew offered "Not sure", so does Jev.
Pew's terms allow use with attribution.
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "ai_attitudes"
NODE = "self.mind.consciousness_ai.ai_in_daily_life"
LICENSE = "Pew Research Center, American Trends Panel W173 topline (2025); use with attribution per Pew's terms"
URL = "https://www.pewresearch.org/wp-content/uploads/sites/20/2025/09/PS_2025.9.17_AI-and-its-impact_topline.pdf"
POP = "US adults (Pew American Trends Panel, June 2025)"

IMPORTANT = ["Extremely important", "Very important", "Somewhat important", "Not too important", "Not at all important"]
CONCERN = ["Extremely concerned", "Very concerned", "Somewhat concerned", "Not too concerned", "Not at all concerned", "Not sure"]
RATE = ["Very high", "High", "Medium", "Low", "Very low", "Not sure"]
ROLE = ["AI should play a big role", "AI should play a small role", "AI should play no role at all", "Not sure"]
IMPACT = ["AI will make people better at this", "AI will make people worse at this",
          "AI will make people neither better nor worse at this", "Not sure"]

# (id, text, options, shares in option order, n)
ITEMS = [
    ("CNCEXC", "Overall, would you say the increased use of artificial intelligence (AI) in daily life makes you feel...",
     ["More excited than concerned", "More concerned than excited", "Equally concerned and excited"], [10, 50, 38], 5023),
    ("AI_KNOWUSE", "Looking ahead, how important do you think it is for people to understand what artificial intelligence (AI) is?",
     IMPORTANT, [36, 37, 20, 3, 2], 5023),
    ("AI_RECOGIMP", "When it comes to pictures, video and text, how important is it for you to be able to tell if these things "
     "were made by artificial intelligence (AI) or made by people?", IMPORTANT, [46, 30, 17, 4, 2], 5023),
    ("AI_RECOGCONF", "When it comes to pictures, video and text, how confident are you that you would be able to tell if these "
     "things were made by artificial intelligence (AI) or made by people?",
     ["Extremely confident", "Very confident", "Somewhat confident", "Not too confident", "Not at all confident"],
     [3, 9, 35, 35, 18], 5023),
    ("AIASSIST", "How much would you be willing to let artificial intelligence (AI) assist you with your day-to-day tasks and activities?",
     ["A lot", "A little", "Not at all"], [13, 60, 27], 5023),
    ("AI_DEAL", "Thinking about all you have heard and read about artificial intelligence (AI), do you think AI has been...",
     ["Made a bigger deal than it really is", "Made a smaller deal than it really is", "Described about right"], [22, 38, 38], 4831),
    ("AI2HAPPEN_a", "How concerned are you, for society, that people will miss opportunities to improve their lives by being too "
     "reluctant to use artificial intelligence (AI)?", CONCERN, [8, 13, 29, 28, 11, 10], 5023),
    ("AI2HAPPEN_b", "How concerned are you, for society, that people's ability to do things on their own will get worse because "
     "of using artificial intelligence (AI)?", CONCERN, [24, 27, 31, 8, 3, 7], 5023),
    ("AI_BENE", "How would you rate the benefits of artificial intelligence (AI) for society as a whole?", RATE, [6, 19, 41, 12, 7, 15], 5023),
    ("AI_RISK", "How would you rate the risks of artificial intelligence (AI) for society as a whole?", RATE, [25, 32, 26, 4, 1, 11], 5023),
    ("TRSTAIPRS", "Do you think artificial intelligence (AI) will ever get to a point where you would trust it to make "
     "important decisions for you?", ["Yes, it will", "No, it will not", "Not sure"], [13, 54, 33], 5023),
    ("AI_ROLE_b", "How much of a role do you think artificial intelligence (AI) should play in judging whether two people could fall in love?", ROLE, [3, 16, 66, 15], 2505),
    ("AI_ROLE_c", "How much of a role do you think artificial intelligence (AI) should play in forecasting the weather?", ROLE, [35, 39, 12, 14], 2505),
    ("AI_ROLE_e", "How much of a role do you think artificial intelligence (AI) should play in developing new medicines?", ROLE, [31, 35, 18, 16], 2505),
    ("AI_ROLE_i", "How much of a role do you think artificial intelligence (AI) should play in providing mental health support to people?", ROLE, [11, 34, 36, 18], 2518),
    ("AI_ROLE_j", "How much of a role do you think artificial intelligence (AI) should play in searching for financial crimes?", ROLE, [35, 35, 13, 16], 2518),
    ("HUMNIMPCT_a", "How do you think the increased use of artificial intelligence (AI) in society will impact people's ability to think creatively?", IMPACT, [16, 53, 16, 16], 5023),
    ("HUMNIMPCT_b", "How do you think the increased use of artificial intelligence (AI) in society will impact people's ability to make difficult decisions?", IMPACT, [19, 40, 20, 20], 5023),
    ("HUMNIMPCT_c", "How do you think the increased use of artificial intelligence (AI) in society will impact people's ability to solve problems?", IMPACT, [29, 38, 15, 17], 5023),
    ("HUMNIMPCT_d", "How do you think the increased use of artificial intelligence (AI) in society will impact people's ability to form meaningful relationships with other people?", IMPACT, [5, 50, 25, 20], 5023),
    ("PAINTAI", "Imagine you see a painting you really like. Later, you find out the painting was made by artificial intelligence "
     "(AI). Would finding out that the painting was made by AI make you...",
     ["Like the painting more", "Like the painting less", "Not change your views"], [3, 49, 48], 2505),
    ("REPAI", "Imagine you chat online with a customer service representative to deal with an issue. The customer service "
     "representative was helpful. Later, you realize you were talking with an artificial intelligence (AI) chatbot, rather "
     "than a person. Would finding out you were talking with an AI chatbot make you feel...",
     ["Better about your customer experience", "Worse about your customer experience", "Would not change how you felt"], [6, 41, 53], 2505),
    ("SONGAI", "Imagine you listen to a song that you really like. Later, you find out the song was created by artificial "
     "intelligence (AI). Would finding out that the song was created by AI make you...",
     ["Like the song more", "Like the song less", "Not change your views"], [3, 38, 58], 2518),
    ("MEDAI", "Imagine you go to the doctor's office for a health problem. After hearing about your symptoms, the doctor gives "
     "you a promising treatment. Later, you find out the treatment was recommended by artificial intelligence (AI). Would "
     "finding out the treatment was recommended by AI make you feel...",
     ["Better about what your doctor told you", "Worse about what your doctor told you", "Not change your views"], [13, 45, 41], 2518),
    ("NEWSAI", "Imagine you read an article on a news website you visit often. You feel that you learn a lot. Later, you find out "
     "the article was written by artificial intelligence (AI). Would finding out that the article was written by AI make you...",
     ["Feel more confident about what you learned", "Feel less confident about what you learned", "Not change your views"], [7, 56, 36], 2518),
    ("LOANAI", "Imagine you apply for a loan. You follow the steps online and learn that an artificial intelligence (AI) program "
     "will decide whether or not you get the loan. Would finding out that AI will decide whether you get the loan make you...",
     ["Feel more positive about applying", "Feel more negative about applying", "Not change your views"], [8, 57, 35], 2518),
]
GROUPS = {"CNCEXC": "outlook", "AI_BENE": "outlook", "AI_RISK": "outlook", "AI_DEAL": "outlook", "TRSTAIPRS": "trust",
          "AIASSIST": "trust", "AI_KNOWUSE": "detection", "AI_RECOGIMP": "detection", "AI_RECOGCONF": "detection"}


def fetch(raw_dir: Path) -> None:
    """The shares are transcribed in ITEMS; the topline is kept for provenance."""
    if not (raw_dir / "topline.pdf").exists():
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        (raw_dir / "topline.pdf").write_bytes(urllib.request.urlopen(req).read())


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def normalize(raw_dir: Path) -> Iterator[Question]:
    for qid, text, opts, shares, n in ITEMS:
        assert len(opts) == len(shares), qid
        keys = [_key(o) for o in opts]
        tot = sum(shares)
        group = GROUPS.get(qid) or ("role" if qid.startswith("AI_ROLE") else "abilities" if qid.startswith("HUMNIMPCT")
                                    else "found_out" if qid.endswith("AI") else "society")
        yield Question(
            text=text, primitive="choice", hemisphere="self", kind="values", origin="dataset", source=NAME,
            options=dict(zip(keys, opts)), node_hint=NODE, license=LICENSE, source_item_id=qid,
            human=[HumanDist(population=POP, distribution={k: s / tot for k, s in zip(keys, shares)}, n=n,
                             source=f"Pew ATP W173 topline, {qid} (No answer dropped)")],
            meta={"experiment": "ai_attitudes", "item": qid, "group": group, "order": keys})
