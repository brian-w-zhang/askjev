"""General Social Survey (NORC) 1972-2024: non-political attitude items as Choice/Noul questions with weighted
US-adult answer shares.

Source: the GSS 1972-2024 cumulative cross-section (Release 3a, Stata file), a public no-login download from
gss.norc.org. Question wording was taken from the 2024/2022/2021 year codebooks and the 1972-2018 cumulative
codebook (not downloaded at runtime; the texts below are authored from them).

Each question is one GSS item in the self frame ("Taken all together, how would you say things are these days...").
Options are the item's substantive answer categories (volunteered, "can't choose", "does not apply" categories are
dropped and the shares renormalized). Yes/no and true/false items are Noul. Human data: weighted (WTSSPS) response
shares among valid answers in the item's most recent GSS year ("US adults 2024") and, when the item was also asked
at least 15 years earlier, in the year closest to 1990 ("US adults 1990") as a second population on the same
question. Two ranking batteries (qualities for a child, job attributes) become one Choice each over "ranked first".

Hemisphere: self for items about the respondent (their happiness, trust, values, habits, beliefs), world for
items about society (confidence in institutions, science, medicine, media, technology). Contested politics
(party, voting, abortion, guns, immigration, race attitudes, spending/government-role items, civil liberties,
policing, same-sex marriage, climate policy, national identity) are skipped entirely. Religious belief/practice
and sexual-morality items are kept and flagged "sensitive"; suicide-right items are flagged "sensitive". NSF science
literacy items carry truth.
"""

from __future__ import annotations

import re
import struct
import zipfile
from pathlib import Path
from typing import Iterator

import httpx
import numpy as np

from askjev.model import HumanDist, Question

NAME = "gss"
URL = "https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip"
DTA = "gss7224_r3a.dta"
LICENSE = "GSS public-use data (NORC at the University of Chicago); free for research use with citation"
SOURCE = "General Social Survey 1972-2024 (NORC), weighted by WTSSPS"
MIN_N_LATEST = 300
MIN_N_OLD = 250
OLD_TARGET_YEAR = 1990
OLD_GAP = 15

# ---------------------------------------------------------------------------------------------------------------
# nodes
HW = "self.mind.happiness_wellbeing"
MOOD = "self.personality.emotions_stress.recent_stress_mood"
HN = "self.mind.big_questions.meaning_human_nature"
BIGQ = "self.mind.big_questions"
EPI = "self.mind.epistemics"
FAMR = "self.love.family_parenting.family_rules_of_thumb"
FAMS = "self.love.family_parenting.family_situations"
ROMR = "self.love.romance_partnership.relationship_rules_of_thumb"
ROMC = "self.love.romance_partnership.relationship_choices"
FRH = "self.love.friendship.friendship_habits"
FRR = "self.love.friendship.friendship_rules_of_thumb"
NEIGH = "self.love.workplace_community.neighbors_roommates"
WORK = "self.lifestyle.work_study_life"
HAB = "self.lifestyle.habits_routines"
LEIS = "self.lifestyle.leisure_hobbies"
SCREENS = "self.lifestyle.screens_media"
MONEYH = "self.lifestyle.money_habits"
PRIO = "self.values.life_values.personal_priorities"
LRULE = "self.values.life_values.life_rules_of_thumb"
FAIRJ = "self.values.fairness_justice"
GIVE = "self.values.giving_charity"
HONEST = "self.values.honesty_trust.honesty_rules_of_thumb"
ANIM = "self.values.animals_environment"
DEATH = "self.mind.time_mortality.death_legacy"
SELFC = "self.personality.self_concept"
RISK = "self.personality.risk_decision_style"
TRUSTP = "self.personality.big_five.agreeableness.trust_modesty_temper"
KIND = "self.personality.big_five.agreeableness.kindness_cooperation"
EMP = "self.personality.emotions_stress.empathy_social_reading"
MOTIV = "self.personality.motivation_ambition"

AGREE = 'How much do you agree or disagree with this statement: "{}"'
SENS = ("sensitive",)

# Each item: var (or composite), text, kind, hemisphere, node, flags, opts (code -> label override),
# keys (label -> key override), truth.
ITEMS: list[dict] = []


def add(var, text, kind, hemi, node, flags=(), opts=None, truth=None, keys=None):
    ITEMS.append(dict(var=var, text=text, kind=kind, hemi=hemi, node=node, flags=list(flags), opts=opts,
                      truth=truth, keys=keys or {}))


def battery(template, kind, hemi, node, items, flags=(), **kw):
    for var, fill in items.items():
        n = node
        if isinstance(fill, tuple):
            fill, n = fill
        add(var, template.format(fill), kind, hemi, n, flags, **kw)


def days(n=7):
    return {i: f"{i} day" + ("" if i == 1 else "s") for i in range(n + 1)}


def scale(lo, hi, lo_lab, hi_lab):
    return {i: (f"{i} - {lo_lab}" if i == lo else f"{i} - {hi_lab}" if i == hi else str(i)) for i in range(lo, hi + 1)}


# --- happiness, life, health -------------------------------------------------------------------------------------
add("happy", "Taken all together, how would you say things are these days: would you say that you are very happy, "
    "pretty happy, or not too happy?", "personality", "self", HW)
add("happy7", "If you were to consider your life in general, how happy or unhappy would you say you are, on the whole?",
    "personality", "self", HW)
add("hapunhap", "If you were to consider your life in general these days, how happy or unhappy would you say you "
    "are, on the whole?", "personality", "self", HW)
add("life", "In general, do you find life exciting, pretty routine, or dull?", "personality", "self", HW)
add("health", "Would you say your own health, in general, is excellent, good, fair, or poor?", "personality", "self",
    SELFC)
add("quallife", "In general, would you say your quality of life is excellent, very good, good, fair, or poor?",
    "personality", "self", HW)
add("satsoc", "In general, how would you rate your satisfaction with your social activities and relationships?",
    "personality", "self", FRH)
add("satfin", "We are interested in how people are getting along financially these days. So far as you are "
    "concerned, would you say that you are pretty well satisfied with your present financial situation, more or less "
    "satisfied, or not satisfied at all?", "personality", "self", MONEYH)
add("satjob", "On the whole, how satisfied are you with the work you do: would you say you are very satisfied, "
    "moderately satisfied, a little dissatisfied, or very dissatisfied?", "personality", "self", WORK)
add("satlife", "All things considered, how satisfied are you with your life as a whole these days?", "personality",
    "self", HW)
add("satfam7", "All things considered, how satisfied are you with your family life?", "personality", "self", FAMS)
add("mygoals", 'How true is this statement for you: "It is easy for me to accomplish my goals."', "personality",
    "self", MOTIV)
add("emoprobs", "In the past seven days, how often have you been bothered by emotional problems such as feeling "
    "anxious, depressed or irritable?", "personality", "self", MOOD)
