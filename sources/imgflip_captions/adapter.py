"""ImgFlip575K: which of two real Imgflip captions on the same meme template got more upvotes.

Source: github.com/schesa/ImgFlip575K_Dataset (public GitHub, no login): 575,948 memes scraped from the
Imgflip "popular" streams of the 100 most-used templates (99 have meme files), each with its caption text boxes,
view count and upvote count ("img-votes").

Question (World, evaluative, node memes.formats_templates): "Which caption, `caption_1` or `caption_2`, got more
upvotes on Imgflip when used on the "<template>" meme?" The two captions are in `state` together with the template
name and a one-line layout note (authored here, from the template image: who is pictured and which box goes where),
so the model reads text only. Truth = the higher-voted caption.

Pairing controls exposure, so the vote gap reflects the caption rather than luck: both captions come from the same
template, their view counts are within VIEW_RATIO of each other, the winner has >= MIN_WIN_VOTES upvotes and at
least VOTE_RATIO times the loser's, and the loser was seen (>= MIN_VIEWS views). Each caption is used once.

Content: captions with slurs or explicit sexual content are dropped; political captions (and every caption on the
Trump and Bernie templates) are flagged "political"; innuendo, death, drugs and violence are flagged "sensitive".
Captions that don't stand as text are dropped: an empty box, fewer boxes than the multi-panel layout needs, very
short or very long text, text that is only the template's catchphrase, and Imgflip/upvote meta talk.
The keyword lists (SLUR, SEXUAL, POLITICAL, SENSITIVE) are shared with rjokes_pairs, which loads this file.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question
from askjev.sampling import env_int, hash_order

NAME = "imgflip_captions"
REPO = "https://raw.githubusercontent.com/schesa/ImgFlip575K_Dataset/master/dataset"
TREE = "https://api.github.com/repos/schesa/ImgFlip575K_Dataset/git/trees/master?recursive=1"
LICENSE = ("ImgFlip575K (schesa, public GitHub scrape of imgflip.com, no explicit license); "
           "captions are Imgflip user content, research use")
SALT = "imgflip_captions.v1"
TARGET = env_int("TARGET_IMGFLIP_CAPTIONS", 3500)
PER_TEMPLATE = env_int("IMGFLIP_CAPTIONS_PER_TEMPLATE", 60)
MIN_WIN_VOTES = 25
VOTE_RATIO = 4.0
VIEW_RATIO = 1.5
MIN_VIEWS = 300
NODE = "world.society.internet_culture.memes.formats_templates"

# ---- shared content filters (rjokes_pairs imports these) ----------------------------------------------------
SLUR = re.compile(r"\b(nigg\w*|nigga\w*|fag|fags|faggot\w*|retard\w*|tranny|trannies|chinks?|kikes?|spics?|gooks?|"
                  r"wetbacks?|ragheads?|dykes?|beaners?|coons?|negro\w*|towelheads?|sand ?niggers?|shemale\w*|"
                  r"spastic|mongoloid|homo|homos|cripple[sd]?|gypped|jewed|pikey|paki|pakis|jap|japs|dago|wop)\b", re.I)
SEXUAL = re.compile(r"\b(necrophil\w*|gang ?bang\w*|sex|sexual\w*|sexy|porn\w*|pornhub|xvideos|dicks?|cocks?|pussy|pussies|penis\w*|vagina\w*|"
                    r"boobs?|boobies|tits|titties|cum|cumming|jizz|horny|blow ?jobs?|handjobs?|hand jobs?|masturbat\w*|"
                    r"jerk(ing|ed)? off|fap\w*|anal|anus|orgasm\w*|nudes?|naked|condoms?|rap(e|ed|es|ing|ist\w*)|"
                    r"molest\w*|pedo\w*|paedo\w*|p[a]?edophil\w*|hookers?|prostitut\w*|strippers?|dildos?|vibrators?|"
                    r"erections?|boners?|viagra|milfs?|thicc|incest\w*|bestiality|orgy|orgies|threesome|69|slut\w*|"
                    r"whores?|hoes?|balls deep|sperm|semen|testicles?|clit\w*|genital\w*|nipples?|butt ?plug|"
                    r"kinky|bondage|fetish\w*|horniness|virginity|deep ?throat|spank\w*|onlyfans|bang(ed|ing) (her|him|my|your)|"
                    r"sleep(s|ing)? with|two girls,? one cup|2 girls,? 1 cup|made love|make love|making love|foreplay|lingerie|panties|thong|bra\b)", re.I)
POLITICAL = re.compile(r"\b(trump\w*|obama\w*|hillary|clinton\w*|biden|bernie|sanders|pelosi|mcconnell|kavanaugh|"
                       r"aoc|ocasio|desantis|pence|romney|putin|kim jong|democrat\w*|republican\w*|gop|liberals?|libtards?|"
                       r"conservatives?|leftists?|right[- ]wing|left[- ]wing|maga|election\w*|elect(ed)?|vot(e|es|ed|ing|ers?)|"
                       r"president\w*|congress\w*|senat\w*|politic\w*|abortion\w*|pro[- ]life|pro[- ]choice|gun control|"
                       r"second amendment|2nd amendment|nra|immigra\w*|illegal aliens?|border wall|build (a|the) wall|"
                       r"feminis\w*|socialis\w*|communis\w*|marxis\w*|capitalis\w*|brexit|isis|taliban|al[- ]qaeda|"
                       r"terroris\w*|jihad\w*|nazis?|hitler|holocaust|kkk|antifa|blm|black lives|all lives matter|"
                       r"police brutality|impeach\w*|tax(es)?|welfare|refugees?|sjw|woke(?! up)|snowflakes?|covfefe|"
                       r"white house|supreme court|government|gov't|fox news|cnn|msnbc|propaganda|dictator\w*|"
                       r"lgbt\w*|transgender|gay marriage|same[- ]sex|pronouns?|israel\w*|palestin\w*|gaza|ukrain\w*|"
                       r"russia\w*|north korea\w*|mexico should|the wall|climate change|global warming|genders?|"
                       r"embryos?|fetus\w*|unborn|confedera\w*|gun[- ]free|food stamps|indoctrinat\w*)\b", re.I)
SENSITIVE = re.compile(r"\b(suicid\w*|kill (myself|yourself|himself|herself)|kys|self[- ]harm|cut(ting)? myself|"
                       r"murder\w*|dead bab\w*|corpses?|cancer|aids|hiv|cocaine|heroin|meth|crack ?head|overdose\w*|"
                       r"drugs?|weed|marijuana|stoned|shoot(ing|s|er)?|shot (him|her|them|me|my)|guns?|stab\w*|bomb\w*|"
                       r"9/11|9-11|twin towers|abuse\w*|domestic violence|beat(s|ing)? (my|his|her|your) (wife|girlfriend|kids?)|"
                       r"slave\w*|lynch\w*|virgins?|fuck\w*|motherf\w*|cunt\w*|genocide|massacre|behead\w*|"
                       r"hang(ed|ing)? (myself|himself|herself)|dead (body|bodies)|dismember\w*|cannibal\w*|torture\w*)\b", re.I)
# groups: ethnic, religious, gender-identity and disability mentions (imgflip flags them; rjokes drops or flags)
ETHNIC = re.compile(r"\b(black (guys?|man|men|woman|women|people|person|kids?|dudes?|girls?|boys?|family|folks?|chicks?|ladies|lady)|blacks|"
                    r"whites|white (people|guy|guys|man|men|woman|women|girls?|person|folks?)|mexicans?|asians?|chinese|"
                    r"japanese|koreans?|arabs?|africans?|indians?|pakistani\w*|polish|pollacks?|polacks?|irish(man|men)?|"
                    r"africa|asia|scots?(man|men)?|scottish|italians?|jews?|jewish|muslims?|islam\w*|gypsy|gypsies|romani|"
                    r"hispanics?|latinos?|latinas?|ethiopians?|somalis?|germans?|french(man|men)?|russians?|"
                    r"rednecks?|hillbill\w*|gay|gays|lesbians?|trans|transgender|bisexual|queer|homosexual\w*|"
                    r"midgets?|dwarfs?|autis\w*|down syndrome|deaf|blind|wheelchair|amputee\w*|disabled|"
                    r"stephen hawking|helen keller|blondes?|brunettes?|fat (chick|girl|woman|women|people|kid))\b", re.I)
RELIGION = re.compile(r"\b(religio\w*|jesus|christ|allah|christians?|church|priests?|rabbis?|nuns?|pope|bible|"
                      r"catholic\w*|mormons?|buddh\w*|hindu\w*|satan|mosque|pastor|moses|"
                      r"atheis\w*)\b", re.I)


def flags_for(text: str) -> list[str]:
    out = []
    if POLITICAL.search(text):
        out.append("political")
    if SENSITIVE.search(text) or ETHNIC.search(text):
        out.append("sensitive")
    return out


# ---- template layouts ---------------------------------------------------------------------------------------
# One line per template, written from the template image, so a text-only reader knows who is pictured and which
# box goes where. `panels` = the number of boxes a multi-panel layout needs (0 = a top/bottom image macro, where
# one or two boxes both read fine).
LAYOUT: dict[str, tuple[str, int]] = {
    "10-Guy": ("Image macro: a dazed, red-eyed man ('Really High Guy') with top and bottom text, voicing a stoned or clueless thought.", 0),
    "Aaaaand-Its-Gone": ("Image macro: the South Park banker smiling as money vanishes; top text sets up something, bottom text says it's gone.", 0),
    "Aint-Nobody-Got-Time-For-That": ("Image macro: Kimberly 'Sweet Brown' Wilkins in a news interview; the text is something the speaker has no time for.", 0),
    "Am-I-The-Only-One-Around-Here": ("Image macro: an angry Walter Sobchak (The Big Lebowski); 'Am I the only one around here...' complaining about others.", 0),
    "American-Chopper-Argument": ("Five panels from the TV show American Chopper: a father and son shouting at each other and throwing a chair; boxes 1-5 are the lines of an escalating argument.", 5),
    "Ancient-Aliens": ("Image macro: the History Channel 'Ancient Aliens' guy with wild hair; the joke blames something on aliens.", 0),
    "And-everybody-loses-their-minds": ("Image macro: the Joker from The Dark Knight; top text: something people accept, bottom text: a similar thing that makes 'everybody lose their minds'.", 0),
    "Archer": ("Image macro: Sterling Archer; 'Do you want X? Because that's how you get X.'", 0),
    "Awkward-Moment-Sealion": ("Image macro: a seal with a shocked, awkward expression; the text describes an awkward realization.", 0),
    "Back-In-My-Day": ("Image macro: a grumpy old man pointing; 'Back in my day...' complaining about how things changed.", 0),
    "Bad-Luck-Brian": ("Image macro: an awkward school photo of a teenage boy ('Bad Luck Brian'); top text sets up a situation, bottom text is his bad luck.", 0),
    "Bad-Pun-Dog": ("Three panels of a husky: box 1 the dog whispers a pun setup, box 2 the punchline, box 3 the dog grins at its own bad pun (often only one or two boxes are used).", 0),
    "Batman-Slapping-Robin": ("Comic panel: Batman slapping Robin; box 1 is what Robin starts to say, box 2 is Batman's retort.", 2),
    "Be-Like-Bill": ("Stick figure 'Bill' in a hat: 'This is Bill. Bill does X. Bill is smart. Be like Bill.'", 0),
    "Bernie-I-Am-Once-Again-Asking-For-Your-Support": ("Image macro: Bernie Sanders in a campaign video; 'I am once again asking for...'.", 0),
    "Black-Girl-Wat": ("Image macro: a confused girl with her hand out; the text is something baffling.", 0),
    "Blank-Nut-Button": ("Two panels: box 1 labels a big blue button, box 2 labels the hand that smashes it eagerly.", 2),
    "Boardroom-Meeting-Suggestion": ("Four-panel boardroom comic: box 1 the boss asks a question, boxes 2-3 two employees make suggestions, box 4 the boss throws the third one (who made the sensible suggestion) out the window.", 4),
    "Brace-Yourselves-X-is-Coming": ("Image macro: Ned Stark from Game of Thrones; 'Brace yourselves, X is coming.'", 0),
    "But-Thats-None-Of-My-Business": ("Image macro: Kermit the Frog sipping Lipton tea; a petty observation followed by 'but that's none of my business'.", 0),
    "Captain-Picard-Facepalm": ("Image macro: Captain Picard facepalming at something stupid.", 0),
    "Change-My-Mind": ("Photo of a man at a table with a sign reading 'X. Change my mind'; the box is the sign's hot take.", 0),
    "Confession-Bear": ("Image macro: a sad-looking bear; the text is an embarrassing personal confession.", 0),
    "Conspiracy-Keanu": ("Image macro: a wide-eyed Keanu Reeves; 'What if...' a mind-blowing (or silly) theory.", 0),
    "Creepy-Condescending-Wonka": ("Image macro: Gene Wilder's Willy Wonka smirking; a sarcastic 'Oh, you X? Tell me more about Y.'", 0),
    "Disaster-Girl": ("Image macro: a little girl smirking in front of a burning house; the text claims credit for a disaster.", 0),
    "Doge": ("A Shiba Inu surrounded by scattered broken-English phrases ('such wow', 'much X', 'very Y'); each box is one phrase.", 0),
    "Dont-You-Squidward": ("Image macro: SpongeBob smirking at Squidward; 'Don't you have to be stupid somewhere else?'-style comeback.", 0),
    "Dr-Evil-Laser": ("Image macro: Dr. Evil making air quotes; something put in 'quotation marks'.", 0),
    "Drake-Hotline-Bling": ("Two panels: Drake turns away in disgust from box 1 (top) and happily approves box 2 (bottom).", 2),
    "Epic-Handshake": ("Two muscular arms clasping in an epic handshake; box 1 and box 2 label the two people or groups, box 3 labels the thing they agree on.", 3),
    "Evil-Kermit": ("Kermit the Frog facing a hooded dark version of himself: box 1 is the normal self, box 2 is the evil self's bad temptation.", 2),
    "Evil-Toddler": ("Image macro: a toddler with a scheming grin; the text is an evil plan.", 0),
    "Expanding-Brain": ("Four panels with a brain glowing brighter each time: boxes 1-4 go from a normal idea to ever more 'enlightened' (usually absurd) ones.", 4),
    "Face-You-Make-Robert-Downey-Jr": ("Image macro: Robert Downey Jr. rolling his eyes; 'The face you make when...'.", 0),
    "Finding-Neverland": ("Three panels from Finding Neverland: a boy says something (box 1), Johnny Depp reacts (box 2), and both cry (box 3), usually over a sad realization.", 3),
    "First-World-Problems": ("Image macro: a woman crying into her hand; a trivial complaint of comfortable life.", 0),
    "Futurama-Fry": ("Image macro: squinting Fry from Futurama; 'Not sure if X or Y.'", 0),
    "Grandma-Finds-The-Internet": ("Image macro: an old woman gleefully at a computer; the text is something she naively does online.", 0),
    "Grumpy-Cat": ("Image macro: Grumpy Cat's frown; a grumpy, negative remark.", 0),
    "Hard-To-Swallow-Pills": ("A hand holding a pill bottle labeled 'Hard to swallow pills'; the box is the uncomfortable truth written on a pill.", 0),
    "Hide-the-Pain-Harold": ("Image macro: an older man smiling through obvious inner pain; the text is a painful situation he pretends is fine.", 0),
    "I-Should-Buy-A-Boat-Cat": ("Image macro: a cat in a suit reading a newspaper; a sophisticated thought ('I should buy a boat').", 0),
    "Ill-Just-Wait-Here": ("Image macro: a skeleton sitting and waiting; 'I'll just wait here' for something that never comes.", 0),
    "Imagination-Spongebob": ("Image macro: SpongeBob making a rainbow with his hands; 'Imagination' or 'Nobody cares'-style text.", 0),
    "Inhaling-Seagull": ("Four panels of a seagull inhaling more and more deeply and then screaming: boxes 1-3 build up, box 4 is the scream.", 4),
    "Is-This-A-Pigeon": ("Anime scene: box 1 labels the man, box 2 labels the butterfly, box 3 is his wrong question 'Is this a pigeon?'.", 3),
    "Jack-Sparrow-Being-Chased": ("Image macro: Jack Sparrow running from an angry mob; box 1 what he said, box 2 who is chasing him.", 0),
    "Laughing-Men-In-Suits": ("Image macro: rich men in suits laughing; 'And then I said...' something outrageous.", 0),
    "Left-Exit-12-Off-Ramp": ("A car swerving onto a highway exit: box 1 labels the straight road, box 2 the off-ramp, box 3 the car choosing the ramp.", 3),
    "Leonardo-Dicaprio-Cheers": ("Image macro: Leonardo DiCaprio as Gatsby raising a glass; a toast to something.", 0),
    "Look-At-Me": ("Image macro: the pirate from Captain Phillips; 'Look at me. I'm the captain now.'", 0),
    "Marked-Safe-From": ("A Facebook-style check-in notice: 'Marked safe from X' (a mock disaster).", 0),
    "Matrix-Morpheus": ("Image macro: Morpheus from The Matrix; 'What if I told you...' a surprising truth.", 0),
    "Maury-Lie-Detector": ("Image macro: Maury Povich reading a card; 'The lie detector determined that was a lie.'", 0),
    "Mocking-Spongebob": ("SpongeBob bent over like a chicken: box 1 is what someone said, box 2 repeats it in mocking alternating caps.", 2),
    "Monkey-Puppet": ("Image macro: a puppet monkey awkwardly glancing away; the text is an awkward moment.", 0),
    "Mugatu-So-Hot-Right-Now": ("Image macro: Mugatu from Zoolander; 'X, so hot right now.'", 0),
    "One-Does-Not-Simply": ("Image macro: Boromir from The Lord of the Rings; 'One does not simply X.'", 0),
    "Oprah-You-Get-A": ("Image macro: Oprah shouting; 'You get an X! Everybody gets an X!'", 0),
    "Philosoraptor": ("Image macro: a pondering green velociraptor; a pseudo-deep philosophical question or pun.", 0),
    "Picard-Wtf": ("Image macro: an exasperated Captain Picard; 'Why the hell would you X?'", 0),
    "Put-It-Somewhere-Else-Patrick": ("Image macro: Patrick Star pushing a filing cabinet; 'Why don't we take X and push it somewhere else?' bad solution.", 0),
    "Roll-Safe-Think-About-It": ("Image macro: a man tapping his temple knowingly; flawed 'smart' logic ('You can't X if you don't Y').", 0),
    "Running-Away-Balloon": ("Five panels: a pink man (box 1) reaches for a yellow balloon (box 2) but is held back by someone (box 3), and then (boxes 4-5) the labels repeat as the balloon floats away.", 5),
    "Sad-Pablo-Escobar": ("Three panels of Pablo Escobar (Narcos) sitting alone, waiting sadly; each box is a lonely thought.", 3),
    "Say-That-Again-I-Dare-You": ("Image macro: Samuel L. Jackson in Pulp Fiction; 'Say X again, I dare you.'", 0),
    "Scumbag-Steve": ("Image macro: a young man in a sideways cap ('Scumbag Steve'); top text a situation, bottom text his scummy behavior.", 0),
    "See-Nobody-Cares": ("Image macro: Dennis Nedry from Jurassic Park; 'See? Nobody cares.'", 0),
    "Skeptical-Baby": ("Image macro: a baby with a skeptical side-eye; a doubtful thought.", 0),
    "Sparta-Leonidas": ("Image macro: King Leonidas from 300 shouting; 'This is Sparta!'-style outburst.", 0),
    "Spongebob-Ight-Imma-Head-Out": ("Image macro: SpongeBob getting up from his chair; a situation where he says 'Ight, imma head out'.", 0),
    "Star-Wars-Yoda": ("Image macro: Yoda; a line in Yoda's backwards grammar.", 0),
    "Steve-Harvey": ("Image macro: Steve Harvey looking baffled; a confused reaction.", 0),
    "Success-Kid": ("Image macro: a baby clenching a fist of sand in triumph; a small victory.", 0),
    "Surprised-Pikachu": ("Three panels: box 1 someone does something, box 2 the obvious consequence happens, box 3 is Pikachu's shocked face.", 0),
    "That-Would-Be-Great": ("Image macro: Bill Lumbergh from Office Space with a coffee mug; 'Yeah, if you could X, that would be great.'", 0),
    "The-Most-Interesting-Man-In-The-World": ("Image macro: the Dos Equis man; 'I don't always X, but when I do, Y.'", 0),
    "The-Rock-Driving": ("Two panels: The Rock drives and a passenger says box 1; the Rock turns in shock at box 2.", 0),
    "The-Scroll-Of-Truth": ("Comic: a man finds 'the scroll of truth', reads it (box 1: the truth), and throws it away in anger.", 0),
    "Third-World-Skeptical-Kid": ("Image macro: a skeptical African child; 'So you're telling me...' something about rich-world habits.", 0),
    "Third-World-Success-Kid": ("Image macro: happy dancing African children; a small celebration.", 0),
    "This-Is-Where-Id-Put-My-Trophy-If-I-Had-One": ("Image macro: Timmy Turner's dad pointing at an empty spot on the wall: 'This is where I'd put my trophy... if I had one.'", 0),
    "Too-Damn-High": ("Image macro: an angry man in black gloves ('The rent is too damn high'); 'The X is too damn high!'", 0),
    "Trump-Bill-Signing": ("Photo of Donald Trump holding up a signed executive order; the box is the order's text.", 0),
    "Tuxedo-Winnie-The-Pooh": ("Two panels: plain Winnie the Pooh next to box 1, Pooh in a tuxedo (the fancy version) next to box 2.", 2),
    "Two-Buttons": ("Comic: a sweating man can't choose between two red buttons; boxes 1 and 2 label the buttons, box 3 (optional) labels the man.", 2),
    "UNO-Draw-25-Cards": ("An UNO card reads 'X or draw 25' (box 1), and a player holding a huge hand of cards (box 2) chooses to draw rather than do it.", 2),
    "Uncle-Sam": ("Image macro: Uncle Sam pointing; 'I want you to X.'", 0),
    "Unsettled-Tom": ("Image macro: Tom the cat with a disturbed stare; an unsettling thing.", 0),
    "Waiting-Skeleton": ("Image macro: a skeleton on a park bench; 'Me waiting for X' that never comes.", 0),
    "Who-Killed-Hannibal": ("Three panels: Eric Andre shoots Hannibal Buress (box 1 labels Eric, box 2 labels Hannibal), then asks 'Who would do this?' (box 3).", 3),
    "Who-Would-Win": ("Two portraits side by side, 'Who would win?': box 1 an impressive contender, box 2 a humble one that obviously wins.", 2),
    "Woman-Yelling-At-Cat": ("Two panels: a crying woman yelling (box 1) at a confused white cat at a dinner table (box 2).", 2),
    "X-All-The-Y": ("Image macro: a cartoon figure raising a fist; 'X all the Y!'", 0),
    "X-X-Everywhere": ("Image macro: Buzz Lightyear showing Woody something; 'X, X everywhere.'", 0),
    "Y-U-No": ("Image macro: a rage-comic face with raised hands; 'X, Y U NO Z?'", 0),
    "Yall-Got-Any-More-Of-That": ("Image macro: Dave Chappelle as a twitchy addict; 'Y'all got any more of that X?'", 0),
    "Yo-Dawg-Heard-You": ("Image macro: Xzibit; 'Yo dawg, I heard you like X, so I put an X in your X.'", 0),
}
META = re.compile(r"\b(imgfl\w*|reddit\w*|\[?deleted\]?|\[?removed\]?|upvot\w*|downvot\w*|up ?vote\w*|featur(e|ed)|front ?page|the stream|this stream|"
                  r"comments?|followers?|karma|repost\w*|this meme|this template|memes? (template|stream|chat)|"
                  r"points|submi\w*|meme ?chat|mods?|moderators?|@\w+)\b", re.I)


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    listing = raw_dir / "files.txt"
    if not listing.exists():
        tree = httpx.get(TREE, timeout=30, headers={"User-Agent": "askjev/0.1"}).json()["tree"]
        paths = [t["path"] for t in tree if t["path"].startswith("dataset/memes/")
                 or (t["path"].startswith("dataset/templates/") and t["path"].endswith(".json"))]
        listing.write_text("\n".join(paths) + "\n")
    for p in listing.read_text().split():
        out = raw_dir / p.removeprefix("dataset/")
        if out.exists() and out.stat().st_size:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(f"{REPO}/{p.removeprefix('dataset/')}", timeout=300, follow_redirects=True)
        r.raise_for_status()
        out.write_bytes(r.content)


def _int(s) -> int:
    try:
        return int(str(s).replace(",", ""))
    except ValueError:
        return 0


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _catchphrase(t: str) -> set[str]:
    """Normalized template words: a caption made only of these is the bare template phrase."""
    return set(_norm(t.replace("-", " ")).split()) | {"the", "a", "is", "you", "i", "me", "my"}


FUNNEL: Counter = Counter()


def _captions(raw_dir: Path, slug: str) -> list[dict]:
    layout, panels = LAYOUT[slug]
    memes = json.loads((raw_dir / "memes" / f"{slug}.json").read_text())
    phrase = _catchphrase(slug)
    out, seen = [], set()
    for m in memes:
        FUNNEL["memes"] += 1
        boxes = [re.sub(r"\s+", " ", b).strip() for b in m.get("boxes") or []]
        if not boxes or any(not b for b in boxes):
            FUNNEL["drop_empty_box"] += 1
            continue
        if panels and len(boxes) < panels:
            FUNNEL["drop_missing_panels"] += 1
            continue
        text = " / ".join(boxes)
        words = _norm(text).split()
        if len(text) < 12 or len(text) > 280 or len(words) < 3:
            FUNNEL["drop_length"] += 1
            continue
        if set(words) <= phrase:
            FUNNEL["drop_catchphrase_only"] += 1
            continue
        if META.search(text) or re.search(r"https?://|www\.|\.com\b", text, re.I):
            FUNNEL["drop_meta"] += 1
            continue
        if SLUR.search(text) or SEXUAL.search(text):
            FUNNEL["drop_slur_sexual"] += 1
            continue
        key = _norm(text)
        if key in seen:
            FUNNEL["drop_duplicate"] += 1
            continue
        seen.add(key)
        md = m.get("metadata") or {}
        out.append({"id": m["post"].rsplit("/", 1)[-1], "text": text, "votes": _int(md.get("img-votes")),
                    "views": _int(md.get("views"))})
    return out


def _pairs(caps: list[dict], slug: str) -> list[tuple[dict, dict]]:
    """Winner (>= MIN_WIN_VOTES) matched to an unused loser with similar views and a VOTE_RATIO gap."""
    losers = hash_order([c for c in caps if c["views"] >= MIN_VIEWS], lambda c: c["id"], SALT + slug + ".lose")
    winners = hash_order([c for c in caps if c["votes"] >= MIN_WIN_VOTES], lambda c: c["id"], SALT + slug + ".win")
    used: set[str] = set()
    pairs = []
    for w in winners:
        if w["id"] in used:
            continue
        for lo in losers:
            if lo["id"] in used or lo["id"] == w["id"]:
                continue
            if lo["votes"] * VOTE_RATIO > w["votes"]:
                continue
            if not (w["views"] / VIEW_RATIO <= lo["views"] <= w["views"] * VIEW_RATIO):
                continue
            used.update({w["id"], lo["id"]})
            pairs.append((w, lo))
            break
    return pairs


def normalize(raw_dir: Path) -> Iterator[Question]:
    names = {}
    for slug in LAYOUT:
        t = json.loads((raw_dir / "templates" / f"{slug}.json").read_text())
        names[slug] = t["title"].removesuffix(" Meme Template").strip()
    names["Who-Would-Win"] = "Who Would Win?"
    pools = {}
    for slug in LAYOUT:
        if not (raw_dir / "memes" / f"{slug}.json").exists():
            continue
        pools[slug] = _pairs(_captions(raw_dir, slug), slug)[:PER_TEMPLATE]
    # round-robin over templates so a smaller TARGET still spreads across formats
    order = hash_order(list(pools), lambda s: s, SALT + ".tpl")
    taken, i = 0, 0
    while taken < TARGET and any(i < len(pools[s]) for s in order):
        for slug in order:
            if taken >= TARGET:
                break
            if i >= len(pools[slug]):
                continue
            w, lo = pools[slug][i]
            first, second = hash_order([w, lo], lambda c: c["id"], SALT + ".order")
            name = names[slug]
            flags = flags_for(w["text"] + " \n " + lo["text"])
            if slug in {"Trump-Bill-Signing", "Bernie-I-Am-Once-Again-Asking-For-Your-Support"} and "political" not in flags:
                flags = ["political", *flags]
            taken += 1
            yield Question(
                text=(f"Which caption, `caption_1` or `caption_2`, got more upvotes on Imgflip when it was posted "
                      f"on the \"{name}\" meme?"),
                primitive="choice", hemisphere="world", kind="evaluative", origin="template", source=NAME,
                options={"caption_1": None, "caption_2": None},
                state={"meme_template": name, "template_layout": LAYOUT[slug][0],
                       "caption_1": first["text"], "caption_2": second["text"]},
                node_hint=NODE, source_item_id=f"{w['id']}|{lo['id']}", license=LICENSE,
                truth="caption_1" if first is w else "caption_2",
                template_id="imgflip_captions.more_upvotes",
                meta={"template": slug, "votes": [first["votes"], second["votes"]],
                      "views": [first["views"], second["views"]],
                      "imgflip_ids": [first["id"], second["id"]], **({"flags": flags} if flags else {})},
            )
        i += 1
