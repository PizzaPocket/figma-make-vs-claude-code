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
   - **Structure underneath:** which bones and which muscles would have to exist to make this shape? See "Sculpt from the inside out" below. The surface must look driven by them, not inflated.
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

## Sculpt from the inside out: bone, muscle, skin

A sculptor thinks about the muscles under the skin as much as the skeleton. No surface form is free-floating. Each bump, plane and fold is there because something under it pushes it out, holds it up or lets it fold. Build every element in three layers, and write them in the data in this order:

1. **Bone (landmarks).** The hard, fixed points: rims, ridges, bars and joints. Bone makes crisp edges and flat-ish planes, and it does not change when the creature moves.
   - Bony rims around openings: the eye socket (brow above, cheekbone below, postorbital bar behind), the nostrils, the ear.
   - Arches and crests: the zygomatic arch from below the eye back to the jaw joint, the temporal crest, the skull roof.
   - Joints and pivots: the jaw joint, which sits under the ear in dragons and reptiles.
2. **Muscle (masses).** Each muscle runs from an origin to an insertion. It bulges in its belly and flattens toward its tendons. Know which one fills each region and what it does, because that also tells you how the region moves.
   - **Ring muscle round the eye (orbicularis):** a soft raised pad round the lids, longer toward the back corner. It is what closes the eye.
   - **Masseter:** from the zygomatic arch down to the jaw. It makes the full cheek above the jaw and bunches when the jaw closes.
   - **Temporalis:** fills the skull behind the eye. It is why the cranium is wide behind the brow.
   - **Lip muscles (levator):** a gentle fullness on the side of the muzzle.
   - **Neck muscles** wrap from the skull base. Limb muscles are covered in each limb's sheet.
3. **Skin (creases, openings, scales).** A crease forms where two muscles meet, or where skin folds over something that moves: lids, the mouth corner, joints. In stylised art the ink lines are mostly these creases. Trace each drawn line back to the boundary between masses that causes it, and sculpt that boundary instead of drawing the line.

**How the eye is held.** This is the model case for the method:
- The eyeball sits in a bony socket. The brow shelf (the roof's eave, on Clay) overhangs it from above.
- The cheekbone's crisp top edge is the socket floor. The eye and its lower lid rest on it.
- The postorbital bar closes it behind.
- Inside that frame, the ring muscle forms a raised pad, and the lids are thick shells with a rounded margin hinged on the canthal axis.
- The face's crease lines (Clay's zig-zag under the eye) are where the lid pad meets the cheekbone.

If the eye looks stuck on, a layer is missing. Usually the socket is a plain dent with no rim, or there is no lid pad.

### The face is how a creature communicates

Expression is muscle. Every subtlety in the eye, brow, cheek and mouth matters, because that is where the character shows feeling. Learn the expressive muscles and what each one does to the surface, then model the face so those actions are possible:

| Muscle | Action (FACS unit) | What it does to the surface |
| --- | --- | --- |
| Orbicularis oculi, around the lid | blink (AU45), gentle close | the lids slide over the eyeball |
| Orbicularis oculi, outer ring | cheek raise / squint (AU6, AU7) | the cheek pad rises, the lower lid bunches up, crow's-feet creases fan from the outer corner |
| Levator of the upper lid | lid raise (AU5) | more white above the iris: surprise, fear |
| Corrugator and procerus | brow lower (AU4) | the brow skin is drawn down and in toward the inner corner and bunches over the upper lid: anger, concentration |
| Frontalis, inner part | inner brow raise (AU1) | the skin above the inner corner lifts: worry, sadness |
| Zygomaticus major | lip corner pull (AU12) | the mouth corner goes up and back, and the cheek rises with it: a real smile is AU6 + AU12 |
| Levator labii (with alaeque nasi) | lip raise, nose wrinkle (AU10, AU9) | the upper lip lifts off the teeth and the snout wrinkles: snarl, disgust |
| Depressor anguli oris | lip corner down (AU15) | the mouth corner drops: sadness |
| Masseter and temporalis | jaw | they bunch when the jaw clenches |

