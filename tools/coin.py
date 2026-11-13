"""Concept 5: daylight saving. At dusk the sun is a huge gold coin sliding into a coin slot cut
in the horizon; a tiny banker in a bowler hat stands on its rim, pressing it in."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import comp as C

# variant knobs (defaults = the chosen piece); see README
VAR = dict(R=318, HZ=724, STARS=0, RAYS=0.10, FIG=1.2, REFL=0)
for k in VAR:
    if os.environ.get('COIN_' + k):
        VAR[k] = type(VAR[k])(os.environ['COIN_' + k])
HZ = VAR['HZ']
CX, R = 500, VAR['R']
CY = HZ - 74 + (R - 318) // 3
TILT = math.radians(20)            # turn about the vertical axis: the face narrows, the edge shows
KX = math.cos(TILT)
THICK = 30                          # visible edge thickness, px, toward the right
INK = C.rgb("#07080f")
WHITE = C.rgb("#fff8e6")
GOLD = C.rgb("#ffc24a")
RED = C.rgb("#e2462b")
FONT = "C:/Windows/Fonts/georgiab.ttf"


def shift(a, dx, dy):
    return np.roll(np.roll(a, dy, 0), dx, 1)


def emboss(mask, d=2, soft=1.0):
    m = C.blur(mask, soft)
    return shift(m, -d, -d) - shift(m, d, d)


def glyph_mask(draw):
    big = Image.new("L", (C.N * C.SS, C.N * C.SS), 0)
    draw(big)
    return np.asarray(big.resize((C.N, C.N), Image.BOX), np.float32) / 255.0


def text_arc(txt, r, a_mid, size):
    font = ImageFont.truetype(FONT, size * C.SS)

    def draw(big):
        widths = [font.getlength(ch) / C.SS for ch in txt]
        track = size * 0.14
        total = sum(widths) + track * (len(txt) - 1)
        ang = a_mid - (total / r) / 2
        for ch, w in zip(txt, widths):
            a = ang + (w / 2) / r
            g = Image.new("L", (int(size * 2 * C.SS), int(size * 2 * C.SS)), 0)
            ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=font, fill=255, anchor="mm")
            rot = g.rotate(-math.degrees(a) - 90, resample=Image.BICUBIC)
            x, y = CX + r * math.cos(a), CY + r * math.sin(a)
            big.paste(255, (int(x * C.SS - rot.width / 2), int(y * C.SS - rot.height / 2)), rot)
            ang += (w + track) / r
    return glyph_mask(draw)


def text_at(txt, x, y, size):
    font = ImageFont.truetype(FONT, size * C.SS)
    return glyph_mask(lambda big: ImageDraw.Draw(big).text((x * C.SS, y * C.SS), txt, font=font, fill=255, anchor="mm"))


def squash(a):
    """Map a face drawn face-on onto the tilted coin: x -> CX + (x - CX) * KX."""
    src = CX + (np.arange(C.N, dtype=np.float32) - CX) / KX
    i0 = np.clip(np.floor(src).astype(int), 0, C.N - 2)
    f = np.clip(src - i0, 0, 1)
    if a.ndim == 2:
        return a[:, i0] * (1 - f) + a[:, i0 + 1] * f
    return a[:, i0, :] * (1 - f)[None, :, None] + a[:, i0 + 1, :] * f[None, :, None]


# ---------------- sky and sea ----------------
img = C.vgrad([(0, C.rgb("#080b22")), (250, C.rgb("#181844")), (460, C.rgb("#552858")),
               (610, C.rgb("#c24c3c")), (HZ, C.rgb("#f4a446")), (HZ + 1, C.rgb("#141d46")),
               (1023, C.rgb("#050918"))])
rng = np.random.default_rng(4)
# stars that are loose change: most are pinpoints, the nearer ones are small tilted coins
SILVER = C.rgb("#dfe4ee")
for _ in range(90):
    x, y = rng.uniform(0, 1024), rng.uniform(0, 300)
    if math.hypot(x - CX, y - CY) < R + 80:
        continue
    img = C.over(img, C.circle(x, y, rng.choice([0.8, 1.1, 1.4, 1.8] if VAR["STARS"] else [0.8, 1.1, 1.6, 2.2])), WHITE, 0.85)
placed = []
while len(placed) < 26 * VAR["STARS"]:
    x, y = rng.uniform(30, 994), rng.uniform(24, 470)
    if math.hypot(x - CX, y - CY) < R + 90 or any(math.hypot(x - a, y - b) < 70 for a, b, _ in placed):
        continue
    r = float(rng.choice([4.0, 5.0, 6.5, 8.0, 10.0], p=[.3, .28, .2, .14, .08]))
    placed.append((x, y, r))
for x, y, r in placed:
    tilt = rng.uniform(0.45, 1.0)
    rot = rng.uniform(0, math.pi)
    gold = rng.uniform() < 0.6
    base = C.rgb("#ffcf5c") if gold else SILVER
    dark = C.rgb("#9a6a1c") if gold else C.rgb("#7c8496")
    ca, sa = math.cos(rot), math.sin(rot)

    def ell(rx, ry, ox=0.0, oy=0.0):
        pts = []
        for a in np.linspace(0, 2 * math.pi, 40):
            ex, ey = rx * math.cos(a) + ox, ry * math.sin(a) + oy
            pts.append((x + ex * ca - ey * sa, y + ex * sa + ey * ca))
        return C.poly(pts)

    img = C.add_light(img, C.blur(C.circle(x, y, r), r * 1.4), base, 0.45)
    img = C.over(img, ell(r, r * tilt, 0, r * 0.18 * (1 - tilt) + 0.6), dark)      # edge
    img = C.over(img, ell(r, r * tilt), base)                                        # face
    img = C.over(img, np.clip(ell(r, r * tilt) - ell(r * 0.74, r * tilt * 0.74), 0, 1), dark, 0.45)  # rim
    img = C.over(img, ell(r * 0.32, r * tilt * 0.32, -r * 0.3, -r * tilt * 0.3), WHITE, 0.8)  # glint

# long sunset cloud streaks behind the coin, lit from below
for (cy_, x0_, x1_, th) in ((560, -40, 300, 10), (585, 60, 380, 7), (520, 720, 1080, 9), (600, 650, 1000, 7), (470, -60, 220, 6)):
    m = C.blur(C.line([(x0_, cy_), (x1_, cy_ - 6)], th), 2.0)
    img = C.over(img, m, C.rgb("#3a1f3e"), 0.85)
    img = C.over(img, C.blur(C.line([(x0_ + 20, cy_ + th * 0.45), (x1_ - 20, cy_ + th * 0.45 - 6)], th * 0.35), 1.2),
                 C.rgb("#ff9c5a"), 0.75)

above = (C.YY < HZ - 2).astype(np.float32)
# faint rays fanning out from behind the coin
theta = np.arctan2(C.YY - CY, C.XX - CX)
dist = np.sqrt((C.XX - CX) ** 2 + (C.YY - CY) ** 2)
rays = np.clip((np.sin(theta * 34) - 0.25) * 2.0, 0, 1) * np.clip((dist - R) / 60, 0, 1) * np.exp(-(dist - R) / 420)
img = C.add_light(img, C.blur(rays, 1.5) * above, C.rgb("#ffb070"), VAR["RAYS"])
face = C.ellipse(CX, CY, R * KX, R)
edge = np.clip(C.ellipse(CX + THICK, CY, R * KX, R) - face, 0, 1)
coin_all = np.clip(face + edge + C.rect(CX, CY - R, CX + THICK, CY + R) * 0, 0, 1)
# fill the band between the two ellipses' top and bottom points
band = np.zeros_like(face)
for k in range(THICK + 1):
    band = np.maximum(band, C.ellipse(CX + k, CY, R * KX, R)) if k % 6 == 0 or k == THICK else band
coin_all = np.maximum(face, band)
edge = np.clip(coin_all - face, 0, 1)
img = C.add_light(img, (C.blur(coin_all * above, 36) * 0.8 + C.blur(coin_all * above, 140) * 1.0) * above,
                  C.rgb("#ff9a3c"), 0.85)

# ---------------- the edge: darker gold with reeding ----------------
ecol = np.stack([0.66 + 0 * C.XX, 0.42 + 0 * C.XX, 0.12 + 0 * C.XX], -1)
img = C.over(img, edge * above, ecol)
reeds = np.zeros_like(face)
for k in range(-60, 61):
    a = math.asin(k / 61.0)
    y = CY + R * math.sin(a)
    x = CX + R * KX * math.cos(a)
    reeds = np.maximum(reeds, C.line([(x + 1, y), (x + THICK - 1, y)], 1.6))
img = C.over(img, reeds * edge * above, C.rgb("#3e2606"), 0.55)
img = C.add_light(img, C.blur(edge, 3) * edge * np.clip((CY - C.YY) / R, 0, 1) * above, C.rgb("#ffd27a"), 0.35)

# ---------------- face (drawn face-on, then squashed onto the tilt) ----------------
disc = C.circle(CX, CY, R)
u = ((C.XX - CX) * -0.55 + (C.YY - CY) * -0.83) / R
rr = np.sqrt((C.XX - CX) ** 2 + (C.YY - CY) ** 2) / R
lum = 0.66 + 0.26 * u + 0.05 * np.cos(rr * 20)
fcol = np.stack([np.clip(1.05 * lum + 0.12, 0, 1), np.clip(0.80 * lum, 0, 1), np.clip(0.30 * lum - 0.02, 0, 1)], -1)

rim = np.clip(C.circle(CX, CY, R) - C.circle(CX, CY, R - 28), 0, 1)
lip = np.clip(C.circle(CX, CY, R - 36) - C.circle(CX, CY, R - 40), 0, 1)
emb_c = (CX, CY - 126)
emblem = np.clip(C.circle(*emb_c, 46) - C.circle(*emb_c, 39), 0, 1) + C.circle(*emb_c, 26)
for k in range(16):
    a = 2 * math.pi * k / 16
    r0, r1 = 56, (80 if k % 2 == 0 else 70)
    emblem = np.maximum(emblem, C.line([(emb_c[0] + r0 * math.cos(a), emb_c[1] + r0 * math.sin(a)),
                                        (emb_c[0] + r1 * math.cos(a), emb_c[1] + r1 * math.sin(a))], 7))
letters = text_arc("IN DAYLIGHT WE TRUST", R - 66, -math.pi / 2, 33)
value = text_at("ONE DAY", CX, CY + 8, 46)
relief = np.clip(rim + lip + emblem + letters + value, 0, 1)
e = emboss(relief, 2, 1.0)
facec = fcol * np.clip(1.0 + 1.7 * e[..., None], 0.4, 1.7) * (1.0 + 0.08 * relief[..., None])
sheen = C.blur(C.line([(CX - 250, CY - 110), (CX - 110, CY - 250)], 30), 16)
facec = facec + 0.32 * sheen[..., None] * WHITE
facec = squash(facec)
img = C.over(img, face * above, facec)
img = C.over(img, np.clip(C.ellipse(CX, CY, R * KX + 1.5, R + 1.5) - C.ellipse(CX, CY, R * KX - 1.5, R - 1.5), 0, 1) * above,
             C.rgb("#5a3a0a"), 0.8)

# the coin darkens as it goes into the slot
into = np.clip((C.YY - (HZ - 46)) / 46, 0, 1) ** 1.5 * coin_all * above
img = img * (1 - 0.75 * into[..., None])

# ---------------- the slot and the sea ----------------
SX0, SX1 = CX - R * KX - 30, CX + R * KX + THICK + 30
sea = (C.YY >= HZ - 2).astype(np.float32)
seacol = C.vgrad([(HZ, C.rgb("#1b2452")), (1023, C.rgb("#050918"))])
img = C.over(img, sea, seacol)
img = C.over(img, C.rect(SX0 - 6, HZ - 6, SX1 + 6, HZ + 7, r=6), C.rgb("#2b3150"))
img = C.over(img, C.rect(SX0, HZ - 3, SX1, HZ + 3, r=3), INK)
img = C.add_light(img, C.blur(C.rect(SX0, HZ - 7, SX1, HZ - 5), 3), C.rgb("#ffb050"), 0.9)

# woodblock sea: rows of scallop wavelets, larger toward the viewer, gold in the reflection
def scallops(d, s):
    i = 0
    while True:
        y = HZ + 12 + 2.3 * i ** 1.55
        if y > 1040:
            break
        w = 5 + 1.15 * i
        h = w * 0.42
        lw = max(1, int(round((0.9 + i * 0.07) * s)))
        x = -w * (i % 2) - 2 * w
        while x < 1024 + 2 * w:
            pts = [((x + w * math.cos(a)) * s, (y - h * math.sin(a)) * s) for a in np.linspace(0, math.pi, 9)]
            d.line(pts, fill=255, width=lw)
            x += 2 * w
        i += 1


waves = C._mask(scallops) * sea
spread = (95 + (C.YY - HZ).clip(0) * 0.6) if VAR["REFL"] else (70 + (C.YY - HZ).clip(0) * 0.55)
refl = np.exp(-((C.XX - CX - THICK / 2) / spread) ** 2) * np.clip(1 - (C.YY - HZ) / 330, 0, 1)
wcol = C.rgb("#34457e")[None, None, :] * (1 - refl[..., None]) + GOLD[None, None, :] * refl[..., None]
img = C.over(img, waves, wcol, 0.9 if VAR["REFL"] else 0.85)
if VAR["REFL"]:
    img = C.add_light(img, waves * refl, C.rgb("#ffd27a"), 0.5)
img = C.add_light(img, C.blur(refl * sea, 6), C.rgb("#ff9a3c"), 0.18)

# the brass plaque under the slot: NIGHT DEPOSIT
PX, PY, PW, PH = CX + THICK / 2, HZ + 58, 178, 30
plate = C.rect(PX - PW, PY - PH, PX + PW, PY + PH, r=7)
pcol = C.vgrad([(PY - PH, C.rgb("#f0c56a")), (PY + PH, C.rgb("#8a5f22"))])
img = C.over(img, C.blur(C.rect(PX - PW + 4, PY - PH + 8, PX + PW + 4, PY + PH + 8, r=7), 5), C.rgb("#02030a"), 0.6)
img = C.over(img, plate, pcol)
inset = np.clip(C.rect(PX - PW + 7, PY - PH + 7, PX + PW - 7, PY + PH - 7, r=4)
                - C.rect(PX - PW + 9, PY - PH + 9, PX + PW - 9, PY + PH - 9, r=3), 0, 1)
label = text_at("NIGHT DEPOSIT", PX, PY + 1, 31)
eng = emboss(np.clip(label + inset, 0, 1), 1, 0.7)
img = img * np.clip(1.0 - 1.4 * eng[..., None], 0.5, 1.5)
img = C.over(img, label, C.rgb("#4a2c0a"), 0.75)
for sx in (PX - PW + 16, PX + PW - 16):
    img = C.over(img, C.circle(sx, PY, 4.2), C.rgb("#6a4515"))
    img = C.over(img, C.line([(sx - 3, PY + 2), (sx + 3, PY - 2)], 1.4), C.rgb("#2a1a05"))

# ---------------- the banker: profile, bent over, pressing the coin down ----------------
def banker(fx, fy, s=1.0):
    """Upright, three-quarter view: bowler hat, long coat, briefcase in the right hand."""
    P = lambda x, y: (fx + x * s, fy + y * s)
    parts = [
        C.line([P(-5, 0), P(-4, -24)], 6.0 * s), C.line([P(6, 0), P(4, -24)], 6.0 * s),  # legs
        C.poly([P(-11, -20), P(11, -20), P(9, -56), P(-9, -56)]),                      # long coat
        C.poly([P(-9, -56), P(9, -56), P(6, -60), P(-6, -60)]),                        # shoulders
        C.circle(*P(0, -67), 7.2 * s),                                                  # head
        C.ellipse(*P(0, -72), 11.5 * s, 2.4 * s),                                       # hat brim
        C.ellipse(*P(0, -77), 7.0 * s, 6.5 * s),                                        # bowler crown
        C.line([P(9, -54), P(14, -36), P(15, -28)], 4.6 * s),                           # right arm
        C.line([P(-9, -54), P(-14, -36), P(-13, -26)], 4.6 * s),                        # left arm
        C.rect(*P(9, -28), *P(25, -16), r=2 * s),                                       # briefcase
    ]
    return np.maximum.reduce(parts)


top_y = CY - R
fig = banker(CX - 4, top_y + 2, VAR["FIG"])
img = C.over(img, fig, INK)
f_ = VAR["FIG"] / 1.2
img = C.over(img, C.line([(CX - 4, top_y + 2 - 66 * f_), (CX - 4, top_y + 2 - 52 * f_)], 2.6 * f_), RED)  # red tie
im = C.finish(img, grain=0.010)
out = sys.argv[1] if len(sys.argv) > 1 else "out/coin.png"
C.save(im, out)
print(out, os.path.getsize(out))
