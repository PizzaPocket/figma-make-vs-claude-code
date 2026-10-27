# Clay's head: element sheets

## Current correction: front muzzle plane and nose frame

This section supersedes the older walkthrough settings below.

**Evidence.** The user specified a near-right-angle turn from the shield plane to
the orange front face, rather than merely less puffing. The How to Draw crop
(`refs/study/muzzle_htd_grid.jpg`, source width 1641, box 550,230–920,600) shows
the shield turning into a distinct front above the lip. The flight crop
(`refs/study/muzzle_topshot_grid.jpg`, source width 782, box 580,385–760,585)
shows the same change of plane and a nose raised above the shield. These are
projected views, so their apparent angles are not direct 3D measurements.

**Premaxilla / maxilla.** `premaxilla` extends the anterior crown relative to its
alveolar base, fading smoothly from z 1.8 to 2.017. The crown extension is 0.20
before the existing snout compression. Height is measured between the local lip
and crown; the lip and everything below it receive zero extension. This changes
the plane relationship, not just the skin's bulge. The front keeps a small
0.016 convex profile and its rounded transverse contour. All head skin,
expression keys and bone anchors use the same field. The nose is constructed
after this field, as described below.

**Jaw coherence.** The dentary, symphysis, coronoid / retroarticular profile and
hinge retain their existing geometry. Sampled lip-line / alveolar positions
and all generated lower-jaw top landmarks have zero longitudinal displacement.
The geometric shield/front landmark angle is about 90 degrees after the snout
compression. This verifies the requested construction; it is not proof of an
exact character match. Review the full mouth open as well as closed.

**Nose.** The bridge and cap are 25% wider (maximum half-width 0.065) and their
stations sit 0.032 farther back along the carrier than the previous version;
the cap centre is now s 0.010. The foot is ray-bound to the actual shield mesh
at each lateral sample. Build that carrier in the finished muzzle coordinates,
derive an orthonormal tangent/normal frame, then add the nose height (0.046).
The cap plane is set at 45 degrees to that local shield plane. This remains a
visual fitting parameter, rather than a claimed angle recovered from the art.

**Flap.** The old loft ran past the cap and projected the excess rings onto its
face. It had 80 near-zero-area triangles and overlapping face layers. Each
meridian now terminates at the cap boundary and one radially sampled disk
closes it, with the dome, bevel and carved nostrils on that disk. The nose is a
closed, consistently wound surface without the collapsed triangles.

**Lesson from the rejected first render.** Applying the muzzle's deformation
to the already-built nose sheared the leather cap almost flat against the
shield. A closed mesh and a correct muzzle angle did not make that visual
result acceptable. The nose must be built in the final shield frame and
checked in profile against the reference before reporting success.

**Review.** `views.json` sets `muzzle_before` and `muzzle_correction` put the same
profile and three-quarter cameras beside reference crops, plus the nose from
front/top and the jaw open in plain clay. References and generated snapshots
remain in ignored `refs/` and `out/`. Remaining unrelated head issues include
the eye-ring width and ear/jaw-back-edge work in `CHECKLIST.md`.

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

**Path: a simple S** (s_curve in head_design.json). The horn rises steeply out of the back of the head (48 degrees above straight back), flattens as it sweeps back (7 degrees at mid-length), then curls up toward the tip (62 degrees). The length (0.485) is fitted so the tip lands on the side sheet's (px 283, py 116). It splays outward from x 0.15 to 0.23. *Earlier, wrong:* a path through six hand-placed points, which zigzagged.

**Surface:** smooth, *lined but not bumpy*.
- The rings are hairline incisions (depth 0.0007, width 0.0014, every 0.03), inked in the shader.
- They start just past the root and fade out at 88% of the length.

## The sheet's head turn (snout length)

The side sheet draws the head turned a few degrees toward the viewer. The front of its snout, a darker band from the tip back to a crease at px 80-95, is the muzzle's front face and front corner. Measured as if it were a true side view, that read as extra length and a forward slant, and the slant was then mirrored onto both sides of the head. With the muzzle about 0.21 wide, a turn of about 25 degrees accounts for about 0.07 of the sheet's snout. So every head part is compressed toward the eye from z 1.72 by 0.78 (snout_turn; the tip moves from 2.02 to 1.95), which also stands the front up straighter. Measurements below are as taken from the sheet, before that correction.