Build each muscle action as a shape of the face (a morph target): a push of the region it moves, plus the creases it makes. Lid tilts go on bones; the blink is a shape of the lids themselves. Write expressions as mixes of actions. Clay's brow is a rigid plate, so his brow actions move the skin and lids under it, not the plate.

### Eyes, the details that make them convincing

- **The two corners differ.**
  - The inner (medial) corner is rounded, and holds the caruncle: a small fleshy pink teardrop lying on the eyeball between the lid margins. It is never a bead stuck on.
  - The outer (lateral) corner closes to a sharp point, usually higher, so the canthal axis tilts up toward the outer corner.
- **The corners sit on the visible eyeball,** where it meets the face, about 50° to each side of the gaze. They are not the ends of the eye's axis, which are buried. Put them at the axis ends and the visible opening has no corners.
- **The margins are not mirror images.** The upper lid arcs highest a little toward the inner corner. The lower lid is flatter and dips lowest toward the outer corner.
- **The lids have thickness.** Each is a shell with a rounded margin that slides over the eyeball. They are pinned at the corners by the canthal tendons, so they move most mid-eye and not at all at the corners.
- **A blink is the lid sliding,** not a large rigid turn. A large bone turn tears the corners, so make the blink a shape key of the lids.
- **The socket holds the eye assembly.** Carve the face into a socket: inside the lids' footprint the skin runs in just under the lid dome, and a rounded rim (the orbital rim under the ring muscle) turns it back out. No bone or muscle form may raise the skin over the eye opening; they frame it.
- **The cheekbone is the floor of the socket.** In stylised dragons it is often the face's most distinctive line. Find where it starts and ends in every reference, and which side is crisp: lit above and shadowed below means it overhangs. Sculpt it strongly enough that it reads in the plain clay render without any line drawn on it.

**Judge forms in a plain clay render.** Render with no colour, scales or ink, under a raking light. Paint hides missing anatomy.

## Element sheet template

```
## <element>
References: <files and crops used; where they disagree>
Primary mass: <solid, size in model units>
Bone: <landmarks (rims, arches, bars, joints) and the crisp edges/planes they make>
Muscle: <each mass: origin -> insertion, where it bulges, what it moves>
Skin: <creases and folds, and which boundary between masses each one marks>
Planes: <faces and the edges between them (hard/soft)>
Drawn lines: <name: polyline in ref px, ridge|crease|edge>
Openings/attachments: <name: position, size, orientation>
Articulation: <bone, pivot, range; rigid vs skinned>
Build: <which toolkit pieces>
Check: <what to compare; known differences>
```

## Toolkit (what elements are built from)

- **Masses.** Lofted quad meshes. Rings of points at measured stations along the element, each ring a superellipse or profile. The exponent controls boxiness: 2 is round, 3.5 is a boxy plane form. Clean topology and natural surface coordinates come for free.
- **Brushes,** applied to a mass as data, grouped into `bone`, `muscle` and `skin` layers:
  - `ridge(polyline, height, width)`: a raised line, such as a brow or a cheek ridge;
  - `crease(polyline, depth, width)`: a fold or the edge of a plate;
  - `dent(point, depth, radius)`: a nostril, ear opening or eye socket;
  - `shelf(polyline, height, width_up, width_down)`: a bony edge that is crisp on one side and slopes off on the other, such as the cheekbone under the eye;
  - `bulge(point, amount, radii)`: a muscle belly;
  - `pad(centre, radii, tilt, height)`: a raised plateau in a tilted ellipse, such as the lid ring muscle;
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
- Every visible line in the art should end up as geometry. Carry forms such as the cheekbone, lid creases and plate joints by sculpting (ridges, creases, gaps between plates), not by drawn ink lines on the skin. Drawn lines read as scratches on a sculpted model.

## Lessons

