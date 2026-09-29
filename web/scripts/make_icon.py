"""The askjev icon (docs/07-ui.md, Look): a play on TypeSafe's logo. Their mark is interlocking isometric blocks drawn in
heavy black line on hot magenta; ours is a question mark built from the same blocks: a voxel "?" one block deep,
projected isometrically, with a line on every crease and silhouette edge and none on the seams between blocks that
share a face.
- icon.svg: the line art as vectors (what browsers show in the tab; crisp at any pixel density)
- apple-icon.png: the line art at 180 px
- favicon.ico: the fallback for small raster sizes, solid instead (white top, ink side, plum front), because thin
  diagonal lines smear at 16 px
    python3 web/scripts/make_icon.py"""
import math
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw

MAGENTA, INK, PAPER, PLUM = "#E052C8", "#1E1E1E", "#FEFEFE", "#7A2A6E"
GLYPH = [  # the "?" as blocks, top row first: a squared hook, its stem, a gap, the dot
    "XXXX",
    "X..X",
    "...X",
    ".XXX",
    ".X..",
    "....",
    ".X..",
]
LINE = 0.40  # stroke width, in block units: as heavy as TypeSafe's tab icon, and enough to read at 16 css px
APP = Path(__file__).resolve().parents[1] / "src" / "app"

C30, S30 = math.cos(math.pi / 6), 0.5
# Seen as TypeSafe's blocks are: the letterform lies on the left vertical plane and the view is from below, so the
# hook's loop becomes a hexagonal frame with a small cube in its inside corner, like their left piece. Built upside
# down and viewed from above (rows top-first along +y), then mirrored vertically in `proj`.
VOX = {(x, y, 0) for y, row in enumerate(GLYPH) for x, ch in enumerate(row) if ch == "X"}
# the dot sits half a block lower (1.5 blocks of gap): seen from below, one block lets the stem's point touch it
DOT = len(GLYPH) - 1
VOX = {(x, y + 0.5 if y == DOT else y, z) for (x, y, z) in VOX}


def faces():
    """Visible faces seen from +x +y +z, back to front: (orientation, 4 corners, voxel)."""
    out = []
    for (x, y, z) in VOX:
        if (x, y + 1, z) not in VOX: out.append(("y", [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)], (x, y, z)))
        if (x + 1, y, z) not in VOX: out.append(("x", [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x + 1, y, z + 1)], (x, y, z)))
        if (x, y, z + 1) not in VOX: out.append(("z", [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)], (x, y, z)))
    return sorted(out, key=lambda f: (sum(f[2]), {"y": 2, "x": 1, "z": 1}[f[0]]))


F = faces()
edge = lambda a, b: tuple(sorted([a, b]))
# an edge two visible faces of one orientation share is a seam inside one flat surface: no line there
SEAMS = {k for k, n in Counter((o, edge(cs[i], cs[(i + 1) % 4])) for o, cs, _ in F for i in range(4)).items() if n > 1}
proj = lambda p: ((p[0] - p[2]) * C30, p[1] - (p[0] + p[2]) * S30)  # isometric, mirrored top to bottom
PTS = [proj(c) for _, cs, _ in F for c in cs]
X0, X1 = min(p[0] for p in PTS), max(p[0] for p in PTS)
Y0, Y1 = min(p[1] for p in PTS), max(p[1] for p in PTS)


def fit(size: float, pad: float):
    """Scale and offset that center the mark in a square of `size` with `pad` margin (fraction)."""
    s = size * (1 - 2 * pad) / max(X1 - X0, Y1 - Y0)
    return s, (size - (X1 - X0) * s) / 2 - X0 * s, (size - (Y1 - Y0) * s) / 2 - Y0 * s


def svg(size=64, pad=0.02) -> str:
    """Line art on a transparent background, like TypeSafe's own tab icon. With no background to paint over hidden
    lines, each face's lines are masked by every face drawn after it (the faces nearer the viewer). The stroke color
    follows the system theme: white on dark tab bars, ink on light ones."""
    s, ox, oy = fit(size, pad)
    T = lambda p: f"{proj(p)[0] * s + ox:.2f},{proj(p)[1] * s + oy:.2f}"
    polys = [" ".join(T(c) for c in cs) for _, cs, _ in F]
    defs, parts = [], []
    for k, (o, cs, _) in enumerate(F):
        lines = [(cs[i], cs[(i + 1) % 4]) for i in range(4) if (o, edge(cs[i], cs[(i + 1) % 4])) not in SEAMS]
        if not lines:
            continue
        d = " ".join(f"M{T(a)}L{T(b)}" for a, b in lines)
        nearer = polys[k + 1:]
        if nearer:
            holes = "".join(f'<polygon points="{pp}" fill="#000"/>' for pp in nearer)
            defs.append(f'<mask id="m{k}" maskUnits="userSpaceOnUse" x="0" y="0" width="{size}" height="{size}"><rect width="{size}" height="{size}" fill="#fff"/>{holes}</mask>')
            parts.append(f'<path d="{d}" mask="url(#m{k})"/>')
        else:
            parts.append(f'<path d="{d}"/>')
    style = (f"path{{stroke:{INK};stroke-width:{LINE * s:.2f};stroke-linecap:round;fill:none}}"
             f"@media (prefers-color-scheme: dark){{path{{stroke:{PAPER}}}}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}"><style>{style}</style>'
            f'<defs>{"".join(defs)}</defs>{"".join(parts)}</svg>\n')


def raster(size: int, solid: bool, pad: float) -> Image.Image:
    SS = 8
    W = size * SS
    s, ox, oy = fit(W, pad)
    T = lambda p: (proj(p)[0] * s + ox, proj(p)[1] * s + oy)
    im = Image.new("RGB", (W, W), MAGENTA)
    d = ImageDraw.Draw(im)
    lw = max(1, round(LINE * s))
    for o, cs, _ in F:
        d.polygon([T(c) for c in cs], fill={"y": PAPER, "x": INK, "z": PLUM}[o] if solid else MAGENTA)
        if solid:
            continue
        for i in range(4):
            a, b = cs[i], cs[(i + 1) % 4]
            if (o, edge(a, b)) in SEAMS:
                continue
            d.line([T(a), T(b)], fill=INK, width=lw)
            for q in (T(a), T(b)):
                d.ellipse([q[0] - lw / 2, q[1] - lw / 2, q[0] + lw / 2, q[1] + lw / 2], fill=INK)
    return im.resize((size, size), Image.LANCZOS)


(APP / "icon.svg").write_text(svg())
raster(180, solid=False, pad=0.14).save(APP / "apple-icon.png")
# RGBA entries (Next.js can't decode an .ico of 24-bit RGB images), each size drawn at its own resolution
icons = [raster(k, solid=True, pad=0.05).convert("RGBA") for k in (16, 32, 48, 64)]
icons[-1].save(APP / "favicon.ico", sizes=[im.size for im in icons], append_images=icons[:-1])
print("wrote", APP / "icon.svg", APP / "apple-icon.png", APP / "favicon.ico")