battery("During the past 4 weeks, how often have you {}", "personality", "self", MOOD, {
    "hlthdep": "felt unhappy and depressed?",
    "hlthconf": "lost confidence in yourself?",
    "hlthnot": "felt you could not overcome your problems?",
})
battery("During the past 4 weeks, how often have you {}", "personality", "self", MOOD, {
    "lonely1": "felt that you lack companionship?",
    "lonely2": "felt isolated from others?",
    "lonely3": "felt left out?",
    "unhappy": "been unhappy or depressed?",
    "pilingup": "felt difficulties were piling up so high that you could not overcome them?",
})
battery("Over the last 2 weeks, how often have you been bothered by {}", "personality", "self", MOOD, {
    "feelnerv": "feeling nervous, anxious, or on edge?",
    "worry": "not being able to stop or control worrying?",
    "feeldown": "feeling down, depressed, or hopeless?",
    "nointerest": "having little interest or pleasure in doing things?",
})
battery("During the past week, how much of the time {}", "personality", "self", MOOD, {
    "cesd1": "did you feel depressed?",
    "cesd3": "were you happy?",
    "cesd4": "did you feel lonely?",
    "cesd5": "did you feel sad?",
}, keys={"none or almost none of the time": "none_or_almost_none", "all or almost all of the time": "all_or_almost_all"})
battery("On how many days in the past seven days have you {}", "personality", "self", MOOD, {
    "hapfeel": "felt happy?",
    "ashamed": "felt ashamed of something you had done?",
    "fearful": "felt fearful about something?",
    "angry": "felt angry at someone?",
    "proud": "felt proud of something you had done?",
}, opts=days())

# --- trust and human nature ------------------------------------------------------------------------------------------
add("trust", "Generally speaking, would you say that most people can be trusted or that you can't be too careful in "
    "dealing with people?", "social", "self", HN)
add("helpful", "Would you say that most of the time people try to be helpful, or that they are mostly just looking "
    "out for themselves?", "social", "self", HN)
add("fair", "Do you think most people would try to take advantage of you if they got a chance, or would they try to "
    "be fair?", "social", "self", HN)
add("cantrust", "Generally speaking, would you say that people can be trusted or that you can't be too careful in "
    "dealing with people?", "social", "self", HN,
    keys={"people can almost always be trusted": "almost_always_trusted", "people can usually be trusted":
          "usually_trusted", "you usually can't be too careful in dealing with people": "usually_cant_be_too_careful",
          "you almost always can't be too careful in dealing with people": "almost_always_cant_be_too_careful"})
add("befair", "Do you think that most people would try to take advantage of you if they got the chance, or would "
    "they try to be fair?", "social", "self", HN,
    keys={"try to take advantage almost all of the time": "take_advantage_almost_always",
          "try to take advantage most of the time": "take_advantage_mostly",
          "try to be fair most of the time": "fair_mostly", "try to be fair almost all of the time": "fair_almost_always"})
add("trppl", "On a scale from 0 to 10, where 0 means you can't be too careful and 10 means that most people can be "
    "trusted, generally speaking, how much do you think people can be trusted?", "social", "self", HN,
    opts=scale(0, 10, "you can't be too careful", "most people can be trusted"))
add("intrust", "On a scale from 0 to 10, where 0 means no trust at all and 10 means complete trust, how much do you "
    "trust people you have only met online?", "social", "self", TRUSTP,
    opts=scale(0, 10, "no trust at all", "complete trust"))
battery(AGREE, "social", "self", TRUSTP, {
    "fewtrsty": "There are only a few people I can trust completely.",
    "exploit": "If you are not careful, other people will take advantage of you.",
    "wantbest": "I am sure that most other people want the best for me.",
})
add("geneexps", "Which do you think plays the bigger role in determining a person's personality: their genes or "
    "their experiences?", "social", "self", HN,
    opts={1: "genes play the major role", 2: "experience plays the major role"})
add("getahead", "Some people say that people get ahead by their own hard work; others say that lucky breaks or help "
    "from other people are more important. Which do you think is most important?", "evaluative", "world",
    "world.money.careers")
battery("For getting ahead in life, how important do you think {}", "evaluative", "world", "world.money.careers", {
    "opwlth": "it is to come from a wealthy family?",
    "oppared": "it is to have well-educated parents?",
    "opeduc": "it is to have a good education yourself?",
    "ophrdwrk": "hard work is?",
    "opknow": "it is to know the right people?",
    "opbribes": "it is to give bribes?",
})

# --- confidence in institutions (world) ------------------------------------------------------------------------------
battery("As far as the people running this institution are concerned, would you say you have a great deal of "
        "confidence, only some confidence, or hardly any confidence at all in them: {}?", "evaluative", "world", None, {
            "confinan": ("banks and financial institutions", "world.money.economics"),
            "conbus": ("major companies", "world.money.companies_brands"),
            "coneduc": ("education", "world.society.education"),
            "conpress": ("the press", "world.society.media_news"),
            "conmedic": ("medicine", "world.health.medicine"),
            "contv": ("television", "world.society.media_news"),
            "consci": ("the scientific community", "world.science"),
        })
add("conclerg", "As far as the people running this institution are concerned, would you say you have a great deal of "
    "confidence, only some confidence, or hardly any confidence at all in them: organized religion?", "evaluative",
    "world", "world.society.world_religions", SENS)
add("conhlth", "In general, how much confidence do you have in the health care system in the United States?",
    "evaluative", "world", "world.health.medicine")
battery("How reliable do you think the news is {}", "evaluative", "world", "world.society.media_news", {
    "smnews": "on social media?",
    "tvnews1": "on television?",
    "papernews": "in newspapers?",
    "radionews": "on the radio and in podcasts?",
    "webnews": "on news websites?",
})

# --- child-rearing, family, gender roles ----------------------------------------------------------------------------
add("@child_qualities", "If you had to choose, which of these would you pick as the most important thing for a child "
    "to learn to prepare him or her for life?", "values", "self", FAMR)
add("spanking", "Do you strongly agree, agree, disagree, or strongly disagree that it is sometimes necessary to "
    "discipline a child with a good, hard spanking?", "values", "self", FAMR)
add("chldidel", "What do you think is the ideal number of children for a family to have?", "values", "self", FAMR,
    opts={0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven or more",
          8: "as many as you want"})
add("aged", "As you know, many older people share a home with their grown children. Do you think this is generally a "
    "good idea or a bad idea?", "values", "self", FAMR)
