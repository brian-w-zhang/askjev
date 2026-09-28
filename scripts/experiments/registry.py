"""Every experiment, by family. Each family module exposes EXPERIMENTS: a list of (Spec, run) pairs."""

from __future__ import annotations

import importlib
from pathlib import Path

FAMILIES = ["fam_taste", "fam_person", "fam_resemble", "fam_moral", "fam_humor", "fam_judge", "fam_risk",
            "fam_knowledge", "fam_social", "fam_words", "fam_work", "fam_polls", "fam_consistency", "fam_self",
            "fam_perception", "fam_numbers", "fam_minds", "fam_reasoning", "fam_influence", "fam_world", "fam_language"]

EXPERIMENTS = []
for name in FAMILIES:
    if (Path(__file__).parent / f"{name}.py").exists():  # families still being written are skipped
        EXPERIMENTS += importlib.import_module(name).EXPERIMENTS
