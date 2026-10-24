"""Render a comparison sheet of a model: painted and plain-clay views, posed, next to reference crops.

    python3 render_sheet.py --viewer head-viewer.js --mount mountHead --glb head.glb \
        --three THREE_DIR --views views.json --set NAME --out sheet.jpg [--design design.json]

THREE_DIR holds three.min.js and GLTFLoader.js (three r128). views.json maps set names to lists of
shots: {label, cam, target, fov, pose, clay (bool), ref (an image path shown instead of a render;
"{refs}" in it stands for --refs, since reference images are not committed)}.
Every sheet should put the model beside the reference it is being judged against.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = """<!doctype html><html><body style="margin:0;background:#000"><div id="v" style="width:700px;height:520px"></div>
<script src="three.min.js"></script><script src="GLTFLoader.js"></script><script src="viewer.js"></script>
<script>window.errors=[];{mount}(THREE,document.getElementById('v'),{{glbUrl:'model.glb',clay:{clay}}})
.then(a=>{{window.api=a;window.ready=true}}).catch(e=>window.errors.push(String(e.stack||e)));</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    for k in ("viewer", "mount", "glb", "three", "views", "set", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--design")
    ap.add_argument("--refs", default=".", help="folder that {refs} in a view's ref path stands for (references are not committed)")
    ap.add_argument("--cols", type=int, default=3)
    a = ap.parse_args()
    shots = json.load(open(a.views))[a.set]
    work = tempfile.mkdtemp(prefix="sheet_")
    for f in ("three.min.js", "GLTFLoader.js"):
        shutil.copy(os.path.join(a.three, f), work)
    shutil.copy(a.viewer, os.path.join(work, "viewer.js"))
    shutil.copy(a.glb, os.path.join(work, "model.glb"))
    tiles = []
    for clay in (False, True):
        batch = [dict(s, out=os.path.join(work, f"s{i}.png")) for i, s in enumerate(shots) if "ref" not in s and bool(s.get("clay")) == clay]
        if not batch:
            continue
        page = os.path.join(work, f"page_{int(clay)}.html")
        open(page, "w").write(PAGE.format(mount=a.mount, clay="true" if clay else "false"))
        sf = os.path.join(work, f"shots_{int(clay)}.json")
        json.dump(batch, open(sf, "w"))
        cmd = ["node", os.path.join(HERE, "shoot.js"), page, sf] + ([a.design] if a.design else [])
        subprocess.run(cmd, check=True)
    for i, s in enumerate(shots):
        im = Image.open(s["ref"].replace("{refs}", a.refs)) if "ref" in s else Image.open(os.path.join(work, f"s{i}.png"))
        im = im.convert("RGB"); im.thumbnail((700, 520))
        tile = Image.new("RGB", (700, 520), (20, 17, 14)); tile.paste(im, ((700 - im.width) // 2, (520 - im.height) // 2))
        ImageDraw.Draw(tile).text((10, 8), s.get("label", ""), fill=(255, 220, 0))
        tiles.append(tile)
    cols = min(a.cols, len(tiles)); rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 700, rows * 520), (20, 17, 14))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 700, (i // cols) * 520))
    sheet.save(a.out, quality=86)
    print("saved", a.out)


if __name__ == "__main__":
    main()