battery(AGREE, "values", "self", FAMR, {
    "fechld": "A working mother can establish just as warm and secure a relationship with her children as a mother "
              "who does not work.",
    "fepresch": "A preschool child is likely to suffer if his or her mother works.",
    "fefam": "It is much better for everyone involved if the man is the achiever outside the home and the woman takes "
             "care of the home and family.",
    "meovrwrk": "Family life often suffers because men concentrate too much on their work.",
    "feovrwrk": "Family life often suffers because women concentrate too much on their work.",
    "famsuffr": "All in all, family life suffers when the woman has a full-time job.",
    "homekid": "A job is all right, but what most women really want is a home and children.",
    "housewrk": "Being a housewife is just as fulfilling as working for pay.",
    "hubbywk1": "A man's job is to earn money; a woman's job is to look after the home and family.",
    "marlegit": "People who want children ought to get married.",
    "marmakid": "A single mother can bring up her child as well as a married couple.",
    "marpakid": "A single father can bring up his child as well as a married couple.",
    "kidnofre": "Having children interferes too much with the freedom of parents.",
    "kidsocst": "Having children increases people's social standing in society.",
    "kidjoy": "Watching children grow up is life's greatest joy.",
    "kidempty": "People who have never had children lead empty lives.",
    "kidfinbu": "Children are a financial burden on their parents.",
    "kidjob": "Having children restricts the employment and career chances of one or both parents.",
    "twoincs1": "Both the man and woman should contribute to the household income.",
    "kidpars": "Adult children have a duty to look after their elderly parents.",
})
battery(AGREE, "values", "self", ROMR, {
    "cohabok": "It is all right for a couple to live together without intending to get married.",
    "cohabfst": "It is a good idea for a couple who intend to get married to live together first.",
    "marhappy": "Married people are generally happier than unmarried people.",
    "marnomar": "It is better to have a bad marriage than no marriage at all.",
    "divbest": "Divorce is usually the best solution when a couple can't seem to work out their marriage problems.",
})
add("premarsx", "If a man and a woman have sexual relations before marriage, do you think it is always wrong, almost "
    "always wrong, wrong only sometimes, or not wrong at all?", "values", "self", ROMR, SENS)
add("xmarsex", "What is your opinion about a married person having sexual relations with someone other than the "
    "marriage partner: is it always wrong, almost always wrong, wrong only sometimes, or not wrong at all?", "values",
    "self", ROMR, SENS)
battery("Do you think that women should work outside the home full-time, part-time or not at all {}", "values", "self",
        FAMR, {
            "wrkbaby": "when there is a child under school age?",
            "wrksch": "after the youngest child starts school?",
            "wrknokid": "after marrying and before there are children?",
            "wrkgrown": "after the children leave home?",
        })
add("famwkbst", "Consider a family with a child under school age. What, in your opinion, is the best way for them to "
    "organize their family and work life?", "values", "self", FAMR,
    keys={"the mother stays at home and the father works full-time": "mother_home_father_full_time",
          "the mother works part-time and the father works full-time": "mother_part_time_father_full_time",
          "both the mother and father work full-time": "both_full_time",
          "both the mother and father work part-time": "both_part_time",
          "the father works part-time and the mother works full-time": "father_part_time_mother_full_time",
          "the father stays at home and the mother works full-time": "father_home_mother_full_time"})
add("famwklst", "Consider a family with a child under school age. Which of these ways to organize their family and "
    "work life would be the least desirable?", "values", "self", FAMR,
    keys={"the mother stays at home and the father works full-time": "mother_home_father_full_time",
          "the mother works part-time and the father works full-time": "mother_part_time_father_full_time",
          "both the mother and father work full-time": "both_full_time",
          "both the mother and father work part-time": "both_part_time",
          "the father works part-time and the mother works full-time": "father_part_time_mother_full_time",
          "the father stays at home and the mother works full-time": "father_home_mother_full_time"})
add("paidlvdv", "Consider a couple who both work full-time and now have a newborn child. If both are in a similar work "
    "situation and are eligible for paid leave, how should this paid leave period be divided between the mother and "
    "the father?", "values", "self", FAMR,
    keys={"the mother should take the entire paid leave period and the father should not take any paid leave":
          "mother_takes_all",
          "the mother should take most of the paid leave period and the father should take some of it":
          "mother_takes_most",
          "the mother and the father should each take half of the paid leave period": "half_each",
          "the father should take most of the paid leave period and the mother should take some of it":
          "father_takes_most",
          "the father should take the entire paid leave period and the mother should not take any paid leave":
          "father_takes_all"})
add("rspgndr", "People have different opinions about how much responsibility women and men should have for the home "
    "and family. Which comes closest to your view?", "values", "self", FAMR)
add("prntlk", "People have different opinions about how well mothers and fathers are suited to look after their "
    "children. Which comes closest to your view?", "values", "self", FAMR)
battery("Consider a family with a father and a mother raising a five-year-old child. In your opinion, which parent "
        "should {}", "values", "self", FAMR, {
            "prntfnce": "provide for the family financially?",
            "prntcre": "take care of the child on a daily basis?",
            "prntply": "play with the child and take part in their leisure activities?",
            "prntbhav": "teach the child how to behave?",
            "prntadvs": "take time to listen to and advise the child if they have problems?",
            "prntmdl": "try to be a role model for the child?",
        }, keys={"the mother mostly": "mother_mostly", "the mother somewhat more than the father": "mother_somewhat_more",
                 "the mother and father equally": "both_equally",
                 "the father somewhat more than the mother": "father_somewhat_more", "the father mostly": "father_mostly"})
battery("Who do you think is better suited to be {}", "values", "self", FAIRJ, {
    "univgndr": "the head of a university: women, men, or are they equally suited?",
    "execgndr": "a senior executive of a large company: women, men, or are they equally suited?",
})
add("clsrltv", "Imagine a person living with a partner and their children. Which of these people would you consider "
    "to be that person's close relatives?", "social", "self", FAMS,
    keys={"children and partner only": "children_and_partner_only",
          "children, partner, parents and siblings": "plus_parents_and_siblings",
          "children, partner, parents, siblings, cousins, aunts/uncles, nephews/nieces": "plus_extended_family",
          "children, partner, parents, siblings, cousins, aunts/uncles, nephews/nieces, but others as well":
          "plus_extended_family_and_others"})

# --- friendship, social life, helping ---------------------------------------------------------------------------------
battery("How often do you {}", "social", "self", None, {
    "socrel": ("spend a social evening with relatives?", FAMS),
    "socommun": ("spend a social evening with someone who lives in your neighborhood?", NEIGH),
    "socfrend": ("spend a social evening with friends who live outside the neighborhood?", FRH),
    "socbar": ("go to a bar or tavern?", LEIS),
})
battery("How important is it to you that a close friend is someone who {}", "social", "self", FRR, {
    "frdthink": "is intelligent?",
    "frdhelps": "helps you?",
    "frdknows": "understands you?",
    "frdenjoy": "is enjoyable to be with?",
})
battery(AGREE, "values", "self", FRR, {
    "usefrds": "It's all right to develop friendships with people just because they can be useful to you.",
    "firstyou": "People should take care of themselves and their families first, before helping others.",
    "helpfrds": "People who are better off should help friends who are less well off.",
})
battery("Suppose {} Who would you turn to first for help?", "social", "self", FRH, {
    "hlphome": "you needed help around your home, for example moving furniture or doing household repairs.",
    "hlpsick": "you were sick in bed and needed help with household chores or shopping.",
    "hlpdown": "you felt a bit down or depressed and wanted to talk about it.",
    "hlpadvce": "you needed advice about a serious personal or family matter.",
})
battery(AGREE, "values", "self", GIVE, {
    "othshelp": "People should be willing to help others who are less fortunate.",
    "careself": "Those in need have to learn to take care of themselves and not depend on others.",
    "peoptrbl": "Personally assisting people in trouble is very important to me.",
    "selffrst": "These days people need to look after themselves and not overly worry about others.",
})
battery("During the past 12 months, how often have you {}", "social", "self", GIVE, {
    "givhmlss": "given food or money to a homeless person?",
    "retchnge": "returned money to a cashier after getting too much change?",
    "cutahead": "allowed a stranger to go ahead of you in line?",
    "directns": "given directions to a stranger?",
    "givseat": "offered your seat on a bus or in a public place to a stranger who was standing?",
    "givchrty": "given money to a charity?",
    "volchrty": "done volunteer work for a charity?",
}, keys={"at least 2 or 3 times in the past year": "two_or_three_times_a_year", "not at all in the past year": "not_at_all"})
battery("How often do you {}", "personality", "self", EMP, {
    "selfless": "feel a selfless caring for others?",
    "accptoth": "accept others even when they do things you think are wrong?",
})
battery(AGREE, "values", "self", ROMC, {
    "agape1": "I would rather suffer myself than let the one I love suffer.",
    "agape2": "I cannot be happy unless I place the one I love's happiness before my own.",
    "agape3": "I am usually willing to sacrifice my own wishes to let the one I love achieve theirs.",
    "agape4": "I would endure all things for the sake of the one I love.",
})

