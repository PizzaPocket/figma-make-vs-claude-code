"""Stage 1 (automatic part): separate land from sea on the Pyrrhia map.

Uses the colors of the illustration plus the hand-listed annotations in
data/pyrrhia/map_annotations.json so that labels and decorations are not
mistaken for terrain:

- Saturated blue that connects to the open ocean is sea. Blue enclosed by
  the coastline (shaded ice, lakes) is not; lakes are traced separately.
- Warm and green colors are land. Pure white outside labels is snow (land).
- A label's white background (plus its glow, up to GLOW px past its box)
  is not terrain: it becomes sea or land per the label's "sits_on". Labels
  that sit on the coast are split by distance to the nearest confident pixel,
  which joins the coastline where it enters and leaves the label; those
  need review by hand.
- Decorations (compass, sea creatures, border ornaments) are painted as sea.
- Everything else uncertain (ink lines, label text, pale blue) is assigned
  by a watershed that treats dark ink as a wall, so the drawn coastline is
  where land and sea meet.

Writes cache/stage1/landmask.png (white = land) and a review overlay.
"""
import json
import pathlib

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from skimage.segmentation import watershed

ROOT = pathlib.Path(__file__).resolve().parents[2]
ANNOTATIONS = ROOT / "data" / "pyrrhia" / "map_annotations.json"
OUT = ROOT / "cache" / "stage1"

UNKNOWN, SEA, LAND = 0, 1, 2
GLOW = 25


def load_cropped(ann):
    img = Image.open(ROOT / "cache" / "maps" / ann["source"]).convert("RGB")
    m = int(ann["crop_fraction"] * img.width)
    return img.crop((m, m, img.width - m, img.height - m))


def box_mask(shape, boxes, pad=0):
    mask = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        mask[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = True
    return mask


def label_background(white, shape, label):
    """White label background plus the glow that spills past its box."""
    near = box_mask(shape, label["boxes"], pad=label.get("glow", GLOW))
    lab, _ = nd.label(nd.binary_closing(white & near, iterations=2))
    inside = box_mask(shape, label["boxes"])
    ids = np.unique(lab[inside & (lab > 0)])
    return np.isin(lab, ids) & near


def main():
    ann = json.loads(ANNOTATIONS.read_text())
    img = load_cropped(ann)
    hsv = np.asarray(img.convert("HSV")).astype(int)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    shape = h.shape

    blue = (h >= 128) & (h <= 170)
    white = (s <= 15) & (v >= 220)
    # Ink is near-black and colorless; dark but strongly colored paint (the
    # deep green of a forested island) is terrain, not ink.
    ink = (v < 60) | ((v < 110) & (s < 80))
    decorations = box_mask(shape, [d["box"] for d in ann["decorations"]])

    # Sea is blue water that reaches the edge of the map.
    water = (blue & (s >= 45) & ~ink) | decorations
    water[[0, -1], :] = water[:, [0, -1]] = True
    lab, _ = nd.label(water)
    border_ids = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    sea = np.isin(lab, border_ids[border_ids > 0])

    markers = np.full(shape, UNKNOWN, np.uint8)
    markers[sea] = SEA
    markers[~blue & (s >= 45) & ~ink] = LAND
    markers[white] = LAND
    # Shrink markers away from ink so the watershed, not the color test,
    # decides the pixels right at the coastline.
    for value in (SEA, LAND):
        region = markers == value
        markers[region & ~nd.binary_erosion(region, iterations=2)] = UNKNOWN

    coast_labels = np.zeros(shape, bool)
    for label in ann["labels"]:
        background = label_background(white, shape, label)
        if label["sits_on"] == "coast":
            markers[background] = UNKNOWN
            coast_labels |= background
        else:
            markers[background] = SEA if label["sits_on"] == "water" else LAND
    markers[decorations] = SEA

    walls = nd.gaussian_filter(255.0 - v, 1.0)
    result = watershed(walls, markers)
    # Under coast labels the drawn coastline is hidden, so the watershed has
    # no wall to stop at. Split them (and the uncertain pixels hugging them)
    # by distance to the nearest pixel whose color was confidently sea or land.
    if coast_labels.any():
        hidden = nd.binary_dilation(coast_labels, iterations=GLOW) & (markers == UNKNOWN)
        hidden |= coast_labels
        _, (iy, ix) = nd.distance_transform_edt(markers == UNKNOWN, return_indices=True)
        result[hidden] = markers[iy, ix][hidden]

    land = result == LAND
    land = nd.binary_opening(land, iterations=1)
    land = nd.binary_fill_holes(land) | land
    lab, n = nd.label(land)
    sizes = nd.sum(land, lab, range(1, n + 1))
    land = np.isin(lab, 1 + np.flatnonzero(sizes >= 40))

    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray((land * 255).astype(np.uint8)).save(OUT / "landmask.png")

    # Review overlay: red = extracted coastline, yellow = label boxes,
    # magenta = decorations, orange = labels that hide the coastline.
    overlay = np.asarray(img).copy()
    overlay[land ^ nd.binary_erosion(land, iterations=2)] = [255, 0, 0]
    review = Image.fromarray(overlay)
    draw = ImageDraw.Draw(review)
    for l in ann["labels"]:
        color = (255, 140, 0) if l["sits_on"] == "coast" else (230, 200, 0)
        for box in l["boxes"]:
            draw.rectangle(box, outline=color, width=3)
    for d in ann["decorations"]:
        draw.rectangle(d["box"], outline=(220, 0, 220), width=3)
    review.save(OUT / "landmask_review.png")
    print(f"land {land.mean():.1%}, {nd.label(land)[1]} land pieces")


if __name__ == "__main__":
    main()
