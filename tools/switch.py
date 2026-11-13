"""Concept 1: the day switch. A wall switch set into the sky; left of the seam it is
night, right of it it is day; a tiny figure at the top of a ladder has just flipped it."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from flat import Canvas, save_png, hexc
from PIL import Image, ImageDraw
import numpy as np

NIGHT = "#16203f"
NIGHT2 = "#24305a"
DAY = "#f3b23c"
DAY2 = "#f7d27a"
CREAM = "#efe5cf"
SHADE = "#cfc3a7"
INK = "#15131a"
RED = "#d9442b"

c = Canvas(NIGHT)
SEAM = 512
# day half
c.rect(SEAM, 0, 1024, 1024, DAY)
# soft bands in the day sky (flat, posterised)
for i, y in enumerate(range(0, 820, 82)):
    if i % 2:
        c.rect(SEAM, y, 1024, y + 82, DAY2 if i > 6 else DAY)
# sun on the day side, half cut by the seam? keep it whole, low right
c.circle(800, 300, 70, RED)
# stars on the night side
rng = np.random.default_rng(3)
for _ in range(70):
    x, y = rng.uniform(20, SEAM - 10), rng.uniform(20, 760)
    if 350 < x and 230 < y < 700:
        continue
    r = rng.choice([1.2, 1.6, 2.2, 3.0], p=[.45, .3, .17, .08])
    c.circle(x, y, r, CREAM)
c.circle(170, 210, 46, CREAM)
c.circle(190, 196, 44, NIGHT)  # crescent

# switch plate centred on the seam
PX0, PY0, PX1, PY1 = 392, 250, 632, 640
c.rect(PX0 + 10, PY0 + 14, PX1 + 10, PY1 + 14, (0, 0, 0, 90), r=26)  # drop shadow
c.rect(PX0, PY0, PX1, PY1, CREAM, r=26)
c.rect(PX0 + 8, PY0 + 8, PX1 - 8, PY1 - 8, CREAM, r=20)
# screws
for sy in (PY0 + 40, PY1 - 40):
    c.circle(512, sy, 11, SHADE)
    c.line([(504, sy + 6), (520, sy - 6)], INK, 3)
# toggle slot and toggle (flipped up = on)
c.rect(470, 372, 554, 528, SHADE, r=16)   # bezel
c.rect(480, 382, 544, 518, INK, r=12)     # slot
# lever: dark outline, then light body with a shaded right side, tip up (= on)
c.poly([(489, 452), (535, 452), (549, 318), (475, 318)], INK)
c.poly([(494, 448), (530, 448), (543, 324), (481, 324)], "#fbf6ea")
c.poly([(512, 448), (530, 448), (543, 324), (512, 324)], SHADE)
c.rect(473, 306, 551, 334, INK, r=12)
c.rect(477, 310, 547, 330, "#fbf6ea", r=9)

# ground: dark hills over both halves
c.poly([(0, 1024), (0, 800), (140, 770), (300, 790), (470, 760), (640, 785), (820, 760),
        (1024, 790), (1024, 1024)], INK)
# a house with a lit window on each side
for hx, lit in ((200, True), (840, False)):
    c.poly([(hx - 26, 800), (hx, 776), (hx + 26, 800), (hx + 26, 830), (hx - 26, 830)], INK)
    if lit:
        c.rect(hx - 7, 806, hx + 7, 818, DAY)

# ladder from the ground to under the plate
L0, L1 = (560, 812), (548, 560)
R0, R1 = (600, 812), (588, 560)
c.line([L0, L1], INK, 5)
c.line([R0, R1], INK, 5)
for t in np.linspace(0.06, 0.96, 10):
    a = (L0[0] + (L1[0] - L0[0]) * t, L0[1] + (L1[1] - L0[1]) * t)
    b = (R0[0] + (R1[0] - R0[0]) * t, R0[1] + (R1[1] - R0[1]) * t)
    c.line([a, b], INK, 4)
# tiny figure on the top rungs, arm up to the toggle
fx, fy = 566, 540
c.circle(fx, fy - 40, 9, INK)                         # head
c.poly([(fx - 9, fy - 30), (fx + 9, fy - 30), (fx + 8, fy + 2), (fx - 8, fy + 2)], INK)  # body
c.line([(fx - 4, fy), (fx - 6, fy + 26)], INK, 6)     # legs
c.line([(fx + 4, fy), (fx + 8, fy + 22)], INK, 6)
c.line([(fx - 7, fy - 26), (fx - 30, fy - 64), (fx - 40, fy - 104)], INK, 5)  # arm up
c.line([(fx + 7, fy - 26), (fx + 16, fy - 6)], INK, 5)
# red scarf for a spot of colour
c.poly([(fx - 9, fy - 32), (fx + 9, fy - 32), (fx + 28, fy - 24), (fx + 8, fy - 24)], RED)

im = c.finish(grain=5)
out = sys.argv[1] if len(sys.argv) > 1 else "out/switch.png"
save_png(im, out)
print(out, os.path.getsize(out))