**Roof front:** the front band and the snout's front are one piece raised from the face itself (front_shell), like the body's shell. It covers the front of the snout down to the roof's level lower edge, and the band's strip of the top and sides back to its joint. It has a rounded edge along the joint and the bottom, round the corners too, so it has no seams or notches. *Earlier, wrong:* the front band, a skirt hung from it, and the side band's lower end were separate surfaces that never met at the corners.

**Top line:** between the brow (z 1.706) and where the nose begins (z 1.953), the roof's top line is one smooth bend fitted to the traced points (each moved 0.022 at most). The trace stepped steep, flat, steep there.

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

**Upper lip over the upper teeth:** in most images only the lower teeth show, rising plainly from the lower jaw. So the upper teeth grow from the roof of the mouth, inward (inset 0.03) and up (0.02) behind the upper lip, the front row set back 0.02. With the mouth closed the lip hides them; open, they show just behind it.

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

**Re-measured, with the head-neck weld (see body_sheets.md):** the tip is at (px 258, py 190), so (0.255, 1.866, 1.289). It had stood 0.05 too far back and 0.04 too high, like a spike behind the horn. The base sits outside the neck shell's rim (x 0.285), so the ear shows as a leaf at the back corner of the head, as on the Dragonet Prophecy cover. Behind the cheek line the face mesh is trimmed away and the body's skin is the head's surface.

## Known differences after this pass

- **Frills:** seen from above they stick out flat like blades. They should stand up and cup forward.
- **Closed eye:** it bulges, because the eye and lid stand out of the socket. The lid should sink into the face as it closes.
- **Anatomy forms:** the cheekbone, lid pad and masseter now shape the surface but still read soft in the plain clay render. They need more contrast, and the shelf needs a firmer, more continuous top edge.
- **Back of the head:** the roof's back edge is a flat cap. The neck plates and mane will cover it, but the joint still has to be built.
- **Horn roots:** a small shading seam shows at the top of each root, where the morph starts. In the art the root also sits a little further back on the corner.

## Ear, sculpted (rolled cup)

**On the side sheet (gridded crop, px 200–260, py 188–225):** the ear is a horse's ear laid back, not a flat leaf.
- **Rim:** the upper front edge is a thick, rolled orange rim along a nearly straight line from base to tip.
- **Hollow:** below the rim, a pale peach hollow faces out. Its front boundary is a dark fold line, from the upper rim about a third of the way along down to the lower edge about halfway.
- **Base:** the front third is orange, and it grows out of the top of the cheek line.

**Built (`ear_frill`):**
- **Cross-section:** each section is an arc round the ear's axis, shallow at the hollow's bottom (`depth` 0.45 of the half-width). The lower edge curls up 95° and the upper front edge 150°, over into the rim (`roll_deg`).
- **Solid:** it has real thickness (0.007, thinning toward the tip), with closed edges. The root dives into the head (`root_sink`, `root_len`).
- **Paint:** pale inside, orange behind and on the rims, with the fold line where the art draws it.
- **Fixed by the way:** the neck shell's rim was traced along the middle of the scalloped band; it now follows its lower edge, 5–8 px lower near the head (`zones.dark_edge_px`). So the rim runs under the ear, as drawn, not across its base.

**Still to do:** a small round knob where the shell's rim ends at the cheek line under the ear's base.
- **Knob under the ear, fixed:** it was the neck shell's rim stopping dead behind the cheek line, 0.03 proud of the face beside it. The shell and its rim now taper to nothing over the last 0.06 before the line (`anatomy.head_weld.shell_taper`), so the rim band runs out into the S line as drawn.
- **Face contour resolution:** doubled (`N_AROUND` 192), so the trimmed face edge follows the cheek line in steps of about 0.01 instead of 0.02.

## Ear, attached (user: "floating off his head")

**Fault:** it was a thin shell standing off the shell of the neck, with air behind it. On the Dragonet Prophecy cover the ear grows out of the head's top-back corner, with a broad root fused to the head.

**Built:**
- **Root:** the base sits at the face's top-back corner (0.275, 1.78, 1.44), broad at the root (`root_width`) and sunk a little into the head.
- **Body:** behind the hollow the ear is a solid body (`body` 0.06 at the root, thinning to the tip) that runs back into the head, so there is no gap behind it from any side.
- **Paint:** the back is the head's dark skin round its root.
- **Tip:** it lies closer along the neck (x 0.24).

## Open mouth: stretching skin, not two rigid pieces (user)

