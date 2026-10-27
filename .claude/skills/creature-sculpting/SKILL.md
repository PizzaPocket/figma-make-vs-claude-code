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
- **Model what every depiction agrees on.** A single sheet, especially fan art, has quirks. Before encoding a curve, line it up across every official image (`all_heads`-style sheets of the same part) and keep what is consistent. Clay's side sheet sags his lip line, while no official image does.
- **Measure, don't eyeball.** Read positions off gridded crops and line maps. Measure each corner, joint and stroke where it actually is. A measurement between the wrong two points gives a confident wrong number: Clay's eye tilt was first measured to where two creases meet, not to the eye's corner, and came out 26° instead of about 45°.
- **Trace colour boundaries; don't sketch them.** For a colour edge (roof over face, face over jaw), classify the reference's pixels by colour and read the boundary off, column by column. Then prove it: render a true side view framed at the reference's scale and blend it over the reference. Clay's roof edge and lip were twice hand-placed "from every depiction" and were 0.07 off. The trace and the blend caught it at once.
- **Don't dismiss a reference's shape as its quirk until you have looked for it in the others.** Clay's overhanging upper lip was dropped as a side-sheet oddity, but *How to Draw* and the flight render show it too.
- **A drawn line's weight is the edge's strength.** A heavy stroke means a crisp, deep edge; a tapering stroke means the form fades out. Sculpt the edge on the side the line is drawn.
- **The references decide.** When the model and the art disagree, the model is wrong.
- **Tell overlapping layers apart before measuring.** A side view can draw the far limb peeking out behind the near one, offset by the sheet's slight elevation. On Clay's side sheet the far wing's plain fingers show above and ahead of the near wing's studded ones, so the folded fan looks twice as broad as either wing. Match details (studs, claws, shading) to decide which layer a line belongs to.
- **Know each reference's view angle before measuring from it.** Clay's "side" sheet shows the snout at about three-quarters. Its front-of-snout diagonal is the front face seen obliquely, and its short chin is the front of the chin seen at an angle. Tracing them as a true profile produced a short, set-back lower jaw, a concave muzzle front and a 45° front lip ramp, each fixed only after rounds of user corrections. For a foreshortened region, take the art's intent (what form it depicts) and build that form from anatomy; don't trace its outline.
- **When a part is "modelled after" an animal, study how that animal's part sits on its head, then find the same arrangement in the art.** The user said Clay's nose is a lion's. It was first read as the end of the muzzle shield (wrong), then as the shield itself (wrong). The references (Dragonet Prophecy cover, the top-view painting) show a lion's arrangement: the nose bridge rises out of the middle of the muzzle shield, runs forward and down along its top, and ends in a rounded leather cap set back from the shield's tip, the shield's rim carrying on round the front ahead of and below it. Same material and colour as the shield: it reads by form, not colour.
- Left and right are mirrored: model the left side and mirror it.
- Organic, not mechanical. Plates and scales vary in size and follow the form; never use a regular grid or brick pattern.
- **When the user names a part, ask what it is before building.** "Front ridge" was built three wrong ways (a bar, part of the nose, a separate shelf) before the user explained it: an extension of the roof's front. Restate your reading in one line and build the simplest version of that.
- **Simple first.** When the user says a form is too complicated, rebuild it from fewer, plainer pieces, not by adding corrections to the complicated one.
- **Check geometry numerically, not only by eye.** Probe which mesh is on top at a spot (a gap, a flap), and project measured landmarks (eye corners, lid margins) onto the reference. Both found causes that renders hid: the brown hanging below a lifted lip corner, an inner eye corner turned to 83° instead of 57°.
- **Don't stop at a list of known faults.** If a render still shows a fault you can fix, fix it before reporting.

## Construction principles

- **Look for fitted pieces.** A different colour area is often a different solid. Clay's head is an orange face mass with a dark roof of plates fitted over it, standing proud so its edge overhangs.
- **Sculpt features into their host.** A nose pad, a horn root or a brow belongs to the surface it rises from:
  - a nose pad is a height field on its plate, with the nostrils cut into it;
  - a horn root is the roof moved onto the smooth union (exponential smooth-min with a fillet radius) of roof and horn, so the plates swell up into the horn.

  Separate pieces planted on top, flared collars and separate root lofts all failed: they read as stuck on.
