"""USCIS naturalization civics test (2025 version, 128 questions; plus the 2008 version's 100 where it adds new items).

The official list gives each question with its accepted answers, not answer choices. Each kept item becomes a
World factual Choice: one official answer as the correct option, three distractors authored here from the other
questions' official answer lists where possible (e.g. "Makes the federal budget", a Congress power, as a wrong
answer to "a power of the president"), otherwise clearly wrong but plausible alternatives. "Name one/two/three X"
is asked as "Which of these is ...". US federal government work: public domain.

Skipped: anything whose answer varies or names a current official (your senator, the President now, the Speaker,
the Chief Justice, your governor), anything partisan (the two parties, the President's party), numbers, counts and
dates (how many senators, term lengths, voting age, "When was..."), and trivial or policy-flavored items (civic
participation lists, why pay taxes, Selective Service, the 9/11 and post-9/11 items, the causes of the Civil War).
Each correct answer is checked against the downloaded official text of its question (the anchor), so a typo or a
changed official answer fails loudly.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import Question

NAME = "uscis_civics"
LICENSE = "Public domain (US federal government work, USCIS)"
BASE = "https://www.uscis.gov/sites/default/files/document/questions-and-answers/"
FILES = {"2025": "2025-Civics-Test-128-Questions-and-Answers.pdf", "2008": "100q.pdf"}

GOV = "world.society.politics_government.government"
CON = "world.society.crime_law.constitution"
REV = "world.history.early_modern.american_revolution"
NAM = "world.history.history_of_north_america"
USA = "world.places.countries.united_states"
HOL = "world.society.holidays_traditions.festival"
WW1, WW2, COLD = "world.history.modern.world_war_i", "world.history.modern.world_war_ii", "world.history.modern.cold_war"

# (version, number, text, correct, distractors, node, anchor or None = correct)
ITEMS = [
    ("2025", 1, "What is the form of government of the United States?", "Constitution-based federal republic",
     ["Constitutional monarchy", "Direct democracy without representatives", "One-party state"], GOV, None),
    ("2025", 2, "What is the supreme law of the land in the United States?", "U.S. Constitution",
     ["Declaration of Independence", "Articles of Confederation", "Federalist Papers"], CON, None),
    ("2025", 3, "Which of these is one thing the U.S. Constitution does?", "Defines powers of government",
     ["Declares independence from Britain", "Sets the federal budget each year", "Appoints federal judges"], CON, None),
    ("2025", 4, "The U.S. Constitution starts with the words \"We the People.\" What does \"We the People\" mean?",
     "Popular sovereignty", ["Checks and balances", "Separation of powers", "Limited government"], CON, None),
    ("2025", 5, "How are changes made to the U.S. Constitution?", "Amendments",
     ["Executive orders", "Supreme Court rulings", "Presidential vetoes"], CON, None),
    ("2025", 6, "What does the U.S. Bill of Rights protect?", "The basic rights of Americans",
     ["The powers of the states over Congress", "The authority of the president", "The structure of Congress"],
     CON, None),
    ("2025", 8, "Why is the U.S. Declaration of Independence important?", "It says America is free from British control.",
     ["It set up the three branches of government.", "It created the Bill of Rights.",
      "It ended slavery in the United States."], REV, None),
    ("2025", 9, "What founding document said the American colonies were free from Britain?",
     "Declaration of Independence", ["U.S. Constitution", "Articles of Confederation", "Mayflower Compact"], REV, None),
    ("2025", 10, "Which of these is an important idea from the U.S. Declaration of Independence and the U.S. Constitution?",
     "Natural rights", ["Divine right of kings", "Hereditary nobility", "An official state church"], CON, None),
    ("2025", 11, "The words \"Life, Liberty, and the pursuit of Happiness\" are in what American founding document?",
     "Declaration of Independence", ["U.S. Constitution", "Bill of Rights", "Federalist Papers"], REV, None),
    ("2025", 12, "What is the economic system of the United States?", "Capitalism",
     ["Socialism", "Communism", "Feudalism"], GOV, None),
    ("2025", 13, "In the United States, what is the rule of law?", "No one is above the law.",
     ["The president decides what the law is.", "Only citizens must follow the law.",
      "Each state may ignore federal law."], CON, None),
    ("2025", 14, "Which of these documents influenced the U.S. Constitution?", "Articles of Confederation",
     ["Emancipation Proclamation", "Gettysburg Address", "Monroe Doctrine"], CON, None),
    ("2025", 15, "There are three branches of the U.S. government. Why?", "So one part does not become too powerful",
     ["So laws can be passed faster", "So each region of the country has its own branch",
      "So the president can manage the courts"], GOV, None),
    ("2025", 16, "What are the three branches of the U.S. government?", "Legislative, executive, and judicial",
     ["Federal, state, and local", "Senate, House, and Cabinet", "Army, Navy, and Air Force"], GOV, None),
    ("2025", 17, "The President of the United States is in charge of which branch of government?", "Executive branch",
     ["Legislative branch", "Judicial branch"], GOV, None),
    ("2025", 18, "What part of the U.S. federal government writes laws?", "U.S. Congress",
     ["The President", "The Supreme Court", "The Cabinet"], GOV, None),
    ("2025", 19, "What are the two parts of the U.S. Congress?", "Senate and House of Representatives",
     ["Senate and Supreme Court", "House of Representatives and Cabinet", "President and Vice President"], GOV, None),
    ("2025", 20, "Which of these is a power of the U.S. Congress?", "Declares war",
     ["Vetoes bills", "Appoints federal judges", "Decides if a law goes against the Constitution"], GOV, None),
    ("2025", 26, "Why do U.S. representatives serve shorter terms than U.S. senators?",
     "To more closely follow public opinion",
     ["To save money on salaries", "Because the Constitution limits them to one term",
      "Because senators are appointed by governors"], GOV, None),
    ("2025", 28, "Why does each U.S. state have two senators?", "Equal representation for small states",
     ["To match each state's population", "To give larger states more power",
      "Because each state has two congressional districts"], GOV, None),
    ("2025", 31, "Who does a U.S. senator represent?", "People of their state",
     ["People of one congressional district", "The president's administration", "The state governor"], GOV, None),
    ("2025", 32, "Who elects U.S. senators?", "Citizens from their state",
     ["The state legislature", "The House of Representatives", "The Electoral College"], GOV, None),
    ("2025", 33, "Who does a member of the U.S. House of Representatives represent?", "People in their district",
     ["People of the whole state", "All citizens of the United States", "The state governor"], GOV, None),
    ("2025", 34, "Who elects members of the U.S. House of Representatives?", "Citizens from their congressional district",
     ["The state legislature", "The U.S. Senate", "The Electoral College"], GOV, None),
    ("2025", 35, "Some U.S. states have more representatives in Congress than other states. Why?",
     "Because of the state's population",
     ["Because of the state's land area", "Because of the state's age", "Because of the state's wealth"], GOV, None),
    ("2025", 37, "The President of the United States can serve only two terms. Why?",
     "To keep the president from becoming too powerful",
     ["To save money on elections", "Because the Supreme Court requires it",
      "Because presidents must retire at seventy"], GOV, None),
    ("2025", 40, "If the President of the United States can no longer serve, who becomes president?", "The Vice President",
     ["The Speaker of the House", "The Chief Justice", "The Secretary of State"], GOV, None),
    ("2025", 41, "Which of these is a power of the U.S. president?", "Vetoes bills",
     ["Writes laws", "Declares war", "Makes the federal budget"], GOV, None),
    ("2025", 42, "Who is Commander in Chief of the U.S. military?", "The President",
     ["The Secretary of Defense", "The Vice President", "The Speaker of the House"], GOV, None),
    ("2025", 43, "In the United States, who signs bills to become laws?", "The President",
     ["The Chief Justice", "The Speaker of the House", "The Vice President"], GOV, None),
    ("2025", 44, "In the United States, who vetoes bills?", "The President",
     ["The Supreme Court", "The Vice President", "The Speaker of the House"], GOV, None),
    ("2025", 45, "In the United States, who appoints federal judges?", "The President",
     ["The Senate", "The Chief Justice", "The voters"], GOV, None),
    ("2025", 46, "Which of these is part of the U.S. executive branch?", "Cabinet",
     ["Supreme Court", "Senate", "House of Representatives"], GOV, None),
    ("2025", 47, "What does the U.S. President's Cabinet do?", "Advises the President",
     ["Writes federal laws", "Decides court cases", "Elects the president"], GOV, None),
    ("2025", 48, "Which of these is a U.S. Cabinet-level position?", "Secretary of the Treasury",
     ["Speaker of the House", "Chief Justice of the United States", "Senate Majority Leader"], GOV, None),
    ("2025", 49, "Why is the U.S. Electoral College important?", "It decides who is elected president.",
     ["It confirms Supreme Court justices.", "It writes the federal budget.",
      "It approves amendments to the Constitution."], GOV, None),
    ("2025", 50, "What is one part of the U.S. judicial branch?", "Supreme Court",
     ["Cabinet", "Senate", "Department of Homeland Security"], GOV, None),
    ("2025", 51, "What does the U.S. judicial branch do?", "Decides if a law goes against the U.S. Constitution",
     ["Writes laws", "Vetoes bills", "Enforces laws"], GOV, None),
    ("2025", 52, "What is the highest court in the United States?", "Supreme Court",
     ["Federal Court of Appeals", "District Court of Columbia", "Court of International Trade"], GOV, None),
    ("2025", 55, "How long do U.S. Supreme Court justices serve?", "For life",
     ["Four years", "Six years", "Until the next president takes office"], GOV, None),
    ("2025", 56, "U.S. Supreme Court justices serve for life. Why?", "To be independent of politics",
     ["To reward long legal careers", "Because they are elected by the people",
      "To save money on appointments"], GOV, None),
    ("2025", 58, "Which of these is a power that is only for the U.S. federal government?", "Print paper money",
     ["Provide schooling and education", "Give a driver's license", "Approve zoning and land use"], GOV, None),
    ("2025", 59, "Which of these is a power that is only for the U.S. states?", "Give a driver's license",
     ["Print paper money", "Declare war", "Make treaties"], GOV, None),
    ("2025", 60, "What is the purpose of the 10th Amendment to the U.S. Constitution?",
     "Powers not given to the federal government belong to the states or to the people.",
     ["It guarantees freedom of speech.", "It abolishes slavery.", "It gives women the right to vote."], CON, None),
    ("2025", 63, "Which of these describes one of the amendments to the U.S. Constitution about who can vote?",
     "You don't have to pay a poll tax to vote.",
     ["Only property owners can vote.", "You must pass a literacy test to vote.", "Only men can vote."], CON, None),
    ("2025", 64, "Who can vote in federal elections, run for federal office, and serve on a jury in the United States?",
     "U.S. citizens", ["Permanent residents", "Anyone living in the United States", "Visa holders"], GOV, None),
    ("2025", 65, "Which of these is a right of everyone living in the United States?", "Freedom of religion",
     ["Voting in federal elections", "Running for federal office", "Serving on a jury"], CON, None),
    ("2025", 66, "What do Americans show loyalty to when they say the Pledge of Allegiance?", "The United States",
     ["The president", "Congress", "The military"], USA, None),
    ("2025", 67, "Which of these is a promise new U.S. citizens make in the Oath of Allegiance?",
     "Defend the U.S. Constitution",
     ["Vote in every election", "Join a political party", "Live in the same state for five years"], GOV, None),
    ("2025", 73, "The colonists came to America for many reasons. Which of these was one?", "Religious freedom",
     ["To escape the Great Depression", "To join the California Gold Rush", "To fight in World War I"], NAM, None),
    ("2025", 74, "Who lived in America before the Europeans arrived?", "Native Americans",
     ["English colonists", "Spanish missionaries", "Dutch traders"], NAM, None),
    ("2025", 75, "What group of people was taken to America and sold as slaves?", "People from Africa",
     ["People from Ireland", "People from China", "People from Mexico"], NAM, None),
    ("2025", 76, "What war did the Americans fight to win independence from Britain?", "The American Revolutionary War",
     ["The French and Indian War", "The Civil War", "The Mexican-American War"], REV, "Revolutionary War"),
    ("2025", 77, "Which of these was one reason the Americans declared independence from Britain?",
     "Taxation without representation",
     ["The Louisiana Purchase", "The Emancipation Proclamation", "The Monroe Doctrine"], REV, None),
    ("2025", 78, "Who wrote the Declaration of Independence?", "Thomas Jefferson",
     ["George Washington", "Benjamin Franklin", "John Adams"], REV, None),
    ("2025", 80, "Which of these was an important event of the American Revolution?", "Battle of Saratoga",
     ["Battle of Gettysburg", "Battle of Vicksburg", "Battle of Antietam"], REV, None),
    ("2025", 81, "Which of these was one of the thirteen original American states?", "Georgia",
     ["Vermont", "Maine", "Florida"], NAM, None),
    ("2025", 82, "What American founding document was written in 1787?", "U.S. Constitution",
     ["Declaration of Independence", "Articles of Confederation", "Bill of Rights"], CON, None),
    ("2025", 83, "The Federalist Papers supported the passage of the U.S. Constitution. Which of these was one of the writers?",
     "John Jay", ["Thomas Jefferson", "Benjamin Franklin", "Samuel Adams"], NAM, None),
    ("2025", 84, "Why were the Federalist Papers important?", "They supported passing the U.S. Constitution.",
     ["They declared independence from Britain.", "They opposed ratifying the U.S. Constitution.",
      "They ended the Revolutionary War."], NAM, None),
    ("2025", 85, "Benjamin Franklin is famous for many things. Which of these is one?",
     "First Postmaster General of the United States",
     ["First Secretary of the Treasury", "First Chief Justice of the United States",
      "Second president of the United States"], NAM, None),
    ("2025", 86, "George Washington is famous for many things. Which of these is one?",
     "President of the Constitutional Convention",
     ["Writer of the Declaration of Independence", "Father of the Constitution", "First Secretary of State"], NAM, None),
    ("2025", 87, "Thomas Jefferson is famous for many things. Which of these is one?", "Founded the University of Virginia",
     ["First Secretary of the Treasury", "Father of the Constitution", "General of the Continental Army"], NAM, None),
    ("2025", 88, "James Madison is famous for many things. Which of these is one?", "Father of the Constitution",
     ["Father of Our Country", "First Postmaster General of the United States", "First Secretary of the Treasury"],
     NAM, None),
    ("2025", 89, "Alexander Hamilton is famous for many things. Which of these is one?", "First Secretary of the Treasury",
     ["First Secretary of State", "Third president of the United States",
      "First Postmaster General of the United States"], NAM, None),
    ("2025", 90, "What territory did the United States buy from France in 1803?", "Louisiana Territory",
     ["Alaska", "Oregon Territory", "Florida"], NAM, None),
    ("2025", 91, "Which of these wars did the United States fight in the 1800s?", "Mexican-American War",
     ["Korean War", "World War I", "Vietnam War"], NAM, None),
    ("2025", 92, "What was the U.S. war between the North and the South called?", "The Civil War",
     ["The Revolutionary War", "The Mexican-American War", "The Spanish-American War"], NAM, None),
    ("2025", 93, "Which of these was an important event of the American Civil War?", "Battle of Gettysburg",
     ["Battle of Bunker Hill", "Battle of Yorktown", "Battle of Saratoga"], NAM, None),
    ("2025", 94, "Abraham Lincoln is famous for many things. Which of these is one?", "Delivered the Gettysburg Address",
     ["Wrote the Declaration of Independence", "Bought Louisiana from France", "Led the Continental Army"], NAM, None),
    ("2025", 95, "What did the Emancipation Proclamation do?", "Freed slaves in the Confederacy",
     ["Gave women the right to vote", "Ended the Revolutionary War", "Created the Bill of Rights"], NAM, None),
    ("2025", 96, "What U.S. war ended slavery?", "The Civil War",
     ["The Revolutionary War", "World War I", "The Mexican-American War"], NAM, None),
    ("2025", 97, "What amendment to the U.S. Constitution says all persons born or naturalized in the United States, "
                 "and subject to the jurisdiction thereof, are U.S. citizens?", "Fourteenth Amendment",
     ["First Amendment", "Tenth Amendment", "Nineteenth Amendment"], CON, "14th Amendment"),
    ("2025", 99, "Which of these was a leader of the women's rights movement in the 1800s?", "Elizabeth Cady Stanton",
     ["Martha Washington", "Betsy Ross", "Dolley Madison"], NAM, None),
    ("2025", 100, "Which of these wars did the United States fight in the 1900s?", "Korean War",
     ["Civil War", "Mexican-American War", "Spanish-American War"], NAM, None),
    ("2025", 101, "Why did the United States enter World War I?", "Because Germany attacked U.S. civilian ships",
     ["Because Japan bombed Pearl Harbor", "To stop the spread of communism", "To force the Iraqi military from Kuwait"],
     WW1, None),
    ("2025", 103, "What was the Great Depression?", "Longest economic recession in modern history",
     ["A war between the North and the South", "A long drought on the Great Plains",
      "A period of rapid economic growth"], NAM, None),
    ("2025", 104, "What event started the Great Depression?", "The Great Crash",
     ["The attack on Pearl Harbor", "The end of the Civil War", "The sinking of the Titanic"], NAM, None),
    ("2025", 105, "Who was president during the Great Depression and World War II?", "Franklin Roosevelt",
     ["Woodrow Wilson", "Dwight Eisenhower", "Theodore Roosevelt"], NAM, None),
    ("2025", 106, "Why did the United States enter World War II?", "Japanese attacked Pearl Harbor",
     ["To stop the spread of communism", "To force the Iraqi military from Kuwait", "To support the Central Powers"],
     WW2, None),
    ("2025", 107, "Dwight Eisenhower is famous for many things. Which of these is one?", "General during World War II",
     ["General during the Civil War", "President during the Great Depression", "First Secretary of State"], WW2, None),
    ("2025", 108, "Who was the United States' main rival during the Cold War?", "Soviet Union",
     ["Germany", "Japan", "Great Britain"], COLD, None),
    ("2025", 109, "During the Cold War, what was one main concern of the United States?", "Communism",
     ["Slavery", "Monarchy", "Piracy"], COLD, None),
    ("2025", 110, "Why did the United States enter the Korean War?", "To stop the spread of communism",
     ["Because Japan attacked Pearl Harbor", "To force the Iraqi military from Kuwait",
      "Because Germany attacked U.S. ships"], COLD, None),
    ("2025", 111, "Why did the United States enter the Vietnam War?", "To stop the spread of communism",
     ["To force the Iraqi military from Kuwait", "Because Japan attacked Pearl Harbor",
      "To win independence from Britain"], COLD, None),
    ("2025", 112, "What did the American civil rights movement do?", "Fought to end racial discrimination",
     ["Fought for women's right to vote", "Fought to end the Vietnam War", "Fought for independence from Britain"],
     NAM, None),
    ("2025", 113, "Martin Luther King, Jr. is famous for many things. Which of these is one?", "Fought for civil rights",
     ["Led the women's suffrage movement", "Founded the first free public libraries", "Delivered the Gettysburg Address"],
     NAM, None),
    ("2025", 114, "Why did the United States enter the Persian Gulf War?", "To force the Iraqi military from Kuwait",
     ["To stop the spread of communism", "Because Japan attacked Pearl Harbor", "To support the Allied Powers against Germany"],
     "world.history.wars_battles.war", None),
    ("2025", 117, "Which of these is an American Indian tribe in the United States?", "Cherokee",
     ["Maori", "Zulu", "Aztec"], NAM, None),
    ("2025", 118, "Which of these is an example of an American innovation?", "Airplane",
     ["Printing press", "Gunpowder", "Magnetic compass"], NAM, None),
    ("2025", 119, "What is the capital of the United States?", "Washington, D.C.",
     ["New York City", "Philadelphia", "Boston"], USA, None),
    ("2025", 120, "Where is the Statue of Liberty?", "New York Harbor",
     ["Boston Harbor", "San Francisco Bay", "Chesapeake Bay"], USA, None),
    ("2025", 121, "Why does the U.S. flag have 13 stripes?", "Because the stripes represent the original colonies",
     ["Because the stripes represent the first presidents", "Because the stripes represent the Union states of the Civil War",
      "Because the stripes represent the amendments in the Bill of Rights"], USA, None),
    ("2025", 122, "Why does the U.S. flag have 50 stars?", "Because each star represents a state",
     ["Because each star represents a president", "Because each star represents a battle of the Revolution",
      "Because each star represents a signer of the Declaration of Independence"], USA, None),
    ("2025", 123, "What is the name of the U.S. national anthem?", "The Star-Spangled Banner",
     ["America the Beautiful", "My Country, 'Tis of Thee", "God Bless America"], USA, None),
    ("2025", 124, "The first motto of the United States was \"E Pluribus Unum.\" What does that mean?", "Out of many, one",
     ["In God we trust", "Liberty or death", "Land of the free"], USA, None),
    ("2025", 125, "What is Independence Day in the United States?", "A holiday to celebrate U.S. independence from Britain",
     ["A holiday to honor soldiers who died in military service",
      "A holiday to honor people who have served in the U.S. military",
      "A holiday to celebrate the end of the Civil War"], HOL, None),
    ("2025", 126, "Which of these is a national U.S. holiday?", "Juneteenth",
     ["Groundhog Day", "Valentine's Day", "Halloween"], HOL, None),
    ("2025", 127, "What is Memorial Day in the United States?", "A holiday to honor soldiers who died in military service",
     ["A holiday to honor people who have served in the U.S. military",
      "A holiday to celebrate U.S. independence from Britain", "A holiday to honor American workers"], HOL, None),
    ("2025", 128, "What is Veterans Day in the United States?",
     "A holiday to honor people who have served in the U.S. military",
     ["A holiday to honor soldiers who died in military service",
      "A holiday to celebrate U.S. independence from Britain", "A holiday to honor American workers"], HOL, None),
    # 2008 version: items the 2025 list does not ask
    ("2008", 3, "The idea of self-government is in the first three words of the U.S. Constitution. What are these words?",
     "We the People", ["Life, Liberty, and Happiness", "E Pluribus Unum", "In God We Trust"], CON, None),
    ("2008", 5, "What do we call the first ten amendments to the U.S. Constitution?", "The Bill of Rights",
     ["The Articles of Confederation", "The Federalist Papers", "The Emancipation Proclamation"], CON, None),
    ("2008", 14, "What stops one branch of the U.S. government from becoming too powerful?", "Checks and balances",
     ["The Electoral College", "The Cabinet", "Executive orders"], GOV, None),
    ("2008", 31, "If both the President and the Vice President of the United States can no longer serve, who becomes president?",
     "The Speaker of the House", ["The Chief Justice", "The Secretary of State", "The Senate Majority Leader"], GOV,
     "Speaker of the House"),
    ("2008", 49, "Which of these is a responsibility that is only for United States citizens?", "Serve on a jury",
     ["Pay federal taxes", "Obey federal laws", "Register for the Selective Service"], GOV, None),
    ("2008", 65, "What happened at the U.S. Constitutional Convention?", "The Constitution was written.",
     ["The Declaration of Independence was signed.", "The Civil War ended.", "Louisiana was bought from France."],
     NAM, None),
    ("2008", 69, "Who is the \"Father of Our Country\" in the United States?", "George Washington",
     ["James Madison", "Thomas Jefferson", "Abraham Lincoln"], NAM, None),
    ("2008", 70, "Who was the first President of the United States?", "George Washington",
     ["John Adams", "Thomas Jefferson", "Benjamin Franklin"], NAM, None),
    ("2008", 77, "What did Susan B. Anthony do?", "Fought for women's rights",
     ["Led the Underground Railroad", "Founded the first free public libraries", "Wrote the Star-Spangled Banner"],
     NAM, None),
    ("2008", 79, "Who was President of the United States during World War I?", "Woodrow Wilson",
     ["Franklin Roosevelt", "Theodore Roosevelt", "Abraham Lincoln"], WW1, "Wilson"),
    ("2008", 81, "Who did the United States fight in World War II?", "Japan, Germany, and Italy",
     ["Great Britain, France, and the Soviet Union", "China, Canada, and Australia", "Mexico, Spain, and Portugal"],
     WW2, None),
    ("2008", 82, "Before he was President, Eisenhower was a general. What war was he in?", "World War II",
     ["World War I", "The Civil War", "The Spanish-American War"], WW2, None),
    ("2008", 84, "What American movement tried to end racial discrimination?", "Civil rights movement",
     ["Women's suffrage movement", "Temperance movement", "Labor movement"], NAM, "civil rights"),
    ("2008", 88, "Which of these is one of the two longest rivers in the United States?", "Mississippi River",
     ["Hudson River", "Ohio River", "Rio Grande"], "world.places.physical_geography.mississippi_river", "Mississippi"),
    ("2008", 89, "What ocean is on the West Coast of the United States?", "Pacific Ocean",
     ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean"], "world.places.physical_geography.pacific_ocean", "Pacific"),
    ("2008", 90, "What ocean is on the East Coast of the United States?", "Atlantic Ocean",
     ["Pacific Ocean", "Indian Ocean", "Arctic Ocean"], "world.places.physical_geography.atlantic_ocean", "Atlantic"),
    ("2008", 91, "Which of these is a U.S. territory?", "Puerto Rico", ["Cuba", "Jamaica", "Bermuda"], USA, None),
    ("2008", 92, "Which of these U.S. states borders Canada?", "Montana", ["Wyoming", "Colorado", "Nebraska"], USA, None),
    ("2008", 93, "Which of these U.S. states borders Mexico?", "New Mexico", ["Nevada", "Oklahoma", "Utah"], USA, None),
]

_spec = importlib.util.spec_from_file_location("sources.mmlu", Path(__file__).parents[1] / "mmlu" / "adapter.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)


def fetch(raw_dir: Path) -> None:
    for version, fn in FILES.items():
        pdf, txt = raw_dir / fn, raw_dir / f"{version}.txt"
        if not pdf.exists():
            r = httpx.get(BASE + fn, follow_redirects=True, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            pdf.write_bytes(r.content)
        if not txt.exists():
            subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)


def _blocks(path: Path) -> dict[int, str]:
    """question number -> its official question + answers text (parentheses unwrapped)."""
    text = path.read_text().replace("(", "").replace(")", "")
    parts = re.split(r"\n\s*(\d{1,3})\.\s", "\n" + text)
    out: dict[int, str] = {}
    for n, body in zip(parts[1::2], parts[2::2]):
        out.setdefault(int(n), M.norm(body))
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    blocks = {v: _blocks(raw_dir / f"{v}.txt") for v in FILES}
    for version, num, text, correct, wrong, node, anchor in ITEMS:
        if M.norm(anchor or correct) not in blocks[version].get(num, ""):
            raise ValueError(f"{version} Q{num}: {anchor or correct!r} not in the official answers")
        answers = [correct, *wrong]
        order = sorted(range(len(answers)), key=lambda i: M.norm(answers[i]))  # stable, not keyed by position
        answers = [answers[i] for i in order]
        q = M.choice_question(source=NAME, text=text, answers=answers, correct=order.index(0), node=node,
                              item_id=f"{version}:{num}", license=LICENSE, origin="template",
                              meta={"test": f"USCIS civics test ({version} version)", "question_number": num,
                                    "distractors": "authored"})
        if q is None:
            raise ValueError(f"{version} Q{num}: answers do not make distinct keys")
        yield q
