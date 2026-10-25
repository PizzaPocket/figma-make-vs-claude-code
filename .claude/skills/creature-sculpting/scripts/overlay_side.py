"""Lay a true side view of the model over the side sheet, at the sheet's scale: the model's outline in
cyan over the sheet, and a half blend, side by side. The check for any outline (back, belly, legs).

    python3 overlay_side.py --viewer head-viewer.js --mount mountHead --glb clay.glb --three THREE_DIR \
        --ref ref1400.png --out overlay.jpg [--box px0 py0 px1 py1] [--clay]

The sheet's mapping: px = 700 - 343 z, py = 830 - 343 y (Clay's model units). The side camera looks
along -x from far away (x 30, fov 5.67 over 520 px), centred on z 0, y 0.935.
"""
import argparse
import json
import math
import os
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
CAM = dict(cam=[30, 0.935, 0.0], target=[0, 0.935, 0.0], fov=5.67, pose="neutral")


def main():
    ap = argparse.ArgumentParser()
    for k in ("viewer", "mount", "glb", "three", "ref", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--box", type=float, nargs=4, default=[0, 0, 1400, 1020])
    ap.add_argument("--clay", action="store_true")
    a = ap.parse_args()
    work = tempfile.mkdtemp(prefix="overlay_")
    views = os.path.join(work, "views.json")
    json.dump({"side": [dict(CAM, clay=a.clay, label="")]}, open(views, "w"))
    tile = os.path.join(work, "side.png")
    subprocess.run(["python3", os.path.join(HERE, "render_sheet.py"), "--viewer", a.viewer, "--mount", a.mount, "--glb", a.glb,
                    "--three", a.three, "--views", views, "--set", "side", "--out", tile], check=True, stdout=subprocess.DEVNULL)
    r = Image.open(tile).convert("RGB")
    ref = Image.open(a.ref).convert("RGB")
    k = 520 / (2 * 30 * math.tan(math.radians(CAM["fov"] / 2)))  # render px per model unit
    s = k / 343
    # sheet pixel (px, py) -> model (z, y) -> render pixel
    X = (s, 0, 350 - k * 700 / 343)
    Y = (0, s, 260 + k * 0.935 - k * 830 / 343)
    warped = r.transform(ref.size, Image.AFFINE, X + Y, resample=Image.BILINEAR, fillcolor=(20, 17, 14))
    bg = Image.new("RGB", ref.size, (20, 17, 14))
    mask = ImageChops.difference(warped, bg).convert("L").point(lambda v: 255 if v > 24 else 0)
    edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)), mask.filter(ImageFilter.MinFilter(3)))
    outline = ref.copy()
    outline.paste((0, 255, 255), (0, 0), edge)
    blend = Image.blend(ref, warped, 0.5)
    box = tuple(int(v) for v in a.box)
    L, B = outline.crop(box), blend.crop(box)
    sheet = Image.new("RGB", (L.width * 2 + 10, L.height), (0, 0, 0))
    sheet.paste(L, (0, 0)); sheet.paste(B, (L.width + 10, 0))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), "model outline (cyan) over the side sheet", fill=(255, 220, 0))
    d.text((L.width + 18, 8), "half blend", fill=(255, 220, 0))
    sheet.save(a.out, quality=88)
    print("saved", a.out)


if __name__ == "__main__":
    main()
