"""Concept 2: the daylight torch. A tiny figure on a night hill points a flashlight at the
sky; where the beam lands, the night is not lit up: it opens onto blue daytime sky."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw
from flat import Canvas, save_png, hexc

NIGHT_TOP = np.array([10, 14, 34], float)
NIGHT_LOW = np.array([30, 40, 82], float)
DAY_TOP = np.array([86, 160, 222], float)
DAY_LOW = np.array([178, 220, 242], float)
CREAM = "#f4ead2"
INK = "#0b0b12"
RED = "#e0452c"
WHITE = "#fbfaf5"

S = 4
N = 1024 * S
c = Canvas("#000000")

# night sky: vertical gradient, posterised into soft bands
yy = np.linspace(0, 1, N)[:, None]
night = NIGHT_TOP + (NIGHT_LOW - NIGHT_TOP) * (yy ** 1.4)
night = np.repeat(night[:, None, :], N, axis=1).reshape(N, N, 3)
c.img = Image.fromarray(night.astype(np.uint8)).convert("RGBA")
c.d = ImageDraw.Draw(c.img)

# stars
rng = np.random.default_rng(11)
CX, CY, R = 640, 330, 215
for _ in range(140):
    x, y = rng.uniform(8, 1016), rng.uniform(8, 760)
    if math.hypot(x - CX, y - CY) < R + 18:
        continue
    r = rng.choice([0.9, 1.3, 1.8, 2.6], p=[.5, .28, .15, .07])
    c.circle(x, y, r, CREAM)

# hand point of the figure
HX, HY = 318, 742

# beam: cone from hand to tangent points of the circle
dx, dy = CX - HX, CY - HY
dist = math.hypot(dx, dy)
ang = math.atan2(dy, dx)
half = math.asin(R / dist)
L = math.sqrt(dist * dist - R * R)
p1 = (HX + L * math.cos(ang - half), HY + L * math.sin(ang - half))
p2 = (HX + L * math.cos(ang + half), HY + L * math.sin(ang + half))
beam = c.layer((255, 236, 190))
bd = ImageDraw.Draw(beam)
bd.polygon([(HX * S, HY * S), (p1[0] * S, p1[1] * S), (CX * S, CY * S), (p2[0] * S, p2[1] * S)],
           fill=(255, 236, 190, 46))
c.paste_layer(beam)

# day disc: its own gradient, clipped to the circle
day = DAY_TOP + (DAY_LOW - DAY_TOP) * np.clip((yy * 1024 - (CY - R)) / (2 * R), 0, 1)
day = np.repeat(day[:, None, :], N, axis=1).reshape(N, N, 3).astype(np.uint8)
dayimg = Image.fromarray(day).convert("RGBA")
dd = ImageDraw.Draw(dayimg)


def dcirc(x, y, r, col):
    dd.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=hexc(col))


# a cloud and birds inside the day
for (x, y, r) in [(560, 360, 52), (615, 330, 70), (690, 345, 58), (742, 372, 40), (650, 385, 50), (590, 392, 40)]:
    dcirc(x, y, r, WHITE)
dd.rectangle([560 * S, 380 * S, 742 * S, 412 * S], fill=hexc(WHITE))
for (bx, by, bs) in [(700, 230, 13), (735, 252, 9), (675, 262, 7)]:
    dd.line([((bx - bs) * S, (by - bs * 0.45) * S), (bx * S, by * S), ((bx + bs) * S, (by - bs * 0.45) * S)],
            fill=hexc(INK), width=int(2.4 * S), joint="curve")
mask = Image.new("L", (N, N), 0)
ImageDraw.Draw(mask).ellipse([(CX - R) * S, (CY - R) * S, (CX + R) * S, (CY + R) * S], fill=255)
c.img.paste(dayimg, (0, 0), mask)
c.d = ImageDraw.Draw(c.img)

# soft rim glow at the edge of the disc
glow = c.layer((255, 240, 200))
gd = ImageDraw.Draw(glow)
gd.ellipse([(CX - R - 10) * S, (CY - R - 10) * S, (CX + R + 10) * S, (CY + R + 10) * S],
           outline=(255, 240, 200, 90), width=int(10 * S))
c.paste_layer(glow, blur=6)

# hill
hill = [(0, 1024), (0, 820)]
for x in range(0, 1025, 16):
    y = 790 + 0.00012 * (x - 300) ** 2 * 1.0 + (0 if x < 300 else 0)
    hill.append((x, min(y, 1024)))
hill += [(1024, 1024)]
c.poly(hill, INK)

# tiny figure standing on the hill top, arm out holding a torch toward the disc
fx, fy = 300, 790   # feet
c.line([(fx - 4, fy), (fx - 3, fy - 22)], INK, 5)
c.line([(fx + 4, fy), (fx + 3, fy - 22)], INK, 5)
c.poly([(fx - 8, fy - 20), (fx + 8, fy - 20), (fx + 7, fy - 48), (fx - 7, fy - 48)], INK)
c.circle(fx, fy - 56, 7.5, INK)
c.poly([(fx - 8, fy - 47), (fx + 8, fy - 47), (fx - 2, fy - 40), (fx - 22, fy - 36)], RED)  # scarf
c.line([(fx + 6, fy - 44), (HX - 6, HY + 4)], INK, 4.5)
c.line([(HX - 8, HY + 5), (HX + 2, HY - 1)], INK, 6)   # torch body
c.circle(HX + 1, HY - 1, 3, CREAM)

im = c.finish(grain=4.5)
out = sys.argv[1] if len(sys.argv) > 1 else "out/torch.png"
save_png(im, out)
print(out, os.path.getsize(out))
