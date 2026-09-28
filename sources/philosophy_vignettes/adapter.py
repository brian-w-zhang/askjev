"""Experimental-philosophy vignettes: knowledge (Gettier), free will, and the side-effect effect (docs/15 E19b / E28;
the second half of resemble_philosophers: what ordinary people say, not what philosophers say).

Human data, only where a study reports the split for the question as asked, stored as a two-option distribution:
- The Gettier "American car" case (Weinberg, Nichols & Stich 2001, Philosophical Topics 29:429-460) is asked with no
  human distribution: its Western split could not be verified from the paper or a reliable secondary source, and
  its cultural contrast did not replicate (Kim & Yuan 2015, Episteme; Machery et al. 2017, Noûs).
- Determinism, Nichols & Knobe 2007 (Noûs 41:663-685): p. 670, abstract condition, 86% said no one in a
  deterministic universe can be fully morally responsible; p. 670, concrete case (Bill kills his family), 72% said
  he is fully morally responsible; pp. 675-676 and Table 2, low-affect case (Mark cheats on his taxes, determinist
  universe), 23% said it is possible he is fully responsible (figure as reported in Florida Philosophical Review's
  critique of the paper; Table 2 is an image).
- Nahmias, Morris, Nadelhoffer & Turner 2005 (Philosophical Psychology 18:561-584): 76% said Jeremy, whose act a
  supercomputer predicted from the laws of nature, robbed the bank of his own free will.
Authored for this project (no human data, marked origin synthetic): five new Gettier cases with two controls (clear
knowledge, clear false belief), and six new side-effect pairs (help vs harm) in the structure of Knobe 2003, whose
original chairman case (82% vs 23% intentional, Analysis 63:190-194) is already in the corpus via Many Labs 2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from askjev.model import HumanDist, Question

NAME = "philosophy_vignettes"
LICENSE = "Vignettes transcribed from the cited studies (research use with citation); new cases authored for this project"
NODE_KNOW = "self.mind.epistemics.knowledge_certainty"
NODE_FREE = "self.mind.big_questions.free_will_reality"
NODE_SIDE = "self.mind.thought_experiments.side_effects"
KNOW = {"knows": "He or she really knows it", "believes": "He or she only believes it"}
YESNO = {"yes": "Yes", "no": "No"}

GETTIER_CAR = ("Bob has a friend, Jill, who has driven a Buick for many years. Bob therefore thinks that Jill drives an "
               "American car. He is not aware, however, that her Buick has recently been stolen, and he is also not "
               "aware that Jill has replaced it with a Pontiac, which is a different kind of American car. Does Bob "
               "really know that Jill drives an American car, or does he only believe it?")
GETTIER_NEW = [  # (item, text, kind): kind gettier | knowledge | false
    ("stopped_clock", "Ana glances at the kitchen clock, which reads 3:00, and concludes that it is three o'clock. It is "
                      "in fact three o'clock, but the clock stopped exactly twelve hours ago and has not moved since. "
                      "Does Ana really know that it is three o'clock, or does she only believe it?", "gettier"),
    ("borrowed_car", "Dev sees his colleague Lee's car in the office car park and concludes that Lee is in the office "
                     "today. Lee lent his car to his sister this morning and she parked it there, but Lee did come in to "
                     "the office by bus. Does Dev really know that Lee is in the office, or does he only believe it?",
     "gettier"),
    ("fake_barns", "Henry is driving through a region where, unknown to him, almost every barn is a fake: a painted "
                   "facade with nothing behind it. He looks at the one real barn in the region and thinks, \"That's a "
                   "barn.\" Does Henry really know that it is a barn, or does he only believe it?", "gettier"),
    ("coins", "Smith has strong evidence that Jones will get the job they both applied for, and he has counted ten "
              "coins in Jones's pocket. He concludes that the man who gets the job has ten coins in his pocket. In fact "
              "Smith himself gets the job, and, without knowing it, Smith also has ten coins in his pocket. Does Smith "
              "really know that the man who gets the job has ten coins in his pocket, or does he only believe it?",
     "gettier"),
    ("dog_sheep", "A farmer looks across a field and sees what looks exactly like a sheep, so he concludes there is a "
                  "sheep in the field. What he is looking at is a large white dog. But behind a hill, out of his "
                  "sight, there really is a sheep in the field. Does the farmer really know that there is a sheep in "
                  "the field, or does he only believe it?", "gettier"),
    ("working_clock", "Ana glances at the kitchen clock, which is working and was set correctly this morning. It reads "
                      "3:00, and she concludes that it is three o'clock. It is three o'clock. Does Ana really know that "
                      "it is three o'clock, or does she only believe it?", "knowledge"),
    ("wrong_clock", "Ana glances at the kitchen clock, which reads 3:00, and concludes that it is three o'clock. The clock "
                    "stopped hours ago; it is actually five o'clock. Does Ana really know that it is three o'clock, or "
                    "does she only believe it?", "false"),
]

UNIVERSE = ("Imagine a universe (Universe A) in which everything that happens is completely caused by whatever happened "
            "before it. This is true from the very beginning of the universe, so what happened in the beginning of the "
            "universe caused what happened next, and so on right up until the present. For example, one day John "
            "decided to have French fries at lunch. Like everything else, this decision was completely caused by what "
            "happened before it. So, if everything in this universe was exactly the same up until John made his "
            "decision, then it had to happen that John would decide to have French fries. ")
FREE_WILL = [  # (item, text, human share saying yes, population/source)
    ("abstract", UNIVERSE + "In Universe A, is it possible for a person to be fully morally responsible for their "
                            "actions?", 0.14,
     "Nichols & Knobe 2007, p. 670, abstract condition: 86% said no"),
    ("bill", UNIVERSE + "In Universe A, a man named Bill has become attracted to his secretary, and he decides that the "
                        "only way to be with her is to kill his wife and three children. He knows that it is impossible "
                        "to escape from his house in the event of a fire. Before he leaves on a business trip, he sets "
                        "up a device in his basement that burns down the house and kills his family. Is Bill fully "
                        "morally responsible for killing his wife and children?", 0.72,
     "Nichols & Knobe 2007, p. 670, concrete condition (Bill): 72% said yes"),
    ("mark", UNIVERSE + "In Universe A, as he has done many times in the past, Mark arranges to cheat on his taxes. Is "
                        "it possible that Mark is fully morally responsible for cheating on his taxes?", 0.23,
     "Nichols & Knobe 2007, low-affect condition, determinist universe (Table 2, p. 676): 23% said yes"),
]
JEREMY = ("Imagine that in the next century we discover all the laws of nature, and we build a supercomputer which can "
          "deduce from these laws of nature and from the current state of everything in the world exactly what will "
          "be happening in the world at any future time. It can look at everything about the way the world is and "
          "predict everything about how it will be with 100% accuracy. Suppose that such a supercomputer existed, and "
          "it looks at the state of the universe at a certain time on March 25, 2150 AD, twenty years before Jeremy "
          "Hall is born. The computer then deduces from this information and the laws of nature that Jeremy will "
          "definitely rob Fidelity Bank at 6:00 PM on January 26, 2195. As always, the supercomputer's prediction is "
          "correct; Jeremy robs Fidelity Bank at 6:00 PM on January 26, 2195. Do you think that, when Jeremy robs the "
          "bank, he acts of his own free will?")

SIDE = [  # (item, agent, goal, harm side effect, help side effect)
    ("mall", "the owner of a development company", "make as much money as possible",
     "destroy a wetland where birds nest", "create jobs for people in the neighborhood"),
    ("recipe", "the owner of a restaurant chain", "cut costs",
     "make the dish less healthy for customers", "make the dish healthier for customers"),
    ("supplier", "a factory manager", "save money on materials",
     "increase pollution in the river", "reduce pollution in the river"),
    ("band", "the leader of a band", "please the crowd at the festival",
     "keep the neighbors awake all night", "cheer up the patients in the hospital next door"),
    ("update", "the head of a software company", "boost this quarter's sales",
     "break the accessibility features blind users rely on", "improve the accessibility features blind users rely on"),
    ("route", "the manager of a delivery company", "make deliveries faster",
     "send heavy trucks past a primary school", "take heavy trucks away from a primary school"),
]


def fetch(raw_dir: Path) -> None:
    """Nothing to download: the vignettes are transcribed from the papers above or written here."""


def _two(yes_key: str, no_key: str, share_yes: float, pop: str, src: str) -> list[HumanDist]:
    return [HumanDist(population=pop, distribution={yes_key: share_yes, no_key: round(1 - share_yes, 4)}, source=src)]


def _q(text, options, node, family, item, *, classic=False, human=None, **meta) -> Question:
    return Question(text=text, primitive="choice", hemisphere="self", kind="evaluative",
                    origin="dataset" if classic else "synthetic", source=NAME, options=options, node_hint=node,
                    license=LICENSE, source_item_id=f"{family}:{item}", human=human or [],
                    meta={"experiment": "philosophy_vignettes", "family": family, "item": item, "classic": classic, **meta})


def normalize(raw_dir: Path) -> Iterator[Question]:
    yield _q(GETTIER_CAR, KNOW, NODE_KNOW, "gettier", "american_car", classic=True, case="gettier")
    for item, text, case in GETTIER_NEW:
        yield _q(text, KNOW, NODE_KNOW, "gettier", item, case=case)
    for item, text, share, src in FREE_WILL:
        yield _q(text, YESNO, NODE_FREE, "free_will", item, classic=True,
                 human=_two("yes", "no", share, "US undergraduates (Nichols & Knobe 2007)", src))
    yield _q(JEREMY, YESNO, NODE_FREE, "free_will", "jeremy", classic=True,
             human=_two("yes", "no", 0.76, "US undergraduates (Nahmias et al. 2005)",
                        "Nahmias, Morris, Nadelhoffer & Turner 2005, Philosophical Psychology 18:561-584, supercomputer scenario, first condition: 76% said he acted of his own free will"))
    for item, agent, goal, harm, helpd in SIDE:
        for valence, effect in (("harm", harm), ("help", helpd)):
            text = (f"An assistant went to {agent} and said: \"We are thinking of a new plan. It will help us {goal}, "
                    f"but it will also {effect}.\" The boss answered: \"I don't care at all about that. I just want to "
                    f"{goal}. Let's go ahead with the plan.\" They went ahead, and sure enough, the plan did {effect}. "
                    f"Did the boss intentionally {effect}?")
            if valence == "help":
                text = text.replace(", but it will also", ", and it will also")
            yield _q(text, YESNO, NODE_SIDE, "side_effect", f"{item}_{valence}", pair=item, valence=valence)
