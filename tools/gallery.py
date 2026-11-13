"""Concept 6: the moon got out. A gallery wall of identical little moon-and-wave prints;
one frame hangs askew with no moon in it, and its moon is rolling away across the floor."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
import comp as C

COLS, ROWS = 7, 5
FW, FH = 112, 112          # frame outer size
GX, GY = 30, 26            # gaps
X0 = (1024 - (COLS * FW + (COLS - 1) * GX)) / 2
Y0 = 52
FLOOR = 770
ODD = (2, 4)               # row, col of the escaped moon's frame

WALL = C.rgb("#e9dfc9")
INDIGO = (29, 43, 88)
CREAM = (240, 230, 205)
WAVE = (232, 236, 240)
FRAME = (36, 26, 20)


def print_tile(with_moon=True, S=8):
    """One print, drawn at S x then reduced: night, moon, a curling wave, a tiny boat."""
    w = 96 * S
    im = Image.new("RGB", (w, w), INDIGO)
    d = ImageDraw.Draw(im)
    if with_moon:
        d.ellipse([60 * S, 12 * S, 84 * S, 36 * S], fill=CREAM)
    # sea band
    d.rectangle([0, 70 * S, w, w], fill=(20, 32, 70))
    # wave: a big curl rising from the left
    pts = []
    for k in range(60):
        t = k / 59
        a = math.pi * 1.0 + t * math.pi * 1.35
        r = 30 - 18 * t
        pts.append(((30 + r * math.cos(a)) * S, (52 + r * math.sin(a)) * S))
    body = [(0, 96 * S), (0, 52 * S)] + pts + [(46 * S, 70 * S), (70 * S, 96 * S)]
    d.polygon(body, fill=(36, 64, 128))
    d.line(pts, fill=WAVE, width=int(3.2 * S))
    for k in range(5):  # foam claws on the crest
        a = math.pi * 1.25 + k * 0.22
        x, y = (30 + 30 * math.cos(a)) * S, (52 + 30 * math.sin(a)) * S
        d.ellipse([x - 2.6 * S, y - 2.6 * S, x + 2.6 * S, y + 2.6 * S], fill=WAVE)
    # boat
    d.polygon([(62 * S, 76 * S), (84 * S, 76 * S), (80 * S, 81 * S), (66 * S, 81 * S)], fill=(10, 10, 16))
    return im.resize((96, 96), Image.LANCZOS)


def framed(tile):
    S = 4
    big = Image.new("RGBA", (FW * S, FH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rectangle([0, 0, FW * S - 1, FH * S - 1], fill=FRAME + (255,))
    d.rectangle([3 * S, 3 * S, FW * S - 3 * S, FH * S - 3 * S], fill=(70, 52, 38, 255))
    d.rectangle([7 * S, 7 * S, FW * S - 7 * S, FH * S - 7 * S], fill=(246, 241, 228, 255))  # mat
    big = big.resize((FW, FH), Image.LANCZOS)
    big.paste(tile, (8, 8))
    return big


wall = C.vgrad([(0, WALL * 0.92), (FLOOR, WALL)])
# soft vignette light on the wall
spot = np.exp(-(((C.XX - 512) / 700) ** 2 + ((C.YY - 380) / 600) ** 2))
img = wall * (0.82 + 0.18 * spot[..., None])

canvas = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
shadow = Image.new("L", (1024, 1024), 0)
sd = ImageDraw.Draw(shadow)
normal = framed(print_tile(True))
odd = framed(print_tile(False)).rotate(-7, resample=Image.BICUBIC, expand=True)
placements = []
for r in range(ROWS):
    for c in range(COLS):
        x = int(X0 + c * (FW + GX))
        y = int(Y0 + r * (FH + GY))
        if (r, c) == ODD:
            placements.append((odd, x - (odd.width - FW) // 2 + 4, y - (odd.height - FH) // 2 + 3))
        else:
            placements.append((normal, x, y))
for im_, x, y in placements:
    sd.rectangle([x + 5, y + 7, x + im_.width + 3, y + im_.height + 5], fill=150)
sh = np.asarray(shadow, np.float32) / 255.0
sh = C.blur(sh, 5)
base = np.asarray(canvas.convert("RGB"), np.float32) / 255.0
base = base * (1 - 0.35 * sh[..., None])
canvas = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
for im_, x, y in placements:
    canvas.alpha_composite(im_, (x, y))
img = np.asarray(canvas.convert("RGB"), np.float32) / 255.0

# floor: dark wooden boards in perspective
floor = (C.YY >= FLOOR).astype(np.float32)
fcol = C.vgrad([(FLOOR, C.rgb("#5a3a24")), (1023, C.rgb("#2a1a10"))])
img = C.over(img, floor, fcol)
img = C.over(img, C.rect(0, FLOOR - 10, 1024, FLOOR), C.rgb("#f4eee0"))       # skirting board
img = C.over(img, C.rect(0, FLOOR - 1, 1024, FLOOR + 2), C.rgb("#3a2618"))
for k in range(-14, 15):
    xb = 512 + k * 40
    xt = 512 + k * 92
    img = C.over(img, C.line([(xb, FLOOR + 2), (xt, 1030)], 1.6), C.rgb("#24160c"), 0.55)

# the escaped moon, rolling right across the floor, with its glow and a reflection
MX, MY, MR = 690, 900, 54
img = C.add_light(img, C.blur(C.circle(MX, MY, MR), 40) * 1.0, C.rgb("#ffe9b0"), 0.55)
img = C.over(img, C.blur(C.ellipse(MX + 6, MY + MR - 2, MR * 0.95, 9), 6), C.rgb("#120a05"), 0.55)
img = C.over(img, C.circle(MX, MY, MR), C.rgb("#f2e6c8"))
for (dx, dy, rr) in [(-14, -12, 9), (12, 8, 6), (-6, 18, 5), (20, -18, 4)]:
    img = C.over(img, C.circle(MX + dx, MY + dy, rr), C.rgb("#d9cba6"), 0.8)
# motion streaks behind it
for k, dy in enumerate((-22, 0, 22)):
    img = C.over(img, C.line([(MX - MR - 18 - 70 + k * 10, MY + dy), (MX - MR - 12, MY + dy)], 3), C.rgb("#f2e6c8"), 0.6)

im = C.finish(img, grain=0.008)
out = sys.argv[1] if len(sys.argv) > 1 else "out/gallery.png"
C.save(im, out)
print(out, os.path.getsize(out))
