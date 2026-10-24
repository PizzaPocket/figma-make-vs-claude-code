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

The horn is not a cone planted on the skull:
- It starts embedded in the roof's top shoulder above the eye (x ≈ 0.15).
- It rises out of the roof as a ridge.
- It leaves the skull behind the brow.
- It sweeps back nearly level, splaying slightly outward (x 0.18 → 0.235).
- It curves gently up at the tip.

**Path:** a Catmull-Rom spline through 7 points (in the data).
- Radius: 0.012 (buried start) → 0.042 → 0.003 at the tip.
- Rings every 0.045, starting where the horn leaves the roof.

## Nose crest

**What the art shows:**
- The nose is its own feature on the top front of the muzzle, above the upper lip.
- It is a raised pad with a centre ridge.
- On each side it flares out over a nostril, and the flare flattens onto the plane of the muzzle at the nostril's outer corner.
- It joins the muzzle at the front, between the nostrils, and fades into the roof behind.
- In the side reference, the nostril is the curled line at px 36–54, py 312–335.

**Build:**
- A shell on the roof surface, from z 2.035 to z 1.86.
- Its half-width is given as an angle around the roof: 0.95 → 1.05 → 0.3 rad.
- Its height is 0.01–0.02. The height profile `(1 - u²)^0.8` gives the ridge and the flat outer corners.
- The nostrils are troughs under the flares (z 2.025–1.945, 50–90% of the way across), shaded dark.

The small dark pit at the eave notch in front of the eye (px 81, py 311) is kept as a minor detail. It is not the nostril.

## Eye and lids

**Eyeball:**
- Centre (z 1.695, y 1.692), measured at px 120, py 250. Radius 0.031.
- Sunk 0.55·r into the face, under the eave.
- Gaze is out and about 30° forward.

**Canthal axis** (the eye's meridian):
- It runs from the tear duct at the front-lower corner (px 114, py 262) to the back corner where the upper crease and the zig-zag lower crease meet (about px 140, py 249).
- It rises **about 26° toward the back** in the side view.
- In 3D it lies in the plane of the face side, perpendicular to the gaze, so the back corner sits further out than the front.

**Lids:**
- Each lid is a shell on a sphere 1.1× the eyeball, parametrised by:
  - ψ along the canthal axis: both lids pinch to the corners, which gives the almond shape;
  - φ around the axis.
- The upper margin is 36° above the gaze and the lower margin 42° below. Both margins have a dark rim.
- **Blink:** each lid bone lies along the canthal axis.
  - A turn about the axis sweeps the upper lid forward and down across the eye (1.2 rad).
  - The lower lid rises 0.25 rad to meet it.

## Anatomy under the face (bone, muscle, skin)

The face surface is shaped from the inside out by the `anatomy` layers in the data. Each entry records what it is and why it is there.

**Bone:**
- **Cheekbone and zygomatic arch:** a shelf from below the front of the eye (1.75, 1.60) back to the jaw joint under the ear (1.44, 1.672). Its crisp top edge is the floor of the eye socket, and it slopes off below into the masseter.
- **Postorbital bar:** closes the socket behind, rising from the cheekbone to the eave.
- **Eye socket:** a shallow dent.

**Muscle:**
- **Ring muscle round the eye (orbicularis):** a raised pad in an ellipse 0.072 × 0.046, tilted 26° along the canthal axis and longer toward the back corner. The lids sit in it.
- **Masseter:** the full cheek above the jowl, behind the mouth corner.
- **Lip muscle (levator):** a gentle fullness in front of the eye.
- **Temporalis:** fills the skull behind the eye under the roof. It is shaped by the stations, not a brush.

**Skin:**
- The measured zig-zag lower lid crease, where the lid pad meets the cheekbone.
- The upper lid crease, along the postorbital bar.
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

**Mouth line** (measured):
- It runs low and nearly level from the lip to the mouth corner under the eye (z 1.72, y 1.34).
- Behind the corner it curves inward (concave) and then up, ending just under the ear opening:
  (1.65, 1.38) → (1.58, 1.43) → (1.52, 1.48) → (1.48, 1.53) → (1.45, 1.58) → (1.42, 1.62).
- The face's lower edge and the jaw's top edge both follow this line.

**Jaw:**
- Set back under the overhanging lip: a strong overbite.
- The chin juts forward and down.
- It hinges at (0, 1.52, 1.47).

The underside of the overhanging lip in front of the jaw is skin, not palate.

## Ear frill and ear opening

- A cupped leaf from the back of the cheek, base (0.20, 1.785, 1.43), up and back to the tip (0.265, 1.905, 1.235).
- Its rolled front/top edge curves back to meet the underside of the horn.
- The ear opening is a dark hole at (1.420, 1.638), just above where the mouth line ends.

## Known differences after this pass

- **Frills:** seen from above they stick out flat like blades. They should stand up and cup forward.
- **Closed eye:** it bulges, because the eye and lid stand out of the socket. The lid should sink into the face as it closes.
- **Anatomy forms:** the cheekbone, lid pad and masseter now shape the surface but still read soft in the plain clay render. They need more contrast, and the shelf needs a firmer, more continuous top edge.
- **Back of the head:** the roof's back edge is a flat cap. The neck plates and mane will cover it, but the joint still has to be built.
- **Horns:** in the front view they still rise a little steeply compared with the limited-edition render.