# --- personality, self-image -----------------------------------------------------------------------------------------
battery('How well does this statement describe you: "I see myself as someone who {}"', "personality", "self", None, {
    "big5a1": ("is reserved.", "self.personality.big_five.extraversion.sociability_energy"),
    "big5a2": ("is outgoing, sociable.", "self.personality.big_five.extraversion.sociability_energy"),
    "big5b1": ("is generally trusting.", TRUSTP),
    "big5b2": ("tends to find fault with others.", TRUSTP),
    "big5c1": ("does a thorough job.", "self.personality.big_five.conscientiousness.drive_self_discipline"),
    "big5c2": ("tends to be lazy.", "self.personality.big_five.conscientiousness.drive_self_discipline"),
    "big5d1": ("is relaxed, handles stress well.", "self.personality.big_five.neuroticism.fear_worry"),
    "big5d2": ("gets nervous easily.", "self.personality.big_five.neuroticism.fear_worry"),
    "big5e1": ("has an active imagination.", "self.personality.big_five.openness.ideas_imagination"),
    "big5e2": ("has few artistic interests.", "self.personality.big_five.openness.ideas_imagination"),
})
battery("How well does this describe you: {}?", "personality", "self", SELFC, {
    "depndabl": "a dependable person",
    "sadblue": "a person who often feels sad and blue",
    "athletic": "an athletic person",
    "kindpers": ("a kind person", KIND),
    "selfish": ("a selfish person", KIND),
})
battery(AGREE, "personality", "self", SELFC, {
    "satself": "On the whole, I am satisfied with myself.",
    "afailure": "All in all, I am inclined to feel that I am a failure.",
    "slfrspct": "I wish I could have more respect for myself.",
    "ofworth": "I feel that I'm a person of worth, at least on an equal plane with others.",
    "nogood": "At times I think I am no good at all.",
})
battery(AGREE, "personality", "self", HW, {
    "lotr1": "In uncertain times, I usually expect the best.",
    "lotr2": "If something can go wrong for me, it will.",
    "lotr3": "I'm always optimistic about my future.",
    "lotr4": "I hardly ever expect things to go my way.",
    "lotr5": "I rarely count on good things happening to me.",
    "lotr6": "Overall, I expect more good things to happen to me than bad.",
})
battery('How true or false is this statement for you: "{}"', "personality", "self", MOTIV, {
    "hope1": "If I should find myself in a jam, I could think of many ways to get out of it.",
    "hope2": "At the present time, I am energetically pursuing my goals.",
    "hope3": "There are lots of ways around any problem that I am facing now.",
    "hope4": "Right now, I see myself as being pretty successful.",
    "hope5": "I can think of many ways to reach my current goals.",
    "hope6": "At this time, I am meeting the goals that I have set for myself.",
})
battery('Is this statement true or false for you: "{}"', "personality", "self", HONEST, {
    "mcsds1": "I'm always willing to admit it when I make a mistake.",
    "mcsds2": "I sometimes try to get even rather than forgive and forget.",
    "mcsds3": "At times I have really insisted on having things my own way.",
    "mcsds4": "I have never been irked when people expressed ideas very different from my own.",
    "mcsds5": "I have never deliberately said something that hurt someone's feelings.",
    "mcsds6": "I like to gossip at times.",
    "mcsds7": "There have been occasions when I took advantage of someone.",
})

# --- values, morality, meaning -----------------------------------------------------------------------------------------
battery("How important is {} to you?", "values", "self", PRIO, {
    "impfinan": "financial security",
    "impmar": "being married",
    "impkids": "having children",
    "impgod": ("having faith in God", PRIO),
    "impthngs": "having nice things",
    "impcultr": "being cultured",
    "impjob": "having a fulfilling job",
    "impself": "being self-sufficient",
})
battery(AGREE, "values", "self", "self.values.moral_foundations", {
    "blkwhite": "Right and wrong are not usually a simple matter of black and white; there are many shades of gray.",
    "rotapple": "Immoral actions by one person can corrupt society in general.",
    "permoral": "Morality is a personal matter and society should not force everyone to follow one standard.",
})
add("punsin", AGREE.format("Those who violate God's rules must be punished."), "values", "self",
    "self.values.moral_foundations", SENS)
battery("Do you think a person has the right to end his or her own life if this person {}", "values", "self", DEATH, {
    "suicide1": "has an incurable disease?",
    "suicide2": "has gone bankrupt?",
    "suicide3": "has dishonored his or her family?",
    "suicide4": "is tired of living and ready to die?",
}, flags=SENS)
battery(AGREE, "values", "self", HN, {
    "fatalism": "There is little that people can do to change the course of their lives.",
    "nihilism": "In my opinion, life does not serve any purpose.",
    "egomeans": "Life is only meaningful if you provide the meaning yourself.",
})
add("godmeans", AGREE.format("To me, life is meaningful only because God exists."), "values", "self", HN, SENS)
battery(AGREE, "values", "self", EPI, {
    "grtwrks": "The great works of philosophy and science are the best source of truth, wisdom, and ethics.",
    "freemind": "To understand the world, we must free our minds from old traditions and beliefs.",
    "decevidc": "When I make important decisions in my life, I rely mostly on reason and evidence.",
    "advfmsci": "All of the greatest advances for humanity have come from science and technology.",
})
battery("Is it just or unjust, right or wrong, that people with higher incomes can {}", "values", "self", FAIRJ, {
    "richhlth": "buy better health care than people with lower incomes?",
    "richeduc": "buy better education for their children than people with lower incomes?",
})
battery("In deciding how much people ought to earn, how important should this be: {}?", "values", "self", FAIRJ, {
    "payresp": "how much responsibility goes with the job",
    "payedtrn": "the number of years spent in education and training",
    "paychild": "whether the person has children to support",
    "paydowel": "how well he or she does the job",
})