- **Lines are geometry, never ink.** Every line in the art becomes an edge, ridge, crease, plate gap or rim. Don't draw lines on the skin in the shader: they read as scratches on a sculpted model. Ink is acceptable only in a groove that already exists in the geometry, such as a horn ring.
- **A shield is one solid piece; its plating is carved into it.** Clay's muzzle shield was first built as separate tiles plus a front cap fitted to the front curve; the seams and the fitted cap read as a workaround (user: why can't this be one solid piece?). Build the shield as one surface with a rounded edge all round, and carve the plating into it (grooves at the joints, a low dome per tile, like an ankylosaur's fused osteoderms). Separate tiles still suit loose overlapping scales elsewhere.
- **Design clearances in, don't patch collisions.** Where a moving or nearby part (the ear) shares space with a shell, set the shell's edge by design on a line clear of that part's whole path, measured from its mesh with a margin, and check the gap numerically.
- **Lay plates out in the art's own directions.** Joints run perpendicular to the form's flow line, and strips run along it. Use coordinates that follow the profile: s along it, d the depth perpendicular to it. On a sloping muzzle the joints are therefore not vertical cuts.
- **Colour and pattern edges are measured lines.** Trace a zone edge as a side-view polyline from the art. Don't use a fraction of the body's depth: a fraction runs parallel to the spine, while the art's edges sweep (Clay's dark neck edge drops straight down into the shoulder).
- **Measure pattern rhythm.** Scan across the ink lines on the sheet to get each pattern's spacing (bands, plates, scales). Lay patterns out in model units, not normalised parameters, so sizes stay true on thick and thin parts. Put the pattern's wrap-around seam on a hidden side.
- **Resolution must match the sharpest edge.** The mesh spacing must be finer than the narrowest crease or overhang, or it renders soft.
- **Smooth, never stepped.** When carving or uniting surfaces (sockets, fillets), use a smooth minimum, and clamp it so it never cuts into a neighbouring part.
- **One piece means one mesh.** A part that should read as continuous with another (the front ridge with the roof's front band) must be built as more rows of the same surface. A separate mesh fitted flush still reads as tacked on.
- **Blink along the meridians.** Lids hinge on the canthal axis (the line between the corners, through the eyeball's centre); the margin sweeps across the eye at right angles to it. Store the blink as several in-between shapes along that arc: one straight-line shape cuts through the eyeball mid-blink.

## Sculpt from the inside out: bone, muscle, skin

No surface form is free-floating: something under it pushes it out, holds it up or lets it fold. Write every element in three layers, in this order:

1. **Bone (landmarks).** Rims round openings, arches, crests, bars and joints. Bone makes crisp edges and flat-ish planes, and does not change shape when the creature moves.
2. **Muscle (masses).** Each muscle runs from an origin to an insertion. It bulges in its belly and flattens toward its tendons. Know which one fills each region, because that tells you both its shape and how the region moves.
3. **Skin (creases, openings, scales).** A crease forms where two muscles meet, or where skin folds over something that moves (lids, mouth corner, joints). Trace each drawn line back to the boundary that causes it, and sculpt that boundary.

**Judge the forms in a plain clay render.** Paint hides missing anatomy.

**Encode the anatomy as structure, not as notes.** Name the bones, muscles and parts in the design data and generate the shape from them: landmarks (a chin's symphysis, a jaw's angular corner, a hinge) that a profile is built through, layers of named brushes, named sub-parts (shield, nose bridge, cap, nostrils). A hand-made table of numbers with the anatomy only in its note loses it: the next session can't edit "the dentary" or keep the rows true to it.

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
- **Read the opening as one outline first.** Clay's eye opening is a teardrop: the round eye with its inner corner drawn into the pink point. Build the lids over that outline and let the blink cover all of it. Corner angles, bent axes and separate tear-duct pieces were a long detour from a shape that was obvious in the drawing.
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
- `overlay_side.py`: renders a true side view at the side sheet's scale and lays the model's outline (cyan) and a half blend over the sheet. Use it to check any outline.
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

**Front muzzle and nose frame**
- When the user describes the angle between the shield and front muzzle, check
  those two planes. Reducing a convex bulge does not correct their angle.
- Keep the alveolar base, lip and lower-jaw closure coherent when changing the
  premaxilla's crown. Check the closed bite and the mouth open.
- A surface attachment built before a muzzle deformation can be sheared flat.
  Build the nose on the final shield in an orthonormal frame; measure its cap
  angle relative to that shield, not only to a world axis.
- Do not flatten overshooting loft rings into a cap: trim the meridians and
  close one face. Topology checks must accompany reference silhouette checks;
  a valid closed mesh can still depict the wrong shape.

**Muzzle**
- Bone and muscle, not a box: the premaxilla rounds the front into a U in top view, and the front is convex everywhere (an earlier box read square, then caved-in concave when its front was traced from the three-quarter sheet).
- The muzzle shield: one solid piece over the top and down round the front corner, plating carved into it.
- The nose: a lion's: a short bridge, a crisp box (flat top, upright sides), ending in the leather cap whose front is its own upright plane facing forward (cut perpendicular to a steep slope, a face points down), just behind the shield's front; comma nostrils in that face.
- Under the shield's front, orange whisker pads drape over the front teeth into the lips; the cheeks are flesh draped over the teeth and jaw, not a puffed shelf.

**Roof rim and lip**
- The roof's lower edge is a rim of square marginal scutes, like a turtle shell's edge.
- It sits about mid-height on the muzzle side and rises steadily to the eye, with small notches at the joints. Not a staircase.
- The upper lip line is straight and level, then sweeps up concave into the mouth corner.

**Roof (the brown crest)**
- Plating laid out along the profile (now carved into one solid shield; see Construction principles):
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
- An almond: the outer corner comes to a soft point and the upper lid rests over the top of the iris (the covers); the side sheet's round stare read as too wide.
- The inner corner points down and forward to the tear duct (pink caruncle).
- A thin liner on the lid margins, which stays on them through the blink.
- The cheekbone is the hooked rim under and behind it.

**Jaw**
- A dragon's lower jaw from its bones, not traced from the three-quarter sheet: the dentary carries the teeth forward to a rounded U-shaped chin (the symphysis) just behind the snout's tip, under a slight overbite. It deepens steadily backward under the jaw muscles (surangular, angular), and the retroarticular process curves up behind the hinge.
- The lip line is nearly straight: level at the front, rising gently back to the mouth corner. A lip edge that rises toward the snout's tip makes the jaw curve up like a bowl ("a Nike check").
- Judge the jaw in a true side view: its underside must be one elegant line from the chin into the throat. Where a separate part meets the skin, run the weld line along the part's own outline (the jaw's underside), never across it: a vertical cut left a stair step.
- The hinge sits under the back of the eye; the jaw drops down and back, and the cheek skin stretches across the corner of the gape (a web), not a rigid slot.
- The cream lower jaw continues up behind the mouth corner as a jowl under the ear.
- Teeth are recurved cones, oval in section; the tongue is a muscular, grooved body on bones; the lips have fleshy margins moved by FACS lip actions.

**Ear**
- A flap of skin on a thin stalk out of the face's flesh, flaring and curling like a tulip petal: orange outside, cream inside. Built as a separate hovering leaf or a solid wedge, it failed.
- Behind the head the neck's top is lower than the ear's top edge, so the neck's shell there is defined by its place round the body (a band over the top), not by a side-view line, to pass above the ear and meet the head's shield.
- It sits high at the back of the cheek, under the horn, its tip curving back toward the horn's underside. Shells near it are set clear of its path by design.
- The ear opening is a small hole below it.

**Head-neck weld**
- A separately built part never reads as one piece with the body's skin, however closely it is fitted. Put the part's own shape into the skin's field (from its measured cross-sections, which give an exact inside test, unlike nearest-face normals). Trim the part's mesh on a drawn line, and let the skin be its surface beyond it.
- Where two surfaces must meet, keep one strictly under the other up to the line and let it out gradually beyond. Surfaces that cross at a shallow angle sawtooth, and a hard cut leaves a kink the marching cubes steps on.
- The skin at a seam must carry the same bone weights as the part it meets, or the seam opens when the creature moves.
- Check bone weights numerically: list the largest weight difference across any mesh edge. A rest pose hides weight jumps, and a bend shows them as crisp bands. Clay's spine had one at every joint for many rounds.

**Body**
- Build limbs as bones with muscles laid from origin to insertion, under one skin (a smooth union of fields), never as tubes stuck onto the body. A limb with no shoulder or haunch muscles reads as chopped off.
- Trace the body's outline under the mane, spikes and frills, at their bases. Clay's first trace ran over the spike tips and made his neck and back too big. Where a limb hides the body (the chest under the upper arm), the body's line is anatomy (a cat's breastbone at elbow height), not the limb's outline.
- One mass per joint: a flat layer over the shoulder blade or hip, then the big belly below it, blended wide (0.07-0.12). Two bellies side by side read as double shoulders or balloons.
- The chest's section is a keel, not a barrel: widest up at the shoulders, so the legs hang close beside it, like a cat's.

**Looking at a part**
- Judge a plate or face square to its own plane. Clay's muzzle shield seen straight down the y axis foreshortened its steep front and hid the hammer-shaped broadening that defines his face. A camera along the shield's normal showed it at once.
- A feature that sits "at the front edge" must follow the surface that is really there. The nose followed the top profile, which ended a plate row short of the shield's true front, and kept landing a row back until it was laid along the measured front shelf.
- A face that is "pitched forward" slopes down toward the tip, foot ahead of top. Leaned the other way it undercuts into a hood with a dark slot beneath.

**Hands and feet**
- The front hands are compact, with big hooked claws and a high dewclaw.
- The hind feet are long and digitigrade, with a heel spur and studs along the top.

### Nose placement and nostril coordinates
Measure visible shield clearance relative to cap width before choosing setback.
An inward-tapered cap needs width-dependent nostril coordinates at each height;
a constant half-width misplaces the openings. Use the cap's up axis and side
normal, rather than world height and a front-only cut direction.


### Attachment tangent stability
Fit an attachment frame over the anatomical surface's local neighborhood, not
across one decorative groove; otherwise moving a cap slightly can change its
orientation sharply. Check placement and cap tilt independently.
