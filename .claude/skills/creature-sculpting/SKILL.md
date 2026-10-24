---
name: creature-sculpting
description: Sculpt a creature model from reference art one element at a time (nose, eye, cheekbone, horn, jaw, neck, limb, hand, wing, tail), the way an architect designs a building and a sculptor builds from bone and muscle outward, then encode it as measured data and build it. Use when modelling or fixing any part of the Clay (Wings of Fire) model, or any character model built from reference images in this repo.
---

# Creature sculpting

Model one element at a time. Treat each element like a building:
- find its load-bearing masses;
- find the bones and muscles that shape them;
- find the planes, ridges, plates and creases the artist drew;
- write all of that down as numbers before building anything.

Never tune the whole creature at once, and never guess a shape the references show.

## How we work

The user reviews every step by eye. Their notes are the most valuable input, and they have repeatedly caught what the numbers missed. Work so their review is fast and every note gets fixed properly.

- **Show, side by side.** End every step with a sheet that puts the model next to the reference it is judged against:
  - a side view aligned with the side sheet;
  - the official three-quarter and front art;
  - a plain clay render;
  - the part articulated (jaw open, blink, expressions).

  Use `scripts/render_sheet.py` with the part's `views.json`.
- **Fix exactly what is named, at its source.** When the user names a feature ("his cheekbone", "the inside eye point"), first find the exact drawn line or shape they mean in the reference: zoom in, and make a line map. Measure it, then change the data. If the meaning is unclear, ask; don't build a guess.
- **Answer the question.** If asked "does X look right?", check the reference and answer plainly. Say what was wrong and why, including your own earlier mistakes. ("Yes, I invented that ridge" is the right answer when it is true.)
- **Report what is still off.** Every report ends with the remaining differences you can see. Never call a part done because it "looks fine".
- **One commit per fix.** After each fix, update the data file, the element sheet (`*_sheets.md`) and this skill's lessons, then commit and push. The repo is public: never commit the reference images or generated `.glb` files.

## The loop, for each element

1. **Isolate.** Crop the element at full resolution from every reference that shows it, with a measuring grid in reference pixels (`scripts/study_crop.py`). Use the official art first and fan sheets second, and note where they disagree. Where the lines are hard to see (dark ink on dark paint), extract them with `scripts/line_map.py` and trace from the line map.
2. **Read it as architecture.** Write an element sheet (template below):
   - **Primary mass:** what simple solid is it (wedge, box, drum, cone)? Its length, height and width. Take lengths and heights from the side view and **widths from the front and top views**. A side profile alone hides a box nose.
   - **Bone, muscle, skin:** what has to exist underneath to make this shape (see "Sculpt from the inside out").
   - **Planes:** the flat faces, and where they meet in a hard edge or a soft turn.
   - **Drawn lines:** each line as a polyline in reference pixels, and what it is: an edge between planes, a ridge, a groove, a plate joint, or the outline of an opening.
   - **Pieces:** which colour areas are separate solids fitted together, which features are sculpted into a host surface, and which are separate attachments.
   - **Articulation:** what moves, around which pivot, and which side of a seam is rigid.
3. **Encode.** Put the numbers in the element's data file, not in code:
   - stations (cross-sections);
   - polylines for ridges, rims and creases;
   - plate layouts;
   - pivots and attachment frames;
   - a `why` for every form, naming its evidence.

   Convert reference pixels to model units with one documented mapping (for Clay: `z = (700 - px) / 343`, `y = (830 - py) / 343`).
4. **Build** from the data with the toolkit below.
5. **Check** with a sheet: the aligned side view against the line map, three-quarter and front against the official art, plain clay under a raking light, and the part moving through its range. Write down what still differs, and fix the data, not the code.
6. **Record** what this element taught you in "Lessons", so the next element starts ahead.

## Evidence rules

- **Never invent a form.** Every ridge, crease, plate and mass must point to a specific line or shading in a specific reference, and its `why` says which. Don't assemble a feature from loosely matching lines across several images, and don't add textbook anatomy the art doesn't show. (Invented and removed on Clay: a pit-to-jaw "cheekbone ridge" and a postorbital bar.)
- **Measure, don't eyeball.** Read positions off gridded crops and line maps. Measure each corner, joint and stroke where it actually is. A measurement between the wrong two points gives a confident wrong number: Clay's eye tilt was first measured to where two creases meet, not to the eye's corner, and came out 26° instead of about 45°.
- **A drawn line's weight is the edge's strength.** A heavy stroke means a crisp, deep edge; a tapering stroke means the form fades out. Sculpt the edge on the side the line is drawn.
- **The references decide.** When the model and the art disagree, the model is wrong.
- Left and right are mirrored: model the left side and mirror it.
- Organic, not mechanical. Plates and scales vary in size and follow the form; never use a regular grid or brick pattern.

## Construction principles