# --- work -------------------------------------------------------------------------------------------------------------
add("@job_values", "Which of these would you most prefer in a job?", "values", "self", WORK)
add("richwork", "If you were to get enough money to live as comfortably as you would like for the rest of your life, "
    "would you continue to work or would you stop working?", "values", "self", WORK)
battery(AGREE, "values", "self", WORK, {
    "wrkearn": "A job is just a way of earning money, no more.",
    "wrkenjoy": "I would enjoy having a paid job even if I did not need the money.",
})
battery("How important is it to you personally that a job {}", "values", "self", WORK, {
    "secjob": "offers job security?",
    "hiinc": "offers a high income?",
    "promotn": "offers good opportunities for advancement?",
    "intjob": "is interesting?",
    "wrkindp": "allows someone to work independently?",
    "hlpoths": "allows someone to help other people?",
    "hlpsoc": "is useful to society?",
    "flexhrs1": "allows someone to decide their times or days of work?",
    "wkpersnl": "involves personal contact with other people?",
})
add("empself", "Suppose you were working and could choose between different kinds of jobs. Which would you personally "
    "choose: being an employee or being self-employed?", "values", "self", WORK,
    opts={1: "being an employee", 2: "being self-employed"})
add("smallbig", "Suppose you were working and could choose between different kinds of jobs. Which would you personally "
    "choose: working in a small firm or working in a large firm?", "values", "self", WORK,
    opts={1: "a small firm", 2: "a large firm"})
add("hrsmoney", "Think of the number of hours you work and the money you earn in your main job. If you had only one of "
    "these three choices, which would you prefer?", "values", "self", WORK)
battery("Suppose you could change the way you spend your time, spending more time on some things and less time on "
        "others. Would you like to spend more time, the same time, or less time than now {}", "values", "self", PRIO, {
            "timepdwk": "in a paid job?",
            "timehhwk": "doing household work?",
            "timefam": "with your family?",
            "timefrnd": "with your friends?",
            "timeleis": "in leisure activities?",
        })

# --- religion and spirituality (flagged) ------------------------------------------------------------------------------
add("god", "Which statement comes closest to expressing what you believe about God: you don't believe in God; you "
    "don't know whether there is a God and don't believe there is any way to find out; you don't believe in a personal "
    "God but do believe in a Higher Power of some kind; you find yourself believing in God some of the time but not at "
    "others; while you have doubts, you feel that you do believe in God; or you know God really exists and have no "
    "doubts about it?", "values", "self", BIGQ, SENS,
    keys={"don't believe": "dont_believe", "don't know, no way to find out": "dont_know_no_way_to_find_out",
          "higher power": "higher_power", "believe sometimes": "believe_sometimes",
          "believe with doubts": "believe_with_doubts", "no doubts": "no_doubts"})
add("postlife", "Do you believe there is a life after death?", "values", "self", DEATH, SENS)
battery("Do you believe in {}", "values", "self", BIGQ, {
    "heaven": "heaven?",
    "hell": "hell?",
    "miracles": "religious miracles?",
    "reincar": "reincarnation, being reborn in this world again and again?",
}, flags=SENS)
add("bible", "Which of these statements comes closest to describing your feelings about the Bible: it is the actual "
    "word of God and is to be taken literally, word for word; it is the inspired word of God but not everything in it "
    "should be taken literally; or it is an ancient book of fables, legends, history, and moral precepts recorded by "
    "men?", "values", "self", "world.society.world_religions", SENS,
    keys={"word of god": "actual_word_of_god", "inspired word": "inspired_word_of_god",
          "ancient book": "ancient_book_of_fables"})
add("reltruth", "Which statement comes closest to your own view: there is very little truth in any religion; there are "
    "basic truths in many religions; or there is truth only in one religion?", "values", "self",
    "world.society.world_religions", SENS,
    opts={1: "very little truth in any religion", 2: "basic truths in many religions", 3: "truth only in one religion"})
add("relpersn", "To what extent do you consider yourself a religious person? Are you very religious, moderately "
    "religious, slightly religious, or not religious at all?", "personality", "self", SELFC, SENS)
add("sprtprsn", "To what extent do you consider yourself a spiritual person? Are you very spiritual, moderately "
    "spiritual, slightly spiritual, or not spiritual at all?", "personality", "self", SELFC, SENS)
add("religimp", "How important is religion in your life: very important, somewhat important, not too important, or not "
    "at all important?", "values", "self", PRIO, SENS)
add("attend", "How often do you attend religious services?", "personality", "self", HAB, SENS)
add("pray", "About how often do you pray?", "personality", "self", HAB, SENS)
add("mditate1", "How often do you meditate?", "personality", "self", HAB)
add("relactiv", "How often do you take part in the activities and organizations of a church or place of worship other "
    "than attending services?", "personality", "self", HAB, SENS)
battery(AGREE, "values", "self", "world.society.world_religions", {
    "religcon": "Looking around the world, religions bring more conflict than peace.",
    "religint": "People with very strong religious beliefs are often too intolerant of others.",
    "comfort": "Religion helps people to gain comfort in times of trouble and sorrow.",
    "makefrnd": "Religion helps people to make friends.",
    "paxhappy": "Religion helps people to find inner peace and happiness.",
    "rspctrel": "We must respect all religions.",
    "mywaygod": "I have my own way of connecting with God without churches or religious services.",
    "theism": "There is a God who concerns Himself with every human being personally.",
    "trustsci": "We trust too much in science and not enough in religious faith.",
}, flags=SENS)

# --- science and technology (world) ----------------------------------------------------------------------------------
battery(AGREE, "evaluative", "world", "world.science", {
    "nextgen": "Because of science and technology, there will be more opportunities for the next generation.",
    "toofast": "Science makes our way of life change too fast.",
    "advfront": "Even if it brings no immediate benefits, scientific research that advances the frontiers of knowledge "
                "is necessary and should be supported by the federal government.",
    "scientgo": "Scientific researchers are dedicated people who work for the good of humanity.",
    "scienthe": "Scientists are helping to solve challenging problems.",
    "scientod": "Scientists are apt to be odd and peculiar people.",
    "scientbe": "Most scientists want to work on things that will make life better for the average person.",
    "harmgood": "Modern science does more harm than good.",
})
add("scibnfts", "People have frequently noted that scientific research has produced benefits and harmful results. "
    "Would you say that, on balance, the benefits of scientific research have outweighed the harmful results, or have "
    "the harmful results of scientific research been greater than its benefits?", "evaluative", "world",
    "world.science")