**Faults:**
- **Rigid gape:** when the jaw dropped, face and jaw parted as rigid pieces, so the gape ran back as a slot toward the hinge.
- **Narrow strut:** behind the last teeth the jaw's top edge climbs steeply (it hides in the cheek when shut), leaving a thin strut there.
- **Flat inside:** the mouth's floor and palate were flat closing faces, and the jaw's box section (squareness 3.6) read as a plank.

**Dragonet Prophecy cover:** the open mouth is a deep, dark cavity, and the gape ends in a rounded corner of cream cheek skin under the eye.

**Built (`mouth` in head_design.json):**
- **Cheek web:** at each corner, a web of skin from the upper lip's edge to the lower jaw's edge, from the hinge (z 1.47) to the mouth corner (z 1.59), its front edge bowed forward into a rounded corner. Its upper edge rides the head and its lower edge the jaw, so it lies folded in the cheek when shut and stretches across the back of the gape when open.
  - **Two layers:** cheek skin outside (orange along the lip, cream below) and the mouth's lining inside.
  - **Corrective shape:** the jaw's angle drives `jawOpen` (jaw / 0.6), which bows the stretched skin outward (0.035 at full opening), so the cheek fills out instead of stretching flat. The viewer sets it from the jaw.
- **Palate and floor:** the palate arches up 0.035 and the floor dips 0.03 into a trough for the tongue (`inner_dip` on the lofts).
- **Jaw section:** a rounder U (squareness 2.4).
- **Lining:** darker red.

