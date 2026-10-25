# Clay's head: element sheets

The working notes behind `head_design.json`. These follow the `creature-sculpting` skill (`.claude/skills/creature-sculpting/SKILL.md`).

**Coordinates:** reference pixels are on the 1400-px-wide side reference (Spirit978's sheet). Model units use `z = (700 - px) / 343` and `y = (830 - py) / 343`. x is Clay's left.

**Official art used:**
- *How to Draw* (Brianna C. Walsh): front three-quarter view.
- The flight render: open mouth, three-quarter view from the front.
- The limited-edition render.
- Joy Ang's covers.

Study crops are made with `scripts/study_crop.py`.

## How the head is put together

The art reads as fitted pieces, not one blob:

| Piece | What it is | Bone |
| --- | --- | --- |
| Face | Orange mass of the muzzle, cheeks and skull | `head` |
| Roof | Dark banded shell fitted over the top of the face, standing proud of it so its eave overhangs the orange. Its back corners carry on as the horns. | `head` |
| Horns | The roof's back corners drawn out | `head` |
| Nose crest | A raised pad on the front of the roof, above the upper lip | `head` |
| Lower jaw | Cream jaw hinged under the face; the mouth line between them | `jaw` |
| Eyes | Spheres sunk into the face under the eave | `head` |
| Lids | Shells hinged on the eye's canthal axis | `lidUpper.L/R`, `lidLower.L/R` |
| Ear frills | Tucked under the horns at the back of the cheek | `head` (own bones still to do) |

## Roof rim and upper lip line (traced, then checked across the official art)

Traced on the side sheet's colour boundaries, pixel by pixel (dark roof over orange face; orange face over cream jaw), not eyeballed. Then checked against *How to Draw* and the flight render, which agree on the shape. Verified by rendering a true side view at the reference's scale and blending it over the side sheet (`cmp_side`).

**The roof's lower edge**
- The roof covers the whole nose: at the front it comes down to the lip.
- From the nose it rises only gently for the front third of the muzzle (z 1.99 to 1.84, y 1.356 to 1.42).
- At about mid-muzzle it turns sharply up in a near-vertical step (z 1.83 to 1.81, up to y 1.55).
- It then climbs steeply and diagonally to the front of the eye, runs over the top of the eye with the eye tucked right under it, steps up again behind the eye (z 1.59) and runs back toward the ear.
- The rim plates (edge row) follow this line; they are thicker than the plates above, with lower edges rolled outward like a turtle shell's margin.
- An earlier pass drew this as a steady diagonal at mid-height: up to 0.07 too high in the front half and missing the step. That was wrong.

**The upper lip line**
- From the bottom of the nose it slopes down and back: an overhanging lip, lowest about a third of the way back (z 1.85, y 1.26). *How to Draw* and the flight render show the same overhang.
- From there it rises in a long, slightly concave line to below the eye.
- At the mouth corner (z 1.59) it turns sharply up, then runs back, gently rising, to the ear opening (z 1.41, y 1.656).
- It does not stop there: the line curls up and forward round the ear opening and climbs to the base of the ear frill, so the cheek's back edge becomes the ear. The neck's orange continues behind it, so this is a form edge, sculpted as a rim (anatomy: "back edge of the cheek"), not a colour edge.
- Traced on the centre of the drawn line, not its bottom edge (the first trace sat ~0.015 low at the front).
- The lower jaw's chin is a short point right under the lip's lowest point (z 1.86); its top runs just inside the lip line at the front and just above it (hidden inside the cheek) behind the mouth corner, back to the ear opening, so no gap shows.
- An earlier pass flattened this into a level line and called the dip a side-sheet quirk. That was wrong: the overhang is in every depiction.

## Roof plates

**Pieces of one kind.** An earlier version stacked an underlay, a nose plate, a front plate, overlapping shingle bands, a long strip and a rim row, which lumped into each other at the front; a later one used a separate front cap. Now every piece is the same kind of tile:
- **Bands:** from the roof's flat front edge back, joints every 0.058. Each band is a mirrored pair of tiles meeting at the ridge, running down each side to d 0.075. The first band starts right at the front edge.
- **Rim:** the edge row of near-square scutes from d 0.075 down to the eave (joints every 0.068), with lower edges rolled outward.
- **No front wall.** The references show no flat front on the snout: the orange face's top comes down to meet the front of the upper jaw (the lip), and the roof starts right there, so its bands run all the way down to the front of the upper jaw. The nose comes out of the roof's front, just above the lip.

**Tiles:** each is a solid of even thickness with a short wall and a narrow 45-degree chamfer at its edges (chamfer 0.003). They abut, with no shingle overlap; the gaps make the drawn lines. A thin dark underlay fills the gaps; its flat front end is the snout's front face.

**Directions:** laid out in coordinates that follow the head's top profile: s along it from the front edge back, d the depth below it, perpendicular. Joints are lines of constant s, running straight from the ridge down to each tile's lower end.

## Roof

**Profile.** The side silhouette, scanned column by column from the reference, has three parts:
1. The low nose crest at the tip (z 2.03–1.94, y 1.46–1.55).
2. A steep forehead rise of about 45° (z 1.91→1.70, y 1.65→1.86).
3. A long, gently rising line over the skull (z 1.70→1.54, y 1.86→1.945).

Behind the skull, that same line carries on as the top of the horn:
- (1.45, 1.965)
- (1.31, 2.01)
- (1.24, 2.06)
- tip (1.21, 2.09)

**Cross-section:**
- A broad, nearly flat top with steep sides, like a mansard roof over the muzzle.
- It is a shell offset 0.006–0.010 outside the face.

**Bands:**
- Overlapping transverse bands every 0.058.
- Each band is thickest at its back edge, like armadillo plates.
- The steps are real geometry, outlined in the shader.

**Eave line** (`dark_plate_edge`):
- The roof covers the front of the muzzle down to the lip.
- Its edge rises steeply in front of the eye.
- It steps up over the eye, so the eye sits tucked under the eave.
- It then runs back level at about y 1.80.

## Horns

**References**
- Side reference: px 175–284, py 100–230. Crop made with `study_crop.py`.
- Official art: the flight render, the limited-edition render and *How to Draw*.

**Where it comes from and how it is held**
- The horn is the roof's back corner drawn out.
- Its root (r ≈ 0.037–0.045) fills the side of the roof's back corner, behind and above the eye, from the eave up to the roof top.
- The roof's top line runs straight on into the horn's top line. To meet it, the roof's top rises slightly at the back, to about 1.91.
- The roof's edge comes back over the eye and curls under the root.
- The ear frill tucks in behind, under the horn.

**Build**
- The horn's root is sculpted into the roof. The roof plates near it are moved onto the smooth union of roof and horn (fillet radius 0.016), so they swell up and wrap the horn's base.
- The horn tube starts buried in the roof, at z 1.62, so there is no separate root piece.

**Thickness:** the horns are thick, as in the art. The root is about r 0.05–0.06 where it leaves the roof, with a broad corner section (out to 1.3 rad over the shoulder), and tapers to 0.04, 0.03 and 0.02 before the tip.

**Path:** measured edges, centreline through:
- (1.487, 1.887) r 0.036
- (1.37, 1.957) r 0.028
- (1.297, 1.999) r 0.022
- (1.245, 2.046) r 0.016
- tip (1.213, 2.096)

It is a long, nearly straight sweep back and up that barely tapers, then narrows and curls up more steeply at the end. It splays slightly outward, x 0.17 → 0.23.

**Surface:** smooth, *lined but not bumpy*.
- The rings are hairline incisions (depth 0.0007, width 0.0014, every 0.03), inked in the shader.
- They start just past the root and fade out at 88% of the length.

## Box muzzle, nose and nostrils

**Roof: a gable**, its ridge exactly on the side sheet's traced top outline (within ~0.01 from the nose tip to the skull); the shoulders drop below it. Two mirrored slopes meet at a crisp ridge down the roof's whole length (upper_head.ridge: 0.045 over the shoulders along the snout, 0.03 at the back). Every band of plates is a mirrored pair meeting at the ridge in a seam, so the lines have reflective symmetry. The roof meets the snout's flat front face along a flat front edge (the plate layout starts exactly at the front plane, not past it).

**Nose (as the user reads the references): one extruded mass,** its section like the border of the Superman shield:
- a flat top with square corners, short sides falling straight down, then two lower edges converging to a point;
- its axis follows the roof's top at the front (falling 43 degrees toward the tip, traced on the side sheet), so its top surface is the roof's top surface carried on: it emerges from it smoothly (its back dips under the roof) and its front face aims forward at the tip (2.02, 1.445);
- organically softened: rounded corners (radius 0.016), softly convex faces, and a rounded rim (radius 0.012) round the front face;
- its back is buried in the snout;
- below it, the main roof's front plate carries on down to the lip.

**Nostrils:** slits cut into the nose's two lower faces (the undersides), just behind the front face.

**Earlier attempts, all wrong:** a raised pad with nostrils on the front face; a thickened nose plate with nostrils on its sides; a hood-like wedge following the snout's surface. Each was built from my own reading of the art, not from the plain shape the user described.

**Still to check:** the nose's size and how far it juts; the nostrils barely show yet; how it compares with the flight and limited-edition renders at matched angles.

## Eye: one teardrop opening

**What the side sheet shows** (full-resolution crop, px 98-142, py 232-276): the eye's opening is one teardrop outline, a round eye whose inner corner is drawn down and forward into a point, with the pink caruncle filling the point. One dark ring runs round the whole outline. Measured from the eyeball's centre in side view, in eyeball radii: the opening (the white's edge) is a circle of radius 0.71; the point's tip is 1.30 out, 56 degrees below horizontal, forward; its sides close at about 13 degrees; the ring is about 0.28 wide.

**Build (kept simple):**
- The outline is a circle plus a wedge from the tip (`opening_frame`).
- The **lids** are two sheets over that outline, seen from the side (`eye_lid`): each runs from its margin on the outline straight out from the eye's centre, past the dark ring, and sinks into the skin. They meet at the tip and at the back of the round, so the ring is unbroken. The ring is its own rows at the margin.
- **Blink:** the upper margin slides across the opening to the lower one, covering the eyeball and the caruncle together (6 in-between shapes). The ring narrows as it closes, so the closed eye is a line.
- The **caruncle** is a low pink pad filling the point, tucked under the lid margins.
- The face is pressed in under the lids' footprint (`press_under_lids`) so its crisp forms never show through.
- Lid bones (two on the upper lid, one on the lower) and the expressions are unchanged.

**Earlier attempts, wrong:** spherical lid shells hinged on a bent canthal axis, with the caruncle as a bead on the eyeball and a separate pink "tear tail" on the skin. When the eye closed, the tail stayed visible on top of the lid. Patching a lid flap onto the tail made it worse. The opening is simply a teardrop.

**Mouth map.** The bite point (z 1.86) is where the upper and lower fronts of the mouth meet when it is closed: on the side sheet, where the orange upper muzzle meets the cream chin. The lip line starts there.
- In front of it is the **front muzzle**: under the nose its front face bulges out a little, then its underside sweeps back and down to the bite point. That underside is skin with no teeth. Its bottom corners pull up a little before turning back to the side muzzle.
- From above, the front face is rounded across (convex, the middle 0.022 forward of the sides). Its bottom edge, the front lip edge, arcs down in the middle (0.03 lower than at the corners).
- The **front ridge** (circled by the user on the flight render) is a subtle extension of the roof's front, not part of the nose and not a separate bar. The roof's front band is one simple piece, not a mirrored pair: it wraps over the ridge down to the eave and carries on, with no edge, down over the front of the snout under the nose. The front is convex forward both ways: rounded across from above (its middle 0.025 forward of its sides) and bulging in side profile (0.01). The band's open front edge follows that same curve, and the ridge is built as more rows of that same plate (front_skirt), so the two are one piece with no seam; an earlier separate ridge mesh, however flush, read as tacked on. Its only edge is its bottom, where it meets the orange front muzzle (y 1.37, one line with the side plates, rising at the corners with the front muzzle's lifted lower edge so it never hangs below it), thinning there to a near-flush rounded step.
- The lower jaw's front is as wide as the upper mouth at the bite point, so the two fronts meet across it.

**Teeth (flight render, limited edition):** small, flat, triangular ivory blades. A row of 4 across the front of the mouth at the bite point (upper and lower), then rows back along each side lip (upper z 1.835–1.62, lower 1.83–1.63). Each points perpendicular to its lip edge, tip raked 12 degrees back. No single big fang. An earlier pass ran them up the front muzzle's underside, which was wrong.

## Anatomy under the face (bone, muscle, skin)

The face surface is shaped from the inside out by the `anatomy` layers in the data. Each entry records what it is and why it is there.

**Bone:**
- **Cheekbone (the line under the eye):** in every reference, Clay's cheekbone is the heavy hooked line under the eye. Measured from the side sheet (px 109–154, py 243–277):
  - it starts thin below the front of the eye at (1.724, 1.611);
  - it runs back beneath the eye, heaviest under its back;
  - it turns up steeply at a corner behind and below the eye, at (1.643, 1.658);
  - it then sweeps back and tapers out at (1.592, 1.711).

  It is sculpted as the rim of the eye socket: 0.02 high, sloping gently up toward the eye and dropping crisply on the outside where the line is drawn. No line is drawn on the skin.

  *Correction:* an earlier "cheekbone" ridge from the pit in front of the eye to the jaw joint, and a postorbital bar, were invented without a matching line in the references. Both are removed.
- **Eye socket:** a shallow dent.

**Muscle:**
- **Ring muscle round the eye (orbicularis):** a raised pad in an ellipse 0.072 × 0.046, tilted 26° along the canthal axis and longer toward the back corner. The lids sit in it.
- **Masseter:** the full cheek above the jowl, behind the mouth corner.
- **Lip muscle (levator):** a gentle fullness in front of the eye.
- **Temporalis:** fills the skull behind the eye under the roof. It is shaped by the stations, not a brush.

**Skin:**
- The masseter's fold over the jowl.
- The ear opening.

**How the eye is held:**
- The roof's eave is the brow shelf above it.
- The cheekbone shelf is the floor below.
- The postorbital bar is behind it.
- The lid pad sits around it.
- The lids are thick shells with a rounded margin, set in that pad.

The eye is sunk 0.7·r into the face, measured from the face's surface on the raised pad.

## Cheek, mouth line and jaw

**Mouth line:** the upper lip line, traced (see "Roof rim and upper lip line" above). The face's lower edge follows it; the jaw's top runs just inside it at the front and just above it, hidden inside the cheek, behind the mouth corner.

**Jaw: a separate piece from the neck**, skinned only to the jaw bone, hinged at (0, 1.52, 1.47). Its outline is the clear line every reference draws round it, traced on the side sheet:
- Set back under the overhanging lip (a strong overbite). The chin is a short point at z 1.86, right under the lip's lowest point.
- The underside drops back to its lowest at z 1.77 (y 1.206), then rises to the throat notch (z 1.60, y 1.38), where the neck begins.
- From the notch its back edge is the heavy line running back and up along the neck: (1.55, 1.41) → (1.49, 1.43) → (1.44, 1.46), then turning up into the ear opening at z 1.39.
- At the back it is as wide as the cheek (the jowl). It stands proud of the neck, so its back edge reads as a step in the form, not a seam or a drawn line.
- Skin: cream with faint pebble scales, larger and softer than the face's. The neck's transverse throat bands start below its back edge; there are none on the jaw.

The underside of the overhanging lip in front of the jaw is skin, not palate.

## Ear frill and ear opening

**Measured** on the side sheet (frill crop, px 205–262, py 188–224): an almond leaf about 0.18 long and 0.075 wide. Its broad base sits at the back of the cheek (0.232, 1.775, 1.425); its tip points back and up to (0.238, 1.905, 1.235), under the horn.

**Shape**
- It lies close along the side of the head, face turned outward. The side sheet shows its whole face, not its edge.
- It is cupped like a horse's ear laid back: a pale peach hollow inside, an orange rim round it, and the top edge rolled out and over.

**Seating:** it must sit on the face surface. Set slightly inside, it was buried, and only its top edge showed, as a spike.

**Ear opening:** a dark hole at (1.420, 1.638), just above where the mouth line ends.

## Known differences after this pass

- **Frills:** seen from above they stick out flat like blades. They should stand up and cup forward.
- **Closed eye:** it bulges, because the eye and lid stand out of the socket. The lid should sink into the face as it closes.
- **Anatomy forms:** the cheekbone, lid pad and masseter now shape the surface but still read soft in the plain clay render. They need more contrast, and the shelf needs a firmer, more continuous top edge.
- **Back of the head:** the roof's back edge is a flat cap. The neck plates and mane will cover it, but the joint still has to be built.
- **Horn roots:** a small shading seam shows at the top of each root, where the morph starts. In the art the root also sits a little further back on the corner.