battery("In general, how dangerous do you think {}", "evaluative", "world", None, {
    "nukegen": ("nuclear power stations are for the environment?", "world.tech.engineering_inventions.energy_power"),
    "indusgen": ("air pollution caused by industry is for the environment?", "world.nature.ecosystems_conservation"),
    "chemgen": ("pesticides and chemicals used in farming are for the environment?",
                "world.nature.ecosystems_conservation"),
    "watergen": ("pollution of America's rivers, lakes and streams is for the environment?",
                 "world.nature.ecosystems_conservation"),
    "genegen": ("modifying the genes of certain crops is for the environment?", "world.science.biology_genetics"),
    "carsgen": ("air pollution caused by cars is for the environment?", "world.nature.ecosystems_conservation"),
}, keys={"extremely dangerous for the environment": "extremely_dangerous",
         "not dangerous at all for the environment": "not_dangerous_at_all"})
battery(AGREE, "evaluative", "world", "world.future.technology", {
    "techesy": "Digital technologies make our lives easier.",
    "harmgood1": "Digital technologies do more harm than good to society.",
    "nextgen1": "Digital technologies provide more opportunities for the next generation.",
})
add("agetech", "Who do you think is benefitting more from digital technologies: older people or younger people?",
    "evaluative", "world", "world.future.technology",
    keys={"older people are benefitting more than younger people": "older_people_more",
          "older people and younger people are benefitting equally": "equally",
          "younger people are benefitting more than older people": "younger_people_more",
          "neither older nor younger are benefitting": "neither"})
add("classtech", "Who do you think is benefitting more from digital technologies: rich people or poor people?",
    "evaluative", "world", "world.future.technology",
    keys={"rich people are benefitting more than poor people": "rich_people_more",
          "rich and poor people are benefitting equally": "equally",
          "poor people are benefitting more than rich people": "poor_people_more",
          "neither rich people nor poor people are benefitting": "neither"})
add("aiworry", "How worried or not worried are you that artificial intelligence will take over many jobs done by "
    "humans?", "evaluative", "world", "world.future.ai")
battery("On a scale from 0 to 10, where 0 means totally uncomfortable and 10 means totally comfortable, how would you "
        "feel about {}", "personality", "self", RISK, {
            "aimed": "having a medical operation performed by a robot?",
            "aidrive": "travelling in a driverless car?",
        }, opts=scale(0, 10, "totally uncomfortable", "totally comfortable"))
battery(AGREE, "personality", "self", SCREENS, {
    "intmeet": "I feel more comfortable meeting people online than in person.",
    "intlnly": "I would feel lonely if I could not access the internet.",
    "infodeal": "I would provide personal information to a company in exchange for discounts or free products.",
    "infoprofit": "I would provide personal information to a company even if it could profit from it.",
})
add("intcnfrm", "How often do you try to confirm the information you find online with other sources?", "personality",
    "self", "self.mind.epistemics.evidence_sources")
battery("How would you rate your {}", "personality", "self", SCREENS, {
    "intskill": "skills at using the internet?",
    "intliteracy": "knowledge of what information to share and not to share online?",
})
add("news", "How often do you read the newspaper: every day, a few times a week, once a week, less than once a week, or "
    "never?", "personality", "self", SCREENS)
battery("How interested are you in {}", "taste", "self", LEIS, {
    "intsci": "issues about new scientific discoveries?",
    "inttech": "issues about the use of new inventions and technologies?",
    "intmed": "issues about new medical discoveries?",
    "intspace": "issues about space exploration?",
    "intenvir": "issues about environmental pollution?",
    "intecon": "economic issues and business conditions?",
    "inteduc": "local school issues?",
    "intfarm": "agricultural and farm issues?",
    "intintl": "international and foreign policy issues?",
})
add("astrolgy", "Do you ever read a horoscope or your personal astrology report?", "personality", "self",
    "self.mind.luck_fate.superstitions_omens")
add("genegoo2", "Do you think genetic testing will do more good than harm, or more harm than good?", "evaluative",
    "world", "world.science.biology_genetics", opts={1: "more good than harm", 2: "more harm than good", 3: "it depends"})
add("antests", AGREE.format("It is right to use animals for medical testing if it might save human lives."), "values",
    "self", ANIM)

# NSF science literacy (truth)
battery('Is this statement true? "{}"', "factual", "world", None, {
    "hotcore": ("The center of the Earth is very hot.", "world.nature.geology"),
    "radioact": ("All radioactivity is man-made.", "world.science.physics.particles_forces"),
    "boyorgrl": ("It is the father's gene that decides whether the baby is a boy or a girl.",
                 "world.science.biology_genetics"),
    "lasers": ("Lasers work by focusing sound waves.", "world.science.physics.matter_energy"),
    "electron": ("Electrons are smaller than atoms.", "world.science.physics.particles_forces"),
    "viruses": ("Antibiotics kill viruses as well as bacteria.", "world.health.medicine"),
    "condrift": ("The continents on which we live have been moving their locations for millions of years and will "
                 "continue to move in the future.", "world.nature.geology"),
    "evolved": ("Human beings, as we know them today, developed from earlier species of animals.",
                "world.science.biology_genetics"),
    "evolved2": ("Elephants, as we know them today, descended from earlier species of animals.",
                 "world.science.biology_genetics"),
})
TRUTH = {"hotcore": True, "radioact": False, "boyorgrl": True, "lasers": False, "electron": True, "viruses": False,
         "condrift": True, "evolved": True, "evolved2": True}
add("earthsun", "Does the Earth go around the Sun, or does the Sun go around the Earth?", "factual", "world",
    "world.science.astronomy_space.solar_system_bodies", truth="earth_around_sun")
add("solarrev", "How long does it take for the Earth to go around the Sun: one day, one month, or one year?", "factual",
    "world", "world.science.astronomy_space.solar_system_bodies", truth="one_year")
add("odds1", "A doctor tells a couple that their genetic makeup means that they've got one in four chances of having a "
    "child with an inherited illness. Does this mean that if their first three children are healthy, the fourth will "
    "have the illness?", "factual", "world", "world.science.mathematics", truth=False)
add("odds2", "A doctor tells a couple that their genetic makeup means that they've got one in four chances of having a "
    "child with an inherited illness. Does this mean that each of the couple's children will have the same risk of "
    "suffering from the illness?", "factual", "world", "world.science.mathematics", truth=True)
add("expdesgn", "Two scientists want to know if a certain drug is effective against high blood pressure. The first "
    "scientist wants to give the drug to 1,000 people with high blood pressure and see how many of them experience "
    "lower blood pressure levels. The second scientist wants to give the drug to 500 people with high blood pressure "
    "and not give the drug to another 500 people with high blood pressure, and see how many in both groups experience "
    "lower blood pressure levels. Which is the better way to test this drug?", "factual", "world",
    "world.science.scientists_discoveries", opts={1: "give all 1,000 the drug", 2: "give 500 the drug and 500 not"},
    keys={"give all 1,000 the drug": "all_1000_get_the_drug", "give 500 the drug and 500 not": "500_drug_500_no_drug"},
    truth="500_drug_500_no_drug")
add("astrosci", "Would you say that astrology is very scientific, sort of scientific, or not at all scientific?",
    "factual", "world", "world.science.fringe_mysteries", truth="not_at_all_scientific")

