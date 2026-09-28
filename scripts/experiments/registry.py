"""Every experiment, by family. Each family module exposes EXPERIMENTS: a list of (Spec, run) pairs."""

from __future__ import annotations

import importlib

FAMILIES = ["fam_taste", "fam_person", "fam_resemble", "fam_moral"]

EXPERIMENTS = []
for name in FAMILIES:
    EXPERIMENTS += importlib.import_module(name).EXPERIMENTS