- **Armour is separate plates, not a scored sheet.** If the art draws plate lines with consistent shapes, build each plate as its own solid tile, in the rows the art uses. On Clay's roof that means a nose plate, a top row of transverse bands, and edge rows of near-square plates along the eave, ending at the brow plate. Give each tile rounded edges, thicker toward its back edge, overlapping the next one like a shingle. The gaps then make the drawn lines, and they stay consistent because they come from the plate layout.
- **Resolution must match the sharpest edge.** A crisp edge (the cheekbone's overhang, a lid crease) needs mesh spacing finer than its width, or it renders soft. Check in the clay render.
- **WebGL allows 16 vertex attributes.** Morph targets use them up (position and normal per target), so pack custom attributes into vectors.
- **Look for fitted pieces first.** Before modelling a region, ask which colour areas are separate architectural pieces fitted together. For Clay's head:
  - the dark roof is a shell over the orange face, with its eave standing proud;
  - the nose crest sits on the roof;
  - the horns continue the roof.

  A different colour often means a different solid, not paint.
- **Find the meridian of every opening.** For an eye, measure the canthal axis (tear duct to the back corner) in the side view. Hinge the lids on that axis: build them as shells parametrised along it and around it, so they pinch to an almond shape and a blink sweeps across along the right angle.
- **Scan silhouettes column by column.** Scan the side silhouette and look for runs of nearly constant slope. They mark the separate planes: nose crest, forehead, skull, then horn.

- **Nose (Clay):**
  - The dark nose plate is a faceted wedge ending in a prow.
  - The nostril sits at the back top corner of that plate on the side, not at the tip.
  - The upper lip overhangs a set-back lower jaw: a strong overbite.
- **Jaw (Clay):** the cream lower jaw continues up behind the mouth corner as a jowl under the ear. The mouth line is low in front and rises steeply toward the corner.
- **Ear (Clay):**
  - The frill sits high at the back of the head.
  - Its front edge rolls over like the rim of a horse's ear.
  - The ear opening is a small dark hole on the cheek below it.
- **Horns (Clay):**
  - **Where it comes from:** a horn is the roof's back corner drawn out, not a cone stuck on the skull. Its root fills the side of the roof's back corner behind and above the eye, from the eave up to the roof top, so the roof's top line runs straight on into the horn's top line.
  - **How it is held:** the roof's edge comes back over the eye and curls under the root.
  - **Path:** it sweeps back in a long, nearly straight line, barely tapering, and curls up only in the last stretch.
  - **Surface:** smooth, *lined but not bumpy*. The rings are hairline incisions plus ink, never raised ridges or a stack of segments.
- **Sculpt features into their host; don't attach them as separate pieces.** A nose crest, a horn root or a brow ridge belongs to the surface it rises from.
  - **Nose crest:** a height field added to the nose plate's own surface, with the nostrils as troughs in it.
  - **Horn root:** the roof plates are moved onto the smooth union (exponential smooth-min with a fillet radius) of the roof and the horn tube, so they swell up and wrap the horn's base and the horn grows out of the head.
  - **What failed:** a separate piece planted on top, a radially flared collar (it read as a trumpet bolted on), and a separate root loft. All of them read as stuck on.
- **Lines on smooth forms.** Make the line a hairline groove (depth about 2% of the radius) plus ink. Check in the clay render that the silhouette stays smooth: if the outline is scalloped, the grooves are too deep or too wide.
- **Hands vs feet (Clay):** the front hands are compact with big hooked claws and a high dewclaw. The hind feet are long and digitigrade, with a heel spur and studs along the top.
- **Widths need a front view.** A side reference gives only lengths and heights. Take widths from the front three-quarter art. Clay's head first read as a horse's head because the widths were guessed narrow.
- **Draw region edges as lines.** For a colour region whose edge is a drawn line (like the dark plate), store the signed distance to the edge per vertex, not a 0/1 flag. The shader can then draw a clean outline instead of a stair-stepped one.
- **Overhangs are skin.** The underside of an overhanging part (the upper lip in front of the jaw) is skin, not mouth interior.
- **Check every render with:**
  - `render.sh`-style sheets: a side, three-quarter and front view, plus the jaw open, next to the references;
  - a script that rebuilds from the repo files, so the scratch copies never drift.