# --- health and medicine (world) -------------------------------------------------------------------------------------
battery(AGREE, "evaluative", "world", "world.health.medicine", {
    "hlthmore": "People use health care services more than necessary.",
    "hlthinf": "In general, the health care system in the United States is inefficient.",
    "altmed": "Alternative medicine provides better solutions for health problems than mainstream medicine.",
    "doctrst": "All things considered, doctors in the United States can be trusted.",
    "docskls": "The medical skills of doctors in the United States are not as good as they should be.",
    "docearn": "Doctors in the United States care more about their earnings than about their patients.",
    "websympt": "The internet is useful to help people decide if their symptoms are serious enough to see a doctor.",
    "webdradv": "The internet is useful to check that the doctor is giving people appropriate advice.",
    "webrely": "It is not easy to distinguish between reliable and unreliable health information on the internet.",
    "vaxdoharm": "Overall, vaccinations do more harm than good.",
    "immunbetr": "It is better to develop immunity by getting ill than by having a vaccination.",
    "vaxkids": "Vaccines are important for children to have.",
    "vaxsafe": "Vaccines are safe.",
})
battery(AGREE, "evaluative", "world", "world.health.diseases", {
    "hlthbeh": "People suffer from severe health problems because of the way they behave.",
    "hlthenv": "People suffer from severe health problems because of the environment they are exposed to at work or "
               "where they live.",
    "hlthgene": "People suffer from severe health problems because of their genes.",
    "hlthpoor": "People suffer from severe health problems because they are poor.",
})
battery("In the United States, do you think it is easier or harder to get access to health care {}", "evaluative",
        "world", "world.health.medicine", {
            "hlthacc1": "for rich people than for poor people?",
            "hlthacc2": "for old people than for young people?",
            "hlthacc3": "for women than for men?",
        })
add("hlthsat", "In general, how satisfied or dissatisfied are you with the health care system in the United States?",
    "evaluative", "world", "world.health.medicine")
battery("How often do you {}", "personality", "self", HAB, {
    "physact": "do physical activity for at least 20 minutes that makes you sweat or breathe more heavily than usual?",
    "frtvegs": "eat fresh fruit or vegetables?",
})

# --- environment and nature ------------------------------------------------------------------------------------------
battery(AGREE, "values", "self", ANIM, {
    "scigrn": "Modern science will solve our environmental problems with little change to our way of life.",
    "harmsgrn": "Almost everything we do in modern life harms the environment.",
    "grwtharm": "Economic growth always harms the environment.",
    "toodifme": "It is just too difficult for someone like me to do much about the environment.",
    "ihlpgrn": "I do what is right for the environment, even when it costs more money or takes more time.",
    "impgrn": "There are more important things to do in life than protect the environment.",
    "othssame": "There is no point in doing what I can for the environment unless others do the same.",
    "helpharm": "I find it hard to know whether the way I live is helpful or harmful to the environment.",
    "popgrwth": "The earth cannot continue to support population growth at its present rate.",
})
battery("How willing would you be to {} in order to protect the environment?", "values", "self", ANIM, {
    "grnprice": "pay much higher prices",
    "grnsol": "accept cuts in your standard of living",
})
add("grncon", "Generally speaking, how concerned are you about environmental issues, on a scale from 1 (not at all "
    "concerned) to 5 (very concerned)?", "values", "self", ANIM,
    opts=scale(1, 5, "not at all concerned", "very concerned"))
battery("How often do you {}", "personality", "self", HAB, {
    "recycle": "make a special effort to sort glass or cans or plastic or newspapers and so on for recycling?",
    "nobuygrn": "avoid buying certain products for environmental reasons?",
})
add("enjoynat", "How much, if at all, do you enjoy being outside in nature?", "taste", "self", LEIS)
add("activnat", "How often do you engage in leisure activities outside in nature, such as hiking, bird watching, "
    "swimming, skiing or other outdoor activities?", "taste", "self", LEIS)
battery("During the last 12 months, did you {}", "taste", "self", LEIS, {
    "yrmovie": "go to the movies?",
    "yrartxbt": "go in person to an art exhibit, such as paintings, sculpture, textiles, graphic design, or "
                "photography?",
    "yrcreat": "create or perform art of your own, such as music, theater, dance, creative writing, crafts, or visual "
               "art?",
    "yrrdg": "read any novels or short stories, poetry, or plays?",
})

# --- society and money (world) ---------------------------------------------------------------------------------------
add("credam", "Do you think Americans' credit scores mostly have to do with choices they make, or with things out of "
    "their control?", "evaluative", "world", "world.money.personal_finance",
    keys={"entirely choices they make": "entirely_their_choices", "mostly choices they make": "mostly_their_choices",
          "both choices they make and things out of their control": "both_equally",
          "mostly things out of their control": "mostly_out_of_their_control",
          "entirely things out of their control": "entirely_out_of_their_control"})
battery("How fair or unfair do you think it is for {} to use people's credit reports when making decisions?",
        "values", "self", FAIRJ, {
            "credland": "landlords",
            "credemp": "employers",
            "credcar": "car insurance companies",
        })

# ---------------------------------------------------------------------------------------------------------------------
COMPOSITES = {
    "@child_qualities": {"obey": "to obey", "popular": "to be well-liked or popular", "thnkself": "to think for "
                         "himself or herself", "workhard": "to work hard", "helpoth": "to help others when they need "
                         "help"},
    "@job_values": {"jobinc": "high income", "jobsec": "no danger of being fired", "jobhour": "short working hours",
                    "jobpromo": "chances for advancement",
                    "jobmeans": "work that is important and gives a feeling of accomplishment"},
}
COMPOSITE_KEYS = {"to be well-liked or popular": "to_be_well_liked", "to think for himself or herself":
                  "to_think_for_themselves", "to help others when they need help": "to_help_others",
                  "work that is important and gives a feeling of accomplishment": "important_meaningful_work"}

DROP = re.compile(
    r"\(vol|volunteer|phone mode|^other\b|^depends$|^it depends$|don'?t know|can'?t choose|refused|no answer|does"
    r"(n'?t| not) apply|no job|not attending|did not need|not available|^no children|works alone|haven'?t heard|"
    r"i don'?t have|not applicable|^iap$|r does not have",
    re.I,
)


def _slug(s: str) -> str:
    s = s.lower().replace("&", "and").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s


def _key(label: str, overrides: dict) -> str:
    if label in overrides:
        return overrides[label]
    words = _slug(label).split("_")
    return "_".join(words[:6])


