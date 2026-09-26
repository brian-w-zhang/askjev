"""Tile ui_shots.mjs output into contact sheets: python3 web/scripts/ui_sheet.py <outdir> <label>"""
import sys
from pathlib import Path
from PIL import Image

out, label = Path(sys.argv[1]), sys.argv[2]
poses = ["home", "high", "level", "side-up", "close", "far"]
for theme in ["light", "dark"]:
    W = Image.new("RGB", (1920, 800), "white")
    for i, n in enumerate(poses):
        f = out / f"{label}_{theme}_{n}.png"
        if f.exists():
            W.paste(Image.open(f).resize((640, 400)), ((i % 3) * 640, (i // 3) * 400))
    W.save(out / f"{label}_{theme}_sheet.png")
print("sheets in", out)
