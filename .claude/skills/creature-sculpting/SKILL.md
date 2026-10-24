---
name: creature-sculpting
description: Architect one part of a creature model at a time (nose, eye, ear, horn base, jaw, limb, wing, tail) from reference art, the way an architect designs a building, then encode it as measured data and build it. Use when modelling or fixing any part of the Clay (Wings of Fire) model, or any character model built from reference images in this repo.
---

# Creature sculpting

Model one element at a time. Treat each element like a building:
- find its load-bearing masses;
- find the anatomy that shapes them;
- find the planes, ridges and creases the artist drew;
- write all of that down as numbers before building anything.

Never tune the whole creature at once.

## The loop, for each element

1. **Isolate.** Crop the element at full resolution from every reference that shows it, with a measuring grid in reference pixels (`scripts/study_crop.py`). Use the official art first and fan sheets second. Note which references disagree.
2. **Read it as architecture.** Write an element sheet (template below), answering in order:
   - **Primary mass:** what simple solid is it? (A wedge, box, drum or cone.) What are its overall length, height and width?
   - **Structure underneath:** what bone or muscle would have to exist to make this shape? For example:
     - the masseter makes the cheek bulge;
     - a temporal crest leads into the horn base;
     - the brow is a shelf of bone over the eye socket.

     The surface must look driven by these, not inflated.
   - **Planes:** where are the flat faces, and where do they meet in a hard edge or a soft turn? Cartoon and illustrated dragons are built from clear planes. Find them.
   - **Lines the artist drew:** every outline and crease is a piece of geometry, either an edge between planes, a ridge or a groove. List each one as a polyline in reference pixels and say which it is.
   - **Openings and attachments:** eyes, nostrils, ear openings, the mouth, and where horns, frills and plates sit.
   - **Articulation:** what moves, around which pivot? Which side of a seam is rigid?
3. **Encode.** Put the numbers in the element's data file, not in code: stations (cross-sections), polylines for ridges and creases, pivots and attachment frames. Convert reference pixels to model units with one documented mapping (for Clay: `z = (700 - px) / 343`, `y = (830 - py) / 343`).
4. **Build** from the data with the toolkit below.
5. **Check** against the references:
   - an orthographic render aligned pixel-for-pixel with the side reference;
   - a three-quarter and a front view against the official art;
   - the element articulated through its full range (jaw open, blink, wing spread).

   Write down what still differs. Fix the data, not the code.
6. **Record** what you learned about this kind of element in this file's "Lessons" section, so the next element starts ahead.

## Element sheet template

```
## <element>
References: <files and crops used; where they disagree>
Primary mass: <solid, size in model units>
Structure underneath: <bones/muscles and what surface each one drives>
Planes: <faces and the edges between them (hard/soft)>
Drawn lines: <name: polyline in ref px, ridge|crease|edge>
Openings/attachments: <name: position, size, orientation>
Articulation: <bone, pivot, range; rigid vs skinned>
Build: <which toolkit pieces>
Check: <what to compare; known differences>
```

## Toolkit (what elements are built from)

- **Masses.** Lofted quad meshes. Rings of points at measured stations along the element, each ring a superellipse or profile. The exponent controls boxiness: 2 is round, 3.5 is a boxy plane form. Clean topology and natural surface coordinates come for free.
- **Brushes,** applied to a mass as data:
  - `ridge(polyline, height, width)`: a raised line, such as a brow or a cheek ridge;
  - `crease(polyline, depth, width)`: a fold or the edge of a plate;
  - `dent(point, depth, radius)`: a nostril, ear opening or eye socket;
  - `bulge(point, amount, radius)`: a muscle mass;
  - `flatten(region, plane)`: to make a drawn plane actually flat.
- **Attachments,** each a separate piece on its own bone:
  - `tube(path, radii, rings)` for horns and claws;
  - `fin(base, axis, outline, thickness, ribs, rolled_edge)` for ear frills and membranes;
  - `eye(centre, radius, gaze)` with upper and lower lid shells;
  - `plate(position, size, thickness, bevel)` for armour plates.
- **Seams.** Decide per element whether it is part of the continuous skin or a rigid piece. Rigid pieces tuck their edges under a drawn line (a plate edge or a frill) so the seam is hidden.

## Rules

- The references decide. When the model and the art disagree, the model is wrong, even if it "looks fine".
- Measure from the side reference, check the shape from the official three-quarter and front art, and use the books (canon descriptions) to settle what the art leaves open.
- Organic, not mechanical. Clay's plates and scales are organic and roughly rectangular, varying in size and following the form. Never use a regular grid or brick pattern.
- Left and right are mirrored. Model the left side and mirror it.
- Every visible line in the art should end up as geometry or as a deliberate texture line. Know which.

## Lessons

- **Nose (Clay):**
  - The dark nose plate is a faceted wedge ending in a prow.
  - The nostril sits at the back top corner of that plate on the side, not at the tip.
  - The upper lip overhangs a set-back lower jaw: a strong overbite.
- **Jaw (Clay):** the cream lower jaw continues up behind the mouth corner as a jowl under the ear. The mouth line is low in front and rises steeply toward the corner.
- **Ear (Clay):**
  - The frill sits high at the back of the head.
  - Its front edge rolls over like the rim of a horse's ear.
  - The ear opening is a small dark hole on the cheek below it.
- **Horns (Clay):** a temporal crest runs from the brow back to the horn base. The horn is ringed along its whole length. A "second horn" in a side view is usually the far-side horn.
- **Hands vs feet (Clay):** the front hands are compact with big hooked claws and a high dewclaw. The hind feet are long and digitigrade, with a heel spur and studs along the top.
- **Widths need a front view.** A side reference gives only lengths and heights. Take widths from the front three-quarter art. Clay's head first read as a horse's head because the widths were guessed narrow.
- **Draw region edges as lines.** For a colour region whose edge is a drawn line (like the dark plate), store the signed distance to the edge per vertex, not a 0/1 flag. The shader can then draw a clean outline instead of a stair-stepped one.
- **Overhangs are skin.** The underside of an overhanging part (the upper lip in front of the jaw) is skin, not mouth interior.
- **Check every render with:**
  - `render.sh`-style sheets: a side, three-quarter and front view, plus the jaw open, next to the references;
  - a script that rebuilds from the repo files, so the scratch copies never drift.