- **Look for fitted pieces.** A different colour area is often a different solid. Clay's head is an orange face mass with a dark roof of plates fitted over it, standing proud so its edge overhangs.
- **Sculpt features into their host.** A nose pad, a horn root or a brow belongs to the surface it rises from:
  - a nose pad is a height field on its plate, with the nostrils cut into it;
  - a horn root is the roof moved onto the smooth union (exponential smooth-min with a fillet radius) of roof and horn, so the plates swell up into the horn.

  Separate pieces planted on top, flared collars and separate root lofts all failed: they read as stuck on.
- **Lines are geometry, never ink.** Every line in the art becomes an edge, ridge, crease, plate gap or rim. Don't draw lines on the skin in the shader: they read as scratches on a sculpted model. Ink is acceptable only in a groove that already exists in the geometry, such as a horn ring.
- **Armour is separate plates, not a scored sheet.**
  - Build each plate as its own solid tile, in the rows the art draws.
  - Give it rounded edges, thicker toward its back edge, overlapping the next one back like a shingle.
  - The gaps make the drawn lines, consistently.
- **Lay plates out in the art's own directions.** Joints run perpendicular to the form's flow line, and strips run along it. Use coordinates that follow the profile: s along it, d the depth perpendicular to it. On a sloping muzzle the joints are therefore not vertical cuts.
- **Resolution must match the sharpest edge.** The mesh spacing must be finer than the narrowest crease or overhang, or it renders soft.
- **Smooth, never stepped.** When carving or uniting surfaces (sockets, fillets), use a smooth minimum, and clamp it so it never cuts into a neighbouring part.

## Sculpt from the inside out: bone, muscle, skin

No surface form is free-floating: something under it pushes it out, holds it up or lets it fold. Write every element in three layers, in this order:

1. **Bone (landmarks).** Rims round openings, arches, crests, bars and joints. Bone makes crisp edges and flat-ish planes, and does not change shape when the creature moves.
2. **Muscle (masses).** Each muscle runs from an origin to an insertion. It bulges in its belly and flattens toward its tendons. Know which one fills each region, because that tells you both its shape and how the region moves.
3. **Skin (creases, openings, scales).** A crease forms where two muscles meet, or where skin folds over something that moves (lids, mouth corner, joints). Trace each drawn line back to the boundary that causes it, and sculpt that boundary.

**Judge the forms in a plain clay render.** Paint hides missing anatomy.

### The face is how a creature communicates

Expression is muscle, and every subtlety in the eye, brow, cheek and mouth matters. Model the face so these actions are possible:

| Muscle | Action (FACS unit) | What it does to the surface |
| --- | --- | --- |
| Orbicularis oculi, around the lid | blink (AU45) | the lids slide over the eyeball |
| Orbicularis oculi, outer ring | cheek raise / squint (AU6, AU7) | the cheek pad rises, the lower lid bunches up, creases fan from the outer corner |
| Levator of the upper lid | lid raise (AU5) | more white above the iris: surprise, fear |
| Corrugator and procerus | brow lower (AU4) | brow skin drawn down and in over the upper lid: anger, concentration |
| Frontalis, inner part | inner brow raise (AU1) | the skin above the inner corner lifts: worry, sadness |
| Zygomaticus major | lip corner pull (AU12) | mouth corner up and back, cheek rises; a real smile is AU6 + AU12 |
| Levator labii (with alaeque nasi) | lip raise, nose wrinkle (AU10, AU9) | upper lip lifts off the teeth, snout wrinkles: snarl, disgust |
| Depressor anguli oris | lip corner down (AU15) | mouth corner drops: sadness |
| Masseter, temporalis | jaw | bunch when the jaw clenches |

Build each muscle action as a face morph target: a push of the region plus the creases it makes. Lid tilts go on bones (split the upper lid into inner and outer halves); the blink is a shape of the lids themselves. Write expressions as mixes of actions. A rigid brow plate doesn't move: brow actions move the skin and lids under it.

### Eyes

- **The eye sits in a socket.** Carve the face into a socket that holds the eye assembly. Inside the lids' footprint the skin runs in just under them, and a rounded rim turns it back out.
  - No bone or muscle form may raise the skin over the eye opening; they only frame it.
  - Seat the eye along the face's true normal at its centre, deep enough that the lids barely stand above the face. A visible lid dome reads as a bulge.
- **The corners differ, and each has its own angle.** Measure each corner's angle from the eye centre on a line map. Clay's inner corner drops about 58° below horizontal, down and forward to the tear duct; his outer corner rises only about 32°. Bend the lid frame so each corner lands at its measured angle.
- **The corners sit on the visible eyeball,** where it meets the face, not at the buried ends of the eye's axis.
  - The inner corner is rounded and holds the caruncle: a fleshy pink teardrop lying on the eyeball between the margins. Never a bead.
  - The outer corner closes where the art's outline closes.
