"""Extract the ink lines of a region of a reference into a clean line map with a measuring grid.

Dark strokes are hard to see on dark paint (Clay's brown crest). This keeps only pixels clearly darker
than their surroundings, so the plate joints, creases and outlines can be traced and measured.
Coordinates are in a working-size copy of the reference (e.g. 1400 px wide), like study_crop.py.

    python3 line_map.py REF.png --work-width 1400 --box x0 y0 x1 y1 --out lines.png
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("--work-width", type=float, default=1400)
    ap.add_argument("--box", type=float, nargs=4, required=True)
    ap.add_argument("--contrast", type=float, default=12, help="how much darker than the local median a pixel must be")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    im = np.asarray(Image.open(a.ref).convert("RGB")).astype(float)
    S = im.shape[1] / a.work_width
    x0, y0, x1, y1 = a.box
    lum = im[int(y0 * S):int(y1 * S), int(x0 * S):int(x1 * S)].mean(2)
    ink = (lum < ndimage.median_filter(lum, size=int(9 * S)) - a.contrast) & (lum < 90)
    ink = ndimage.binary_opening(ink, iterations=1)
    out = (np.clip(lum, 0, 255) * 0.35 + 160).astype(np.uint8)[..., None].repeat(3, 2)
    out[ink] = (20, 20, 20)
    img = Image.fromarray(out).resize((1000, int(1000 * out.shape[0] / out.shape[1])), Image.NEAREST)
    d = ImageDraw.Draw(img)
    sc = 1000 / (x1 - x0)
    for gx in range(int(x0) // 5 * 5, int(x1) + 1, 5):
        X = (gx - x0) * sc
        d.line([(X, 0), (X, img.height)], fill=(0, 150, 255) if gx % 25 == 0 else (200, 200, 230))
        if gx % 25 == 0:
            d.text((X + 2, 2), str(gx), fill=(255, 0, 0))
    for gy in range(int(y0) // 5 * 5, int(y1) + 1, 5):
        Y = (gy - y0) * sc
        d.line([(0, Y), (img.width, Y)], fill=(0, 150, 255) if gy % 25 == 0 else (200, 200, 230))
        if gy % 25 == 0:
            d.text((2, Y + 2), str(gy), fill=(255, 0, 0))
    img.save(a.out)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