# --- Stata 118 reader (numpy; no pandas/pyreadstat) ------------------------------------------------------------------
def _read_dta(path: Path):
    with open(path, "rb") as f:
        head = f.read(4096)
        pre = b"<stata_dta><header><release>118</release><byteorder>LSF</byteorder><K>"
        assert head.startswith(pre), "unexpected Stata format"
        p = len(pre)
        k = struct.unpack("<H", head[p:p + 2])[0]
        p += 2 + len(b"</K><N>")
        n = struct.unpack("<Q", head[p:p + 8])[0]
        i = head.index(b"<map>") + 5
        mp = struct.unpack("<14Q", head[i:i + 112])
        f.seek(mp[2] + len(b"<variable_types>"))
        types = struct.unpack(f"<{k}H", f.read(2 * k))
        f.seek(mp[3] + len(b"<varnames>"))
        raw = f.read(129 * k)
        names = [raw[j * 129:(j + 1) * 129].split(b"\0")[0].decode() for j in range(k)]
        f.seek(mp[6] + len(b"<value_label_names>"))
        raw = f.read(129 * k)
        vln = [raw[j * 129:(j + 1) * 129].split(b"\0")[0].decode() for j in range(k)]
        f.seek(mp[11] + len(b"<value_labels>"))
        labels = {}
        while f.tell() < mp[12]:
            if f.read(5) != b"<lbl>":
                break
            ln = struct.unpack("<i", f.read(4))[0]
            nm = f.read(129).split(b"\0")[0].decode()
            f.read(3)
            tab = f.read(ln)
            f.read(6)
            cnt = struct.unpack("<i", tab[:4])[0]
            off = struct.unpack(f"<{cnt}i", tab[8:8 + 4 * cnt])
            val = struct.unpack(f"<{cnt}i", tab[8 + 4 * cnt:8 + 8 * cnt])
            txt = tab[8 + 8 * cnt:]
            labels[nm] = {v: txt[o:txt.index(b"\0", o)].decode("utf-8", "replace") for o, v in zip(off, val)}
    dt = []
    for nm, t in zip(names, types):
        if 1 <= t <= 2045:
            dt.append((nm, f"S{t}"))
        elif t == 32768:
            dt.append((nm, "V8"))
        else:
            dt.append((nm, {65526: "<f8", 65527: "<f4", 65528: "<i4", 65529: "<i2", 65530: "i1"}[t]))
    data = np.array(np.memmap(path, dtype=np.dtype(dt), mode="r", offset=mp[9] + len(b"<data>"), shape=(n,)))
    return data, {nm: labels.get(v, {}) for nm, v in zip(names, vln)}


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    if (raw_dir / DTA).exists():
        return
    z = raw_dir / "GSS_stata.zip"
    if not z.exists():
        with httpx.stream("GET", URL, follow_redirects=True, timeout=600) as r:
            r.raise_for_status()
            with open(z, "wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
    with zipfile.ZipFile(z) as zf:
        member = next(m for m in zf.namelist() if m.endswith(DTA))
        with zf.open(member) as src, open(raw_dir / DTA, "wb") as dst:
            while chunk := src.read(1 << 22):
                dst.write(chunk)


def _dist(col, year, w, y, codes):
    """Weighted shares over `codes` among respondents in year y with a valid code; (shares, n)."""
    m = (year == y) & np.isin(col, codes)
    n = int(m.sum())
    if not n:
        return None, 0
    tot = w[m].sum()
    return [float(w[m & (col == c)].sum() / tot) for c in codes], n


def _years(col, year, codes):
    ok = np.isin(col, codes)
    ys, cnt = np.unique(year[ok], return_counts=True)
    return {int(a): int(b) for a, b in zip(ys, cnt)}


def _pick_years(ny: dict) -> tuple[int | None, int | None]:
    good = {y: n for y, n in ny.items() if n >= MIN_N_LATEST}
    if not good:
        return None, None
    latest = max(good)
    old = [y for y, n in ny.items() if n >= MIN_N_OLD and y <= latest - OLD_GAP]
    return latest, (min(old, key=lambda y: (abs(y - OLD_TARGET_YEAR), y)) if old else None)


def _human(shares_by_year: dict, keys: list[str]) -> list[HumanDist]:
    out = []
    for y, (sh, n) in shares_by_year.items():
        tot = sum(sh)
        out.append(HumanDist(population=f"US adults {y}", distribution={k: round(s / tot, 4) for k, s in zip(keys, sh)},
                             n=n, source=SOURCE, wave=str(y)))
    return out


def normalize(raw_dir: Path) -> Iterator[Question]:
    data, labels = _read_dta(raw_dir / DTA)
    year = data["year"].astype(int)
    w = data["wtssps"].astype(float)
    w = np.where(np.isfinite(w) & (w < 1e30) & (w > 0), w, 0.0)
    skipped = []
    for it in ITEMS:
        var = it["var"]
        if var.startswith("@"):
            parts = COMPOSITES[var]
            cols = {v: data[v].astype(int) for v in parts}
            first = np.stack([cols[v] == 1 for v in parts])
            valid = first.sum(0) == 1
            codes = list(range(len(parts)))
            col = np.where(valid, first.argmax(0), -1)
            labs = list(parts.values())
            ny = _years(col, year, codes)
            it = dict(it, keys={**COMPOSITE_KEYS, **it["keys"]})
        else:
            col = data[var]
            vl = labels.get(var, {})
            if it["opts"]:
                pairs = list(it["opts"].items())
            else:
                pairs = sorted((c, l) for c, l in vl.items() if abs(c) < 1000)
            pairs = [(c, re.sub(r"\s*\((if )?vol[^)]*\)|\s*\(phone mode[^)]*\)", "", l).strip()) for c, l in pairs
                     if l in it["keys"] or not DROP.search(l)]
            codes = [c for c, _ in pairs]
            labs = [l for _, l in pairs]
            col = col.astype(int)
            ny = _years(col, year, codes)
        latest, old = _pick_years(ny)
        if latest is None or len(codes) < 2:
            skipped.append(var)
            continue
        by_year = {}
        for y in (latest, old):
            if y is not None:
                sh, n = _dist(col, year, w, y, codes)
                if sh:
                    by_year[y] = (sh, n)
        low = [l.lower() for l in labs]
        if sorted(low) in (["no", "yes"], ["false", "true"]):
            prim, options = "noul", None
            yes = low.index("yes") if "yes" in low else low.index("true")
            keys = ["true" if i == yes else "false" for i in range(len(labs))]
        else:
            prim = "choice"
            keys = [_key(l, it["keys"]) for l in labs]
            if len(set(keys)) != len(keys):
                raise ValueError(f"{var}: duplicate option keys {keys}")
            options = {k: (l[0].upper() + l[1:] if _slug(l) != k else None) for k, l in zip(keys, labs)}
        truth = it["truth"]
        if truth is None and var in TRUTH:
            truth = TRUTH[var]
        meta = {"gss_var": var.lstrip("@"), "years": {str(y): n for y, n in sorted(ny.items())}}
        if var.startswith("@"):
            meta["gss_vars"] = list(COMPOSITES[var])
            meta["note"] = "distribution = share ranking each option first"
        if it["flags"]:
            meta["flags"] = it["flags"]
        yield Question(
            text=it["text"],
            primitive=prim,
            hemisphere=it["hemi"],
            kind=it["kind"],
            origin="dataset",
            source=NAME,
            options=options,
            node_hint=it["node"],
            source_item_id=var.lstrip("@").upper(),
            license=LICENSE,
            truth=truth,
            human=_human(by_year, keys),
            meta=meta,
        )
    if skipped:
        print("gss skipped (no year with enough answers):", skipped)
