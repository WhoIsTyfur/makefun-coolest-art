"""Concept 4: screwing in the sun. Dawn over the sea: the sun is a gigantic light bulb whose
brass screw base sinks into the horizon; a tiny worker on a ladder twists it in."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
import comp as C

HZ = 724
CX, CY, R = 512, 360, 250

NAVY = C.rgb("#0b1230")
INK = C.rgb("#07080f")
GOLD = C.rgb("#ffc04a")
WARM = C.rgb("#ffd98a")
WHITE = C.rgb("#fff8e6")
BRASS = C.rgb("#c18f3e")
BRASS_D = C.rgb("#6e4a1c")
RED = C.rgb("#e2462b")

# ---------------- sky and sea ----------------
img = C.vgrad([(0, C.rgb("#0a0f2a")), (300, C.rgb("#1c1d4a")), (520, C.rgb("#6a2f5a")),
               (640, C.rgb("#d0573c")), (HZ, C.rgb("#f6a23e")), (HZ + 1, C.rgb("#16204a")),
               (1023, C.rgb("#070b1e"))])
rng = np.random.default_rng(21)
for _ in range(90):
    x, y = rng.uniform(0, 1024), rng.uniform(0, 330)
    if math.hypot(x - CX, y - CY) < R + 90:
        continue
    img = C.over(img, C.circle(x, y, rng.choice([0.8, 1.1, 1.6, 2.2])), WHITE, 0.85)

# ---------------- bulb silhouette ----------------
def hw(y):
    t = (y - 470) / (640 - 470)
    return 105 + 125 * (1 - t) ** 2


neck_l = [(CX - hw(y), y) for y in np.linspace(470, 640, 40)]
neck_r = [(CX + hw(y), y) for y in np.linspace(640, 470, 40)]
globe = np.maximum(C.circle(CX, CY, R), C.poly(neck_l + neck_r))

# halo in the sky
halo = C.blur(globe, 40) * 0.9 + C.blur(globe, 140) * 0.9
img = C.add_light(img, halo, C.rgb("#ff9a3c"), 0.85)

# glass: radial warm gradient, brightest around the filament
d = np.sqrt((C.XX - CX) ** 2 + ((C.YY - (CY + 20)) * 1.05) ** 2) / R
glass = np.stack([np.interp(d, [0, 0.35, 0.8, 1.15], [1.0, 1.0, 1.0, 0.97]),
                  np.interp(d, [0, 0.35, 0.8, 1.15], [0.97, 0.86, 0.66, 0.5]),
                  np.interp(d, [0, 0.35, 0.8, 1.15], [0.82, 0.50, 0.24, 0.16])], -1)
img = C.over(img, globe, glass)

# glass stem and support wires, filament coil
stem = C.poly([(CX - 42, 640), (CX + 42, 640), (CX + 16, 470), (CX - 16, 470)])
img = C.over(img, stem, C.rgb("#ffe7b0"), 0.55)
wires = np.maximum(C.line([(CX - 10, 520), (CX - 70, 330)], 3), C.line([(CX + 10, 520), (CX + 70, 330)], 3))
img = C.over(img, wires, C.rgb("#a8743a"), 0.8)
coil = []
for k in range(281):
    t = k / 280
    x = CX - 70 + 140 * t
    y = 330 - 34 * math.sin(math.pi * t) + 9 * math.sin(t * math.pi * 2 * 9)
    coil.append((x, y))
fil = C.line(coil, 4.0)
img = C.add_light(img, C.blur(fil, 10), C.rgb("#fff1c0"), 1.4)
img = C.over(img, fil, WHITE)

# specular highlight on the glass
hl = C.line([(CX + 200 * math.cos(a), CY + 200 * math.sin(a)) for a in np.linspace(math.pi * 1.08, math.pi * 1.38, 30)], 14)
img = C.over(img, C.blur(hl, 2.5), WHITE, 0.55)

# ---------------- screw base ----------------
BY0, BY1 = 636, HZ + 40
base = C.poly([(CX - 108, BY0), (CX + 108, BY0), (CX + 100, BY1), (CX - 100, BY1)])
shade = np.clip(np.abs(C.XX - CX) / 108, 0, 1)
bcol = (BRASS[None, None, :] * (1 - 0.55 * shade[..., None] ** 2) + 0.18 * (1 - shade[..., None]) ** 6)
img = C.over(img, base, bcol)
threads = np.zeros_like(base)
for y in range(BY0 + 22, BY1, 20):
    threads = np.maximum(threads, C.poly([(CX - 120, y), (CX + 120, y + 12), (CX + 120, y + 19), (CX - 120, y + 7)]))
img = C.over(img, threads * base, BRASS_D, 0.85)
collar = C.rect(CX - 116, BY0 - 6, CX + 116, BY0 + 14, r=6)
img = C.over(img, collar, C.rgb("#4c3416"))

# ---------------- sea over the base (the socket is the horizon) ----------------
sea = (C.YY > HZ).astype(np.float32)
seacol = C.vgrad([(HZ, C.rgb("#1b2452")), (1023, C.rgb("#060a1c"))])
img = C.over(img, sea, seacol)
# glow where the base meets the water
img = C.add_light(img, C.blur(C.ellipse(CX, HZ, 160, 6), 12), C.rgb("#ffb050"), 1.2)
# reflection: gold streaks under the bulb
for k in range(60):
    y = HZ + 6 + (k ** 1.35) * 1.6
    if y > 1020:
        break
    spread = 60 + (y - HZ) * 0.55
    for _ in range(2):
        x0 = CX + rng.normal(0, spread * 0.45)
        L = rng.uniform(18, 70) * (0.6 + (y - HZ) / 300)
        a = max(0.0, 1 - (y - HZ) / 330) * rng.uniform(0.5, 1.0)
        img = C.over(img, C.line([(x0 - L / 2, y), (x0 + L / 2, y)], 2.2 + (y - HZ) / 120), GOLD, a)

# ---------------- boat, ladder, worker ----------------
BX, BYb = 742, HZ + 26
boat = C.poly([(BX - 54, BYb - 12), (BX + 50, BYb - 12), (BX + 34, BYb + 4), (BX - 40, BYb + 4)])
img = C.over(img, boat, INK)
LT = (CX + 214, 452)   # ladder top touching the glass
LB1, LB2 = (BX - 22, BYb - 12), (BX + 10, BYb - 12)
lad = np.maximum(C.line([LB1, (LT[0] - 12, LT[1] + 6)], 4), C.line([LB2, (LT[0] + 16, LT[1] + 10)], 4))
for t in np.linspace(0.08, 0.95, 12):
    a = (LB1[0] + (LT[0] - 12 - LB1[0]) * t, LB1[1] + (LT[1] + 6 - LB1[1]) * t)
    b = (LB2[0] + (LT[0] + 16 - LB2[0]) * t, LB2[1] + (LT[1] + 10 - LB2[1]) * t)
    lad = np.maximum(lad, C.line([a, b], 3))
img = C.over(img, lad, INK)
# worker: on the top rungs, both arms up on the glass
fx, fy = LT[0] + 14, LT[1] + 46
body = np.maximum.reduce([
    C.circle(fx + 4, fy - 46, 8.5),
    C.poly([(fx - 7, fy - 36), (fx + 10, fy - 36), (fx + 8, fy - 4), (fx - 6, fy - 4)]),
    C.line([(fx - 3, fy - 4), (fx - 8, fy + 22)], 6), C.line([(fx + 5, fy - 4), (fx + 8, fy + 20)], 6),
    C.line([(fx - 4, fy - 32), (fx - 22, fy - 52), (fx - 26, fy - 70)], 5),
    C.line([(fx + 2, fy - 30), (fx - 18, fy - 30), (fx - 28, fy - 36)], 5),
])
img = C.over(img, body, INK)
img = C.over(img, C.poly([(fx - 7, fy - 38), (fx + 10, fy - 38), (fx + 30, fy - 31), (fx + 9, fy - 30)]), RED)

# twist marks: two curved arrows hugging the glass beside the worker
for r_off, a0, a1 in ((R + 26, -0.10, 0.42), (R + 44, -0.02, 0.36)):
    arc = [(CX + r_off * math.cos(a), CY + r_off * math.sin(a)) for a in np.linspace(a0, a1, 30)]
    img = C.over(img, C.line(arc, 3.2), WHITE, 0.9)
    ex, ey = arc[0]
    tx, ty = arc[1][0] - ex, arc[1][1] - ey
    L = math.hypot(tx, ty)
    tx, ty = tx / L, ty / L
    nx, ny = -ty, tx
    head = C.poly([(ex - tx * 4, ey - ty * 4), (ex + tx * 14 + nx * 9, ey + ty * 14 + ny * 9),
                   (ex + tx * 14 - nx * 9, ey + ty * 14 - ny * 9)])
    img = C.over(img, head, WHITE, 0.9)

im = C.finish(img, grain=0.011)
out = sys.argv[1] if len(sys.argv) > 1 else "out/bulb.png"
C.save(im, out)
print(out, os.path.getsize(out))
