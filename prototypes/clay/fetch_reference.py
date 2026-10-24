"""Download the Clay side-view reference from the Wings of Fire wiki and save a
1400 px-wide copy, which build_clay.py and the viewer are measured against.

The image is fan art (by Spirit978) and is not committed: the repo is public.
"""
import io
import json
import pathlib
import urllib.parse
import urllib.request

from PIL import Image

API = "https://wingsoffire.fandom.com/api.php"
HEADERS = {"User-Agent": "wof-pyrrhia-map-tools/0.1 (personal project)"}
OUT = pathlib.Path(__file__).resolve().parents[2] / "cache" / "clay" / "ref1400.png"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS)).read()


def main():
    q = urllib.parse.urlencode({"action": "query", "titles": "File:ClayTemplateS978.png", "prop": "imageinfo",
                                "iiprop": "url", "format": "json"})
    page = next(iter(json.loads(get(f"{API}?{q}"))["query"]["pages"].values()))
    img = Image.open(io.BytesIO(get(page["imageinfo"][0]["url"] + "&format=original"))).convert("RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.resize((1400, 1020), Image.LANCZOS).save(OUT)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
