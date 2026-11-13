"""Float compositing toolkit: anti-aliased masks rasterised at 4x by Pillow, then
composited in linear-ish float RGB at 1024 with gradients, glows and print grain."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

N = 1024
SS = 4


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def _mask(draw_fn):
    m = Image.new("L", (N * SS, N * SS), 0)
    draw_fn(ImageDraw.Draw(m), SS)
    m = m.resize((N, N), Image.BOX)
    return np.asarray(m, np.float32) / 255.0


def poly(pts):
    return _mask(lambda d, s: d.polygon([(x * s, y * s) for x, y in pts], fill=255))


def circle(cx, cy, r):
    return _mask(lambda d, s: d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255))


def ellipse(cx, cy, rx, ry):
    return _mask(lambda d, s: d.ellipse([(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=255))


def line(pts, w):
    def f(d, s):
        d.line([(x * s, y * s) for x, y in pts], fill=255, width=max(1, int(round(w * s))), joint="curve")
        for x, y in (pts[0], pts[-1]):
            r = w / 2
            d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=255)
    return _mask(f)


def rect(x0, y0, x1, y1, r=0):
    if r:
        return _mask(lambda d, s: d.rounded_rectangle([x0 * s, y0 * s, x1 * s, y1 * s], radius=r * s, fill=255))
    return _mask(lambda d, s: d.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], fill=255))


def blur(a, sigma):
    """Gaussian blur of a float mask (or HxWx3 image) via Pillow, in float precision."""
    if a.ndim == 3:
        return np.stack([blur(a[..., k], sigma) for k in range(3)], -1)
    # FFT Gaussian with padding so the glow does not wrap round the edges
    pad = int(min(3 * sigma, 512))
    p = np.pad(a.astype(np.float32), pad, mode="edge")
    h, w = p.shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    k = np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy))
    out = np.fft.irfft2(np.fft.rfft2(p) * k, s=p.shape)
    return out[pad:pad + a.shape[0], pad:pad + a.shape[1]].astype(np.float32)


YY, XX = np.mgrid[0:N, 0:N].astype(np.float32)


def vgrad(stops):
    """Vertical gradient from [(y, colour), ...] stops."""
    ys = [s[0] for s in stops]
    out = np.zeros((N, 3), np.float32)
    col = np.arange(N, dtype=np.float32)
    for k in range(3):
        out[:, k] = np.interp(col, ys, [s[1][k] for s in stops])
    return np.repeat(out[:, None, :], N, 1)


def over(img, mask, col, alpha=1.0):
    """Paint colour (3-vector or HxWx3 array) through mask onto img."""
    m = (mask * alpha)[..., None]
    return img * (1 - m) + np.asarray(col, np.float32) * m


def add_light(img, mask, col, strength=1.0):
    return img + (mask * strength)[..., None] * np.asarray(col, np.float32)


def finish(img, grain=0.018, seed=7):
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, (N, N)).astype(np.float32)
    g = blur(g, 0.7) * 2.2
    out = img + grain * g[..., None]
    out = np.clip(out, 0, 1) ** (1 / 1.0)
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8))


def save(im, path, colors=256):
    if colors:
        im = im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(path, format="PNG", optimize=True)