**Still differs from the cover:** the lower jaw looks shallower under the teeth than on the cover. Its depth is measured on the closed side sheet (about 0.11, a third of the upper jaw's), while the cover's three-quarter view from below shows it deeper.

**Jaw joint and teeth (next round):**
- **Joint:** it now sits at the back end of the mouth line, level with it (0, 1.60, 1.45), where reptiles have it (quadrate to articular). It was 0.08 lower, and the low pivot swung the chin forward as the jaw opened. Now the jaw drops down and back, its tip well behind the upper jaw's, as in the flying painting (ClayTopShot).
- **Teeth:** cones, as both open-mouth paintings show. The upper teeth are 1.4× longer (hidden behind the lip when shut), the lower 1.15× (they show along the closed lip).
- **Cheek web:** its outward bow leaves both edges tangentially (sin²), so it swells out of the lip and the jaw without a lip of its own.
- **Muzzle rounding:** tried and backed out. Narrowing only the last 0.08 of the snout made a pinched, concave beak under the wider roof plates. To redo it: a long, gentle convex taper over the whole front muzzle, and small corner radii.
- **Muzzle taper:** the muzzle narrows from the eye forward in one long convex curve to 0.86 of its width at the tip, with small rounded front corners (`upper_head.muzzle_taper`). Checked from above and below, where the outline is convex with no pinch; not yet checked on the full model.
- **Caved-in front, fixed:**
  - **Measured:** rays cast from the front showed the lip's underside running back from the front plate's edge on a concave 45° ramp (1.961, 1.915, 1.885, 1.863 down the middle).
  - **Cause:** the ramp came from tracing the side sheet's diagonal at the snout's front as the lip sloping back. The sheet shows the snout three-quarter on (the user's reminder), so that diagonal is the front face and front corner seen at an angle.
  - **Fix:** the lip's lower edge at the front stations now sits level with the bite, rising only over a small radius at the tip (`upper_head.front_lip_note`). The front comes down under the plate almost flush (1.992, 1.982, 1.975, 1.947, 1.928) and rolls back into the lip; 93% of the front measures convex.
  - **Also fixed:** the palate arch's falloff ran the wrong way and arched the lip's underside at the front. It now arches only inside the mouth.
  - **Failed on the way:** a sculpted dome on the face. It overshot into a bumper and broke the front plate built on it.

## Ear grown out of the face (user: hovering off the face; build it from the face)

- **Section:** one closed loop: the hollow (an arc curling up at the lower edge and over at the upper front edge into the rolled rim), then back round its solid back.
- **Root:** the loft starts from a footprint on the face's own surface at the top-back corner of the cheek (y 1.785, z 1.47), where the side sheet's S line behind the cheek begins at the ear's base. It is an oval 0.06 along the ear by 0.034 across, and the surface rises out of it tangentially (a fillet over the first fifth) into the section.
- **Paint:** the root keeps the face's pebbled orange, giving way to the ear's colours along the fillet.
- **Shell:** the neck shell now tapers to nothing over 0.13 behind the cheek line (`head_weld.shell_taper`), so its lumpy rim no longer piles up round the ear's root.
- **Still to improve:** close up the ear is thin, and the face of its root is a flat facet.

## Eye: liner and resting lid (user: liner too thick, pulled off the lids when blinking; shape not the references')

- **Liner:** now a thin line, 0.095 of the eyeball's radius on the upper lid and 0.065 on the lower (it was 0.17 on both). It closes into one thin line as the eye blinks; before, the lower lid's broad band stayed behind as a dark crescent.
- **Resting lid:** the upper lid now comes down across the top of the iris (`upper_rest_closed` 0.17), as the painted covers show, and the blink runs on from there.
- **Still to do:** the outer corner is round. The references draw an almond with a pointed outer corner, back and slightly up. That needs the opening described by its radius round the eye's centre, not along one axis from the tear duct, which fixes the outer corner on that axis.

### Ear, re-sculpted as a stalked tulip flap
The ear is no longer a solid wedge. It is a thin flap of skin (0.008) growing from a narrow stalk (0.18 of its widest half-width) out of the face's flesh. It widens to its fullest at 0.55 of its length and narrows to the tip. Its section curls 110° at the lower edge and 165° at the upper front, so the orange outside rolls over the cream hollow like a tulip petal. That matches the side sheet's ear: a pale hollow with an orange rolled rim. The root keeps the face's look, so the stalk reads as face flesh.

### Upper mouth: cheek flesh draped over the teeth (lip_tuck)
The user saw the upper mouth as puffed out. Measured on the build, the upper lip's edge stood 0.04–0.055 outside the lower jaw on each side along the whole mouth, a shelf overhanging the bite. In the references the cheek lies over the teeth: the upper teeth sit just outside the lower ones, with the lip skin over them. So the lip edge now comes in to 0.012 outside the lower jaw. The cheek curves in to it near the lip only (power 2.5), and the tuck fades out at the mouth corner (z 1.58–1.63) and in front of the bite (z 1.84–1.88). The upper teeth follow the tucked edge (inset 0.012), and they now also follow the muzzle taper, which they previously ignored.

### Nose after a great cat; roof plates as ankylosaur osteoderms
**Nose.** The old nose read as a hollow frame: an extruded shield with a flat front, a thin rim and deep triangular nostril cuts. It is now a cat's nose leather (rhinarium) at the end of the nasal bones:
- a rounded-shield section, 0.135 wide and 0.068 tall, that swells from 0.72 to full size as it comes out of the roof;
- a low domed front (0.014);
- comma nostrils, laid onto the surface from a measured centreline, opening at the lower outer corners and curling up and back along the sides;
- a shallow philtrum groove down the middle of its lower part.

It sits 0.01 further forward (front top at z 2.016, so the dome's front is at 2.03, matching the side sheet's tip at 2.02–2.03). That keeps its lower half proud of the snout's dark front plate; buried, the nostrils hid.

**Roof plates.** Each roof plate is now a low dome (0.004 higher in its middle), like an ankylosaur's skull osteoderms, so the ridge reads as bony scutes, not flat tiles.

### Teeth, tongue and lips for expression and speech
- **Teeth** (`tooth()`) are now a reptile's, not flat four-sided shards:
  - Each is a cone rooted 0.004 into the gum.
  - Its section is an oval flattened side to side: across the base 0.6 of its length along the jaw, 0.018 thick.
  - It tapers to a sharp tip that curves back toward the throat by 0.18 of its length. The front row is flattened front to back and curves half as much.
- **Tongue:**
  - A muscular body in the floor's trough, rounded across, with a median groove (0.004).
  - Thick at the root (0.03) and thinning to a broad rounded tip (0.012) that lifts a little off the floor.
  - It sits on the three tongue bones. Positive `tongue` curls the tip up toward the palate; negative pushes it through the floor, so it is never used.
- **Lips** (`mouth.lip_roll`): a fleshy rounded margin, 0.004 proud and centred 0.006 from the edge, on both the upper lip (face) and the lower (jaw).
- **Muscle actions** (FACS):
  - On the face: lipCornerPull (AU12, smile), lipStretch (AU20, "ee") and lipFunnel (AU22+18, "oo").
  - On the jaw's skin (`"mesh": "jaw"`): lowerLipDepress (AU16) and lipCornerDepressJaw (AU15).
- **Speech visemes** are new poses:
  - say_ah: jaw open, lower lip down.
  - say_ee: stretched lips, lower lip down, a little smile.
  - say_oo: funnelled lips.
  - say_th: tongue tip lifted to the front teeth.
- happy, worried and snarl now also use the new lip actions. The `speech` view set renders them all at the mouth.

### Eye: almond outline
The opening's back half was a full circle, so the eye stared round. It now tapers from the round toward a soft cosine point at the outer corner (`opening.back_point` 0.85). The upper lid rests 0.26 of the way closed (was 0.17), over the top of the iris. That makes the covers' almond, while the side sheet's pink inner point stays. The liner and blink are unchanged: thin, and staying on the lid margins.

### Lower jaw from its bones (`lower_jaw.bones`, `jaw_from_bones`)
The jaw is no longer a traced table. It was traced from the side sheet, whose snout is at three-quarters, so the sheet's short chin at z 1.86 was the front of the chin seen at an angle. The profile is now generated from named bones:
- **Symphysis:** the U-shaped chin at z 1.985, just behind the snout's tip under a slight overbite, rounding off over its last 0.03.
- **Chin:** its lowest point at z 1.89.
- **Alveolar margin:** the tooth row's top edge, 0.006 below the upper lip's edge, so the jaws close along their whole length.
- **Coronoid line:** the top edge behind the mouth corner, rising inside the cheek.
- **Throat notch.**
- **Retroarticular:** the deep back of the jaw (angular, retroarticular) lies inside the throat's skin, so the visible back edge is the weld's cheek line. Deepened below that line, it hung out of the throat as trimmed blades.
- **Half-widths** at each landmark.

The tooth rows run the whole jaw. The upper row sits 0.01 outside the lower, never outside the lip. The tongue and its bones reach to z 1.93.

### Muzzle shield (one solid piece) and the lion's nose
**Shield** (`muzzle_shield`, `muzzle_shield()`): one surface from the snout's front back to the roof's end, wrapping down over the front of the snout, its edge rounded all round. The plating (layout from `roof_plates.layout`) is carved into it as grooves at the band joints, down the ridge and along the rim row, with a low dome per tile, like an ankylosaur's fused skull armour. It replaced the separate tiles (`roof_plates`), the front cap fitted to the front curve (`front_shell`) and the underlay, all removed.

**Lion's nose** (`lion_nose`, `lion_nose()`): its bridge rises out of the shield's top at mid-muzzle (s 0.30, z 1.87) and runs forward and down the top. It broadens and gains height, flat-topped, its base flaring into the shield. It ends in a rounded cap whose front stops 0.03 back from the shield's front edge, with the shield's rim carrying on round the front ahead of it. It is the same material as the shield, with comma nostrils in the cap's front.

**Ear clearance, by design:**
- Behind the eye, the shield's lower edge runs at least 0.022 above the ear's top edge, measured from the ear mesh (`ear_clearance.ear_top`).
- The neck's shell lies flush on the skin within 0.006 of either ear, rising to full height by 0.025 (body `anatomy.ear_clearance`).
- Measured after: along the ear both shells are no closer than the skin the ear lies against (0.004–0.009), touching only at the root it grows from. Before, the neck shell came within 0.002 of the ear's rolled rim.

### Shield skirt edge; whisker pads
- The shield's front skirt now rounds off toward its side ends and its bottom edge, like the rest of the shield's edge. At full thickness out to its ends it stood out as square tabs at the bottom corners.
- Lion's whisker pads (`upper_head.front.whisker_pads`) swell 0.008 either side of a philtrum groove on the orange front below the shield's rim, sculpted into the front face. They stay subtle, since the covers show only a narrow orange lip band there.

### Teeth: fewer and stouter
Re-read on the Dragonet Prophecy cover's open mouth: about six or seven stout cones show per side of each jaw, with gaps between them. The model had nine or ten small spikes per side, a saw blade. Now upper 7 per side (0.042–0.064 long) and lower 6 (0.03–0.046).
- **Lower jaw, heavier:** the covers draw the cream jaw's depth at the front at about 0.45 of the upper jaw's height, with a squared chin. The chin's lowest point goes from 1.213 to 1.188 and the symphysis from 1.262 to 1.232 (`lower_jaw.bones`).

### Walkthrough fixes: lip line and jaw profile
- **Bowl and Nike-check front (user):** the upper lip's edge rose 0.045 over the snout's last 0.1, and the jaw followed it up. The lip line is now nearly straight: level at the front (1.268–1.277), rising gently back to the mouth corner. That also brings the front of the muzzle further down the face.
- **Stair step (user):** the visible jaw's underside ended at y 1.285 at the throat notch, where its hidden back followed the weld's cheek line from 1.385, a jump of 0.1. It is now one smooth line: symphysis 1.212, chin 1.188 at z 1.89, the throat junction at 1.345 (z 1.58), rising on inside the throat to the ear (`lower_jaw.bones.throat_junction`, `retroarticular`).
- **Weld:** the cheek line's lower leg now runs diagonally along the jaw's underside instead of dropping vertically at z 1.60–1.62, and the jaw's own sections join the skin's field forward to z 1.72 (body `head_weld.parts[].zcut`). The throat skin wraps the jaw's underside with the jaw's own shape, with no cut.
- **Front face:** the orange front below the shield bulges 0.03 forward at mid-height (`front.convex_side`).

### Lion's nose, reshaped (walkthrough)
- **Bridge:** short, about 0.1 along the profile from its root to the cap, instead of rising from mid-muzzle.
- **Section:** a crisper box (squareness 7): flat top, upright sides, small rounded corners.
- **Cap face:** the leather cap ends in its own flat face, an upright plane facing forward through the cap's top front corner, rounded at its edge (0.01). The nose runs on past it and is cut back to the plane. Cut perpendicular to the steep front slope instead, the face pointed down and showed from the front only as a thin band.
- **Nostrils:** commas carved into the face at its lower outer corners.
- **Position:** the face sits 0.025 behind the shield's front edge, so the shield's rim carries on round the front ahead of and below it.

### Front of the muzzle: convex and taller (walkthrough)
- **Taller:** with the lip line straightened, the orange front below the shield runs from the skirt (y 1.37) down to the lip at 1.268–1.277, more than twice its old height.
- **Fuller:** it bulges 0.035 at mid-height and rounds across broadly (`front.across_power` 2.5), with the muzzle's corners rounding more (`muzzle_taper` corner radius 0.05, down to 0.8 of the width). The whisker pads are broad (0.055) and the philtrum is a faint groove.
- **Measured:** narrow pads had left a valley at x ±0.08 at every height, and a parabolic bulge ended in a ledge where the front met the corner. Ray-cast across the front, the remaining slope change at the corners is about 0.005.

### Eye at rest (walkthrough)
- **Lid:** the upper lid rests only 0.12 closed (it was 0.26).
- **Gaze:** points straight out with a little forward and slightly down (`eye.gaze` [0.98, -0.12, 0.12]), so from the side the iris sits centred in the round of the opening, as a horse's eye does at rest. With the old gaze (a little up, more forward) the iris sat high and forward, white showing below and behind it, and he seemed to peer up toward the top of his head.

### Upper muzzle as a hammer; the shield one piece; the lion's nose on its front edge (user)
- **Look square to the shield's plane.** The `topview` views look down the shield's normal (about 27° off straight down), not down the y axis. Seen straight down, the steep front slope foreshortens and the hammer disappears.
- **Hammer:** seen square to the shield, the upper muzzle waists in to 0.126 at z 1.85 and broadens to 0.163 (top) / 0.17 (low) at the front (`upper_head.rows`, `hammer_note`). The front corners are cut across by a straight chamfer with softened ends (`muzzle_taper.corner_shape` "chamfer"), angular but not a box corner. The low width is barely more than the top width at the front, so the shield does not fold down over the sides there.
- **Shield, one solid piece** (`muzzle_shield()`): the face's own loft, cut to the region inside the plate edge, subdivided and raised by the shield's thickness with its edge rounded. Its plating is carved into it. The old ring-built shell and its tacked-on front cap and skirt are gone.
- **Lion's nose:**
  - **Section:** a rounded ridge (squareness 3.5), 25% wider than before (cap half-width 0.052) and standing 0.046 proud. At squareness 7 the bridge's top fluted out into a box at the cap.
  - **Placement:** the cap sits almost on the shield's front edge. Ahead of the top profile the nose runs on along the shield's measured front shelf (`lion_nose.front_run`), and its face lands 0.022 along it.
  - **Cap face:** a plane pitched forward 30° from upright and sloping down toward the tip, so its foot is ahead of its top. It is domed out 0.009 so it reads slightly convex. Leaning the other way, it undercut into a hood.
  - **Nostrils:** commas on the side-front edges, where the face turns into the sides (path in fractions of the cap's half-width and of the face's height). They are cut along the face's normal and in from the side.
