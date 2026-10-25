"""Download the Clay reference images from the Wings of Fire wiki into a git-ignored folder (the repo is public:
the images are never committed, only where they come from). Also makes the derived images the build and render
sheets use: the side sheet scaled to 1400 px wide (ref1400.png, the model's measuring scale) and thumbnails.
Files already present are kept. Usage: python fetch_refs.py [--refs DIR]  (default prototypes/clay/refs)."""
import argparse
import io
import os
import urllib.request

from PIL import Image

WIKI = "https://static.wikia.nocookie.net/wingsoffire/images/"
# (local folder, local name, wiki path); local names match what the scripts and views.json expect
SOURCES = [
    ("clayref", "ClayTemplateS978.png", "9/97/ClayTemplateS978.png"),  # the side sheet: everything is measured on it
    ("clayref", "ClayTopShot.png", "9/96/ClayTopShot.png"),
    ("clayref", "Clay_TDPLE.jpg", "4/47/Clay_TDPLE.jpg"),
    ("clayref", "Clay_TDP_GN.jpeg", "d/df/Clay_TDP_GN.jpeg"),
    ("clayref", "SE_box_set_Clay.jpg", "b/b3/SE_box_set_Clay.jpg"),
    ("covers", "Clay_Render_zstarchaserr_png.png", "d/da/Clay_Render_-zstarchaserr.png"),  # the flight render
    ("covers", "Clay_LE_Render_zstarchaserr_png.png", "1/1c/Clay_LE_Render_-zstarchaserr.png"),  # limited edition
    ("covers", "Clay_htd_png.png", "6/62/Clay_htd.png"),  # How to Draw
    ("covers", "Clay_GN_Render_png.png", "d/df/Clay_GN_Render.png"),  # graphic novel
    ("covers", "Clay_sticker_no_bg_png.png", "6/63/Clay_sticker_no_bg.png"),
    ("covers", "Clay_SEPoster_Isolated_Edit_png.png", "6/61/Clay_SEPoster_Isolated_Edit.png"),
    ("covers", "Clay_TDP_Full_jpg.png", "c/c1/Clay_TDP_Full.jpg"),
    ("covers", "Clay_WoF_game_jpg.png", "0/0f/Clay-WoF-game.jpg"),
]
BG = (20, 20, 20)


def flat(im):
    """Transparent images are laid on the dark background the sheets use."""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, BG)
        bg.paste(im, mask=im.split()[3])
        return bg
    return im.convert("RGB")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--refs", default=os.environ.get("CLAY_REFS", os.path.join(here, "..", "refs")))
    refs = os.path.abspath(ap.parse_args().refs)
    got = 0
    for folder, name, path in SOURCES:
        d = os.path.join(refs, folder)
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, name)
        if not os.path.exists(out):
            # format=original: by default the wiki serves a lossy WebP copy, which shifts the measured colour edges
            req = urllib.request.Request(WIKI + path + "/revision/latest?format=original", headers={"User-Agent": "clay-model-refs"})
            data = urllib.request.urlopen(req, timeout=60).read()
            im = Image.open(io.BytesIO(data))
            if folder == "clayref":
                open(out, "wb").write(data)  # the file exactly as published: the side sheet is measured pixel by pixel  # kept exactly as published: the side sheet is measured pixel by pixel
            else:
                flat(im).save(out)
            got += 1
        base = os.path.splitext(name)[0]
        thumb = os.path.join(d, "t_" + base + ".jpg")
        if not os.path.exists(thumb):
            t = flat(Image.open(out)); t.thumbnail((700, 700)); t.save(thumb, quality=90)
    side = os.path.join(refs, "clayref", "ref1400.png")
    if not os.path.exists(side):
        im = Image.open(os.path.join(refs, "clayref", "ClayTemplateS978.png")).convert("RGB")  # as measured: not flattened
        im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS).save(side)
    os.makedirs(os.path.join(refs, "study"), exist_ok=True)
    print(f"clay refs: {got} downloaded, all in {refs}")


if __name__ == "__main__":
    main()