- **Follow the eyeliner's path.** If the art draws a closed round ring, the corner must close round where the ring ends. A corner placed too far back drags the dark rim into a wing.
- **The margins are not mirror images.** The upper lid peaks toward the inner corner; the lower dips lowest toward the outer corner.
- **Lids have thickness:** shells with a rounded margin, sliding over the eyeball. They are pinned at the corners, moving most mid-eye. A blink is a shape key of the lids; a large bone turn tears the corners.
- **The cheekbone is the socket's rim.** On Clay it is the heavy hooked line under the eye. Sculpt it as a `rim`: raised, gentle toward the eye, crisp on the outside where the line is drawn.

## Toolkit

**Masses**
- Lofted quad meshes: rings of points at measured stations, each ring a superellipse or profile. The exponent sets boxiness: 2 is round, 5 a crisp box.

**Brushes** (data, grouped into `bone`, `muscle` and `skin` layers)
- `ridge(polyline, height, width)`
- `crease(polyline, depth, width)`
- `dent(point, depth, radius)`
- `rim(polyline, around, height, width_in, width_out)`: a bony rim round an opening
- `bulge(centre, amount, radii)`: a muscle belly
- `pad(centre, radii, tilt, height)`: a raised plateau, such as the lid ring

**Plates**
- Tiles over (s, d) ranges of a profile-following layout, with bevel, back-edge thickening and overlap.
- Sculpted height fields (nose pad, nostrils) and smooth-union fillets (horn roots) are applied to the tiles' surface.

**Attachments** (each on its own bone)
- Tubes along splines for horns and claws, smooth with hairline rings.
- Fins for frills and membranes.
- Eyes with lid shells.

**Actions**
- Face morph targets for muscle actions.
- Lid shape keys for the blink.
- Bones for the jaw, tongue and lid tilts.

**Scripts** (`scripts/`)
- `study_crop.py`: a gridded full-resolution crop of a reference.
- `line_map.py`: extracts a reference's ink lines into a clean, gridded line map.
- `render_sheet.py` with `shoot.js`: renders painted and plain-clay views, posed, next to reference crops, from a `views.json`. Needs Playwright's Chromium and three r128's `three.min.js` and `GLTFLoader.js` in a folder (`npm i three@0.128.0`).

**Technical notes**
- WebGL allows 16 vertex attributes, and morph targets use them up, so pack custom attributes into vectors.
- three r128 needs `skinning: true` and `morphTargets: true` on the material.

## Element sheet template

```
## <element>
References: <files and crops used; where they disagree>
Primary mass: <solid, size in model units; widths from the front/top views>
Bone: <landmarks (rims, arches, bars, joints) and the crisp edges/planes they make>
Muscle: <each mass: origin -> insertion, where it bulges, what it moves>
Skin: <creases and folds, and which boundary each one marks>
Planes: <faces and the edges between them (hard/soft)>
Drawn lines: <name: polyline in ref px, ridge|crease|edge|joint|outline, stroke weight>
Pieces: <separate solids, features sculpted into a host, attachments>
Articulation: <bone, pivot, range; rigid vs skinned; morph targets>
Build: <which toolkit pieces>
Check: <what to compare; known differences>
```

## Lessons (Clay)

**Muzzle**
- A box, not a wedge or prow: it hardly narrows to the front, with a flat top, near-vertical sides, and a flat, near-vertical front face with slightly rounded corners.
- A front plate covers that face above an orange lip band.
- The nose pad runs along the top front edge, with the nostrils as angled, forward-facing slits at its front corners.
- The upper lip overhangs a set-back jaw: a strong overbite.

**Roof (the brown crest)**
- Distinct plates, laid out along the profile:
  - a nose plate;
  - top bands that wrap down to a first line (d ≈ 0.054);
  - a narrow strip of long plates down to d ≈ 0.075;
  - an edge row of near-square plates (joints about every 0.062) down to the orange.
- Over the eye the edge steps up, and the eye sits tucked under it.

**Horns**
- The roof's back corner drawn out: the roof's top line runs on into the horn's.
- Thick at the root.
- A long, nearly straight sweep back, curling up only at the tip.
- Smooth, *lined but not bumpy*: hairline rings.
- The root is sculpted into the roof plates.

**Eye**
- Round and wide open.
- The inner corner points down and forward to the tear duct; the outer corner closes the round outline.
- The cheekbone is the hooked rim under and behind it.

**Jaw**
- The cream lower jaw continues up behind the mouth corner as a jowl under the ear.
- The mouth line is low in front, then curves in and up to end under the ear opening.

**Ear**
- The frill sits high at the back of the cheek, under the horn, and its rolled top edge curves back to the horn's underside.
- The ear opening is a small hole below it.

**Hands and feet**
- The front hands are compact, with big hooked claws and a high dewclaw.
- The hind feet are long and digitigrade, with a heel spur and studs along the top.
