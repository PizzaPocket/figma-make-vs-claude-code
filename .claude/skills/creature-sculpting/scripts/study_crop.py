"""Crop one element of a reference image at full resolution, with a measuring grid.

The grid is labelled in the coordinates of a working-size copy of the reference
(e.g. 1400 px wide), so measurements read off the crop drop straight into the
element's data file.

    python3 study_crop.py REF.png --work-width 1400 --box x0 y0 x1 y1 --out crop.jpg [--grid 10]
"""
import argparse

from PIL import Image, ImageDraw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("--work-width", type=float, default=1400)
    ap.add_argument("--box", type=float, nargs=4, required=True, help="x0 y0 x1 y1 in working-size pixels")
    ap.add_argument("--grid", type=int, default=10)
    ap.add_argument("--size", type=int, default=900, help="output width")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    im = Image.open(a.ref).convert("RGB")
    s = im.width / a.work_width
    x0, y0, x1, y1 = a.box
    crop = im.crop((int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s)))
    scale = a.size / crop.width
    crop = crop.resize((a.size, int(crop.height * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    g = a.grid
    for x in range(int(x0) // g * g, int(x1) + 1, g):
        X = (x - x0) * s * scale
        d.line([(X, 0), (X, crop.height)], fill=(0, 170, 255) if x % (g * 5) == 0 else (60, 60, 60))
        if x % (g * 5) == 0:
            d.text((X + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(int(y0) // g * g, int(y1) + 1, g):
        Y = (y - y0) * s * scale
        d.line([(0, Y), (crop.width, Y)], fill=(0, 170, 255) if y % (g * 5) == 0 else (60, 60, 60))
        if y % (g * 5) == 0:
            d.text((2, Y + 2), str(y), fill=(255, 255, 0))
    crop.save(a.out, quality=90)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
