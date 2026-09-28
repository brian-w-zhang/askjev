"""Every experiment, by family. Each family module exposes EXPERIMENTS: a list of (Spec, run) pairs."""

from __future__ import annotations

import importlib
from pathlib import Path

FAMILIES = ["fam_taste", "fam_person", "fam_resemble", "fam_moral", "fam_humor", "fam_judge", "fam_risk",
            "fam_knowledge", "fam_social", "fam_words", "fam_work", "fam_polls", "fam_consistency", "fam_self",
            "fam_perception", "fam_numbers", "fam_minds", "fam_reasoning", "fam_influence", "fam_world", "fam_language", "fam_lexicon", "fam_society", "fam_choices", "fam_recall", "fam_taste2", "fam_self2", "fam_work2", "fam_reading"]

# Cut in the rework pass (docs/16 step 6): the reason stays on record; the experiment no longer runs.
CUT = {
    "person_self_regard": "no gap clears the noise on any of its four scales",
    "person_empathy": "no gap clears the noise (empathizing, systemizing)",
    "person_social_style": "no gap clears the noise on any of its three scales",
    "person_career": "Jev's code equals the quiz-takers' average code; nothing to learn",
    "polls_family_feud": "duplicate of social_family_feud",
    "work_option_order": "duplicate of consistency_option_order",
    "choices_fair_frames": "the question screen hid one side of every framing pair, so no contrast can be computed",
    "taste_intransitive": "its loops came from a bug (options matched by position); corrected as taste_choices_vs_ratings",
}

EXPERIMENTS = []
for name in FAMILIES:
    if (Path(__file__).parent / f"{name}.py").exists():  # families still being written are skipped
        EXPERIMENTS += [(s, f) for s, f in importlib.import_module(name).EXPERIMENTS if s.id not in CUT]
