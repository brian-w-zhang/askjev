"""The askjev icon (docs/07-ui.md, Look), drawn on a 32-pixel grid so it stays crisp at favicon size:
three dithered clusters in the hemisphere colors (World top, Machine left, Self right) joined to a white
root by pink branches, on an ink square. Writes src/app/icon.svg, src/app/favicon.ico and
src/app/apple-icon.png.   python3 web/scripts/make_icon.py"""
from pathlib import Path
from PIL import Image

INK, PAPER, PINK = "#1E1E1E", "#FEFEFE", "#FF78F2"
WORLD, SELF, MACHINE = "#7D89E6", "#F386A1", "#E8663D"
N = 32
px: dict[tuple[int, int], str] = {}

def line(x0, y0, x1, y1, c):
    steps = max(abs(x1 - x0), abs(y1 - y0))
    for i in range(steps + 1):
        px[(round(x0 + (x1 - x0) * i / steps), round(y0 + (y1 - y0) * i / steps))] = c

def cluster(cx, cy, r, c):
    # a solid core with a checker-dithered rim, like the nebula's halftone
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if d <= r - 1.3 or (d <= r + 0.3 and (x + y) % 2 == 0):
                px[(x, y)] = c

root = (16, 18)
hemis = [((16, 7), WORLD), ((7, 24), MACHINE), ((25, 24), SELF)]
for (hx, hy), _ in hemis:
    line(root[0], root[1], hx, hy, PINK)
for (hx, hy), c in hemis:
    cluster(hx, hy, 4, c)
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        px[(root[0] + dx, root[1] + dy)] = PAPER

app = Path(__file__).resolve().parent.parent / "src" / "app"
rects = "".join(f'<rect x="{x}" y="{y}" width="1" height="1" fill="{c}"/>' for (x, y), c in sorted(px.items()) if 0 <= x < N and 0 <= y < N)
(app / "icon.svg").write_text(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" shape-rendering="crispEdges">'
    f'<rect width="{N}" height="{N}" fill="{INK}"/>{rects}</svg>\n'
)
img = Image.new("RGBA", (N, N), INK)
for (x, y), c in px.items():
    if 0 <= x < N and 0 <= y < N:
        img.putpixel((x, y), Image.new("RGB", (1, 1), c).getpixel((0, 0)))
img.resize((64, 64), Image.NEAREST).save(app / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
img.resize((180, 180), Image.NEAREST).save(app / "apple-icon.png")
img.resize((256, 256), Image.NEAREST).save(Path("/private/tmp/claude-501/-Users-junzhang-Projects-askjev/34611009-f72c-4bb2-9589-d4ed63ccce93/scratchpad/icon_preview.png"))
print("wrote icon.svg, favicon.ico, apple-icon.png")
