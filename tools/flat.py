"""Small flat-graphics toolkit: draw at SS x supersample with Pillow, add paper grain,
downsample to 1024. Deterministic (fixed seeds), so a rebuild gives the same pixels."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = 1024
SS = 4


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


class Canvas:
    def __init__(self, bg="#000000", size=W, ss=SS):
        self.size, self.ss = size, ss
        self.img = Image.new("RGBA", (size * ss, size * ss), hexc(bg))
        self.d = ImageDraw.Draw(self.img)

    def s(self, v):
        return v * self.ss

    def pts(self, pts):
        return [(x * self.ss, y * self.ss) for x, y in pts]

    def poly(self, pts, col):
        self.d.polygon(self.pts(pts), fill=hexc(col) if isinstance(col, str) else col)

    def rect(self, x0, y0, x1, y1, col, r=0):
        box = [self.s(x0), self.s(y0), self.s(x1), self.s(y1)]
        c = hexc(col) if isinstance(col, str) else col
        if r:
            self.d.rounded_rectangle(box, radius=self.s(r), fill=c)
        else:
            self.d.rectangle(box, fill=c)

    def circle(self, cx, cy, r, col):
        c = hexc(col) if isinstance(col, str) else col
        self.d.ellipse([self.s(cx - r), self.s(cy - r), self.s(cx + r), self.s(cy + r)], fill=c)

    def line(self, pts, col, w):
        c = hexc(col) if isinstance(col, str) else col
        self.d.line(self.pts(pts), fill=c, width=max(1, int(round(self.s(w)))), joint="curve")
        for x, y in (pts[0], pts[-1]):
            self.circle(x, y, w / 2, col)

    def layer(self):
        """A transparent overlay at the same resolution, for masks/glows."""
        return Image.new("RGBA", self.img.size, (0, 0, 0, 0))

    def paste_layer(self, lay, blur=0):
        if blur:
            lay = lay.filter(ImageFilter.GaussianBlur(blur * self.ss))
        self.img = Image.alpha_composite(self.img, lay)
        self.d = ImageDraw.Draw(self.img)

    def finish(self, grain=6.0, seed=7, vignette=0.0):
        im = self.img.convert("RGB").resize((self.size, self.size), Image.LANCZOS)
        a = np.asarray(im).astype(np.float32)
        rng = np.random.default_rng(seed)
        if grain:
            n = rng.normal(0, 1, (self.size, self.size)).astype(np.float32)
            n = np.asarray(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8))
                           .filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) - 128
            a += (n / 40.0 * grain)[..., None]
        if vignette:
            y, x = np.mgrid[0:self.size, 0:self.size] / (self.size - 1) - 0.5
            v = 1 - vignette * (x * x + y * y) * 2
            a *= v[..., None]
        return Image.fromarray(a.clip(0, 255).round().astype(np.uint8))


def save_png(im, path, colors=256):
    """Palette PNG keeps grain-textured flat art well under the 1 MiB cap."""
    if colors:
        im = im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(path, format="PNG", optimize=True)
