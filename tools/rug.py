"""Concept 3: sweeping the stars under the rug. The night landscape is a rug; its corner is
folded back and a tiny figure sweeps the last stars into a glowing heap beneath it."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import ImageDraw
from flat import Canvas, save_png, hexc

SKY = "#121a3a"
LAND = "#1d3a4a"
LAND2 = "#183140"
RED = "#c8412e"
GOLD = "#f2c14e"
CREAM = "#efe2c4"
UNDER = "#d9c9a3"
INK = "#0a0a10"
FLOOR = "#07070c"

c = Canvas(SKY)
rng = np.random.default_rng(5)
# a handful of stars still in the sky
for _ in range(14):
    c.circle(rng.uniform(40, 990), rng.uniform(40, 520), rng.choice([1.2, 1.8, 2.4]), CREAM)

HZ, FRONT = 600, 930
c.rect(0, FRONT, 1024, 1024, FLOOR)
# land/rug body with soft hills on the horizon
land = [(0, FRONT), (0, HZ + 10)]
for x in range(0, 1025, 8):
    land.append((x, HZ + 18 * math.sin(x / 140.0) + 10 * math.sin(x / 53.0 + 1)))
land.append((1024, FRONT))
c.poly(land, LAND)
for k, y in enumerate(range(HZ + 70, FRONT - 70, 46)):
    c.rect(0, y, 1024, y + 22, LAND2)
# rug border stripes near the front edge
c.rect(0, FRONT - 64, 1024, FRONT - 52, GOLD)
c.rect(0, FRONT - 46, 1024, FRONT - 22, RED)
for x in range(8, 1024, 28):
    c.poly([(x, FRONT - 40), (x + 7, FRONT - 34), (x, FRONT - 28), (x - 7, FRONT - 34)], GOLD)
c.rect(0, FRONT - 16, 1024, FRONT - 8, GOLD)
# fringe
for x in range(4, 1024, 9):
    c.line([(x, FRONT), (x + 1, FRONT + 22)], CREAM, 2.2)

# fold: corner (0, FRONT) folded across line P-Q
P, Q = (0.0, 640.0), (360.0, FRONT + 0.0)
cut = [P, (0, FRONT + 40), (Q[0] + 30, FRONT + 40), Q]
c.poly(cut, FLOOR)


def reflect(pt):
    (x0, y0), (x1, y1) = P, Q
    dx, dy = x1 - x0, y1 - y0
    t = ((pt[0] - x0) * dx + (pt[1] - y0) * dy) / (dx * dx + dy * dy)
    fx, fy = x0 + t * dx, y0 + t * dy
    return (2 * fx - pt[0], 2 * fy - pt[1])


# heap of gold stars glowing in the hollow under the fold
glow = c.layer((255, 200, 90))
gd = ImageDraw.Draw(glow)
gd.ellipse([20 * 4, 760 * 4, 330 * 4, 1010 * 4], fill=(255, 200, 90, 120))
c.paste_layer(glow, blur=40)


def star(cx, cy, r, col, rot=0.0):
    pts = []
    for i in range(10):
        a = rot + i * math.pi / 5 - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    c.poly(pts, col)


heap = []
for _ in range(80):
    x = rng.normal(150, 60)
    y = 925 - abs(rng.normal(0, 1)) * 40 - max(0, 80 - abs(x - 150)) * 0.5 + rng.uniform(-6, 6)
    heap.append((x, y, rng.uniform(7, 15), rng.uniform(0, 1)))
for x, y, r, rot in sorted(heap, key=lambda h: h[1]):
    if 0 < x < 330:
        star(x, y, r, GOLD if rot > 0.25 else CREAM, rot)

# folded flap (underside of the rug) with its fringe
corner = (0.0, FRONT + 0.0)
tip = reflect(corner)
c.poly([P, Q, tip], UNDER)
# fringe along the flap's former bottom edge (Q -> tip)
n = 22
for i in range(1, n):
    t = i / n
    x = Q[0] + (tip[0] - Q[0]) * t
    y = Q[1] + (tip[1] - Q[1]) * t
    ex, ey = tip[0] - Q[0], tip[1] - Q[1]
    L = math.hypot(ex, ey)
    nx, ny = ey / L, -ex / L   # outward normal (away from the fold line)
    c.line([(x, y), (x + nx * 22, y + ny * 22)], CREAM, 2.2)
# shading line along the fold
c.line([P, Q], "#b7a47c", 3)

# trail of swept stars from the right toward the heap
for i in range(12):
    x = 420 + i * 38 + rng.uniform(-8, 8)
    y = 905 - rng.uniform(0, 14)
    star(x, y, rng.uniform(4, 7), GOLD, rng.uniform(0, 1))

# tiny figure with a broom, sweeping leftwards, standing on the rug's front border
fx, fy = 400, 905
c.line([(fx - 4, fy), (fx - 1, fy - 22)], INK, 5)
c.line([(fx + 5, fy), (fx + 3, fy - 22)], INK, 5)
c.poly([(fx - 8, fy - 20), (fx + 8, fy - 20), (fx + 6, fy - 48), (fx - 6, fy - 48)], INK)
c.circle(fx + 1, fy - 56, 7.5, INK)
c.poly([(fx - 6, fy - 48), (fx + 6, fy - 48), (fx + 22, fy - 44), (fx + 8, fy - 41)], RED)
c.line([(fx + 22, fy - 62), (fx - 26, fy - 2)], "#8a6a3a", 3.5)     # broom handle
c.poly([(fx - 24, fy - 6), (fx - 40, fy + 2), (fx - 30, fy + 4), (fx - 16, fy - 2)], "#c9a35a")  # bristles
c.line([(fx - 4, fy - 40), (fx + 8, fy - 46)], INK, 4)
c.line([(fx + 2, fy - 34), (fx - 8, fy - 20)], INK, 4)

im = c.finish(grain=4.5)
out = sys.argv[1] if len(sys.argv) > 1 else "out/rug.png"
save_png(im, out)
print(out, os.path.getsize(out))
