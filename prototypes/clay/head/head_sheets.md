# Clay's head: element sheets

The working notes behind `head_design.json`. These follow the `creature-sculpting` skill (`.claude/skills/creature-sculpting/SKILL.md`).

Coordinates:
- Reference pixels are on the 1400-px-wide side reference (Spirit978's sheet).
- Model units use `z = (700 - px) / 343` and `y = (830 - py) / 343`.
- x is Clay's left.

Official art used for checks:
- Brianna C. Walsh's *How to Draw*: front three-quarter view.
- Joy Ang's covers: three-quarter views.

## Nose plate and muzzle

**References**
- Side reference crop: px 0–120, py 290–420.
- *How to Draw* front three-quarter view.

**Primary mass:** a wedge.
- It runs 0.12 deep from the prow (z 2.017) to the back edge of the nose plate (z ≈ 1.82).
- The front face is blunt and nearly vertical, about 0.08 tall: px 9→12, py 334→362.

**Structure underneath:** the nasal bones make a flat roof, and the premaxilla makes the blunt front. There is no muscle mass here, so the surfaces are flat.

**Planes**
- A flat top that rises toward the brow.
- Near-vertical sides.
- Hard edges between the top and the sides (squareness 5).
- In the art, a soft turn into the front face.

**Drawn lines**
- The back edge of the nose plate is a **crease**: (1.837, 1.434) → (1.79, 1.62).
- Plate segment lines run across the top: painted, spaced 0.085.

**Openings:** the nostril.
- Dent position: z 1.805, y 1.513.
- It sits at the back top corner of the plate on the side, not at the tip.

**Articulation:** rigid, on `head`.

**Build:** an `upper_head` loft (rows 2.017–1.85), the `dark_plate_edge` line, a crease brush and a dent brush.

**Check**
- The dark plate now reaches the lip at the front.
- The underside of the overhang is skin, not palate.

## Eye, lids and brow

**References**
- Side crop: px 95–150, py 230–290.
- *How to Draw*.
- Covers.

**Primary mass:** a sphere, measured radius ≈ 0.026. The model uses 0.033, since part of the sphere is sunk into the socket. The eye is sunk 0.55·r into the side plane.

**Structure underneath**
- The brow is a shelf of bone over the socket. A ridge brush, 0.022 high, runs (1.749, 1.720) → (1.574, 1.793).
- A cheekbone ridge runs under the eye: (1.735, 1.595) → (1.568, 1.700).

**Planes:** the socket is a shallow dent (radius 0.036) between the brow shelf and the cheek ridge.

**Drawn lines**
- The eye crease behind the lid is a **crease**: (1.671, 1.682) → (1.574, 1.743).
- The zig-zag line under the eye is still to do. It runs back to the mouth corner and is also a crease.

**Look:** every official image shows the eye wide open, with a white ring all round a warm brown iris and a thick dark rim.
- The shader draws the iris to 0.16 of the sphere angle, with a darker limbal ring and a pupil of 0.07.
- The lids cover less than before: upper 0.6 rad, lower 0.45 rad.

**Articulation:** the eyeball can aim. Lids are separate shells, still to be put on blink bones.

## Crown, temporal crest and horns

**References**
- Side crop: px 100–290, py 90–250.
- *How to Draw*: the horns sweep back, then curl up at the tips.

**Primary mass:** the cranium is a box behind the brow.
- Top y ≈ 1.89.
- Half-width 0.2 at the top and 0.24 low.
- Widened 1.3× (top) and 1.12× (low) on this pass, since the front view read as a horse's head.

**Structure underneath:** a temporal crest runs from the end of the brow back to the horn base. Ridge brush: (1.574, 1.793) → (1.501, 1.851).

**Horn**
- A ringed tube along a quadratic path: base (0.13, 1.857, 1.545) → mid (0.19, 1.99, 1.40) → tip (0.26, 2.09, 1.19).
- It sweeps back at about 45° in the side view and splays outward.
- Radius 0.036 → 0.024 → 0.004.
- A ring every 0.05.

**Note:** the second horn in the side view is the far-side horn. It is not a second pair.

**Articulation:** rigid, on `head`.

## Ear frill and ear opening

**References**
- Side crop: px 180–290, py 165–275.

**Primary mass**
- A cupped leaf about 0.15 long.
- Base at about (z 1.36–1.41, y 1.77–1.79).
- It points up and back.

**Look**
- The front edge rolls over like the rim of a horse's ear (`rolled_front_edge` 0.025).
- The inside is pale peach with 3 ribs.
- The rim is orange.

**Opening:** the ear hole is a dent at (1.420, 1.638). It sits below the frill, on the cheek.

**Articulation:** rigid for now. It needs its own bone for ear flicks.

## Cheek, jaw and mouth

**References**
- Side crop: px 40–260, py 330–430.

**Upper lip**
- The lower edge of the upper head drops from 1.38 at the prow to 1.28 at z 1.88.
- It then rises steeply to the mouth corner at about (1.60, 1.47).

**Lower jaw**
- The jaw is set back under the lip, a strong overbite. Its front is at z 1.885.
- The chin juts forward and down.
- Behind the mouth corner, the cream jowl rises to below the ear.
- Half-widths were widened 1.1× with the cranium.

**Structure underneath:** the masseter fills the cheek between the cheek ridge and the jowl.

**Drawn lines:** the mouth corner is a **crease**: (1.640, 1.410) → (1.575, 1.515).

**Articulation**
- `jaw` hinges at (0, 1.52, 1.47).
- The teeth ride on `head` and `jaw`.
- The tongue is on `tongue1`–`tongue3`.

## Known differences after this pass

- The cranium and brow still read rounder than the art's crisp planes. A `flatten` brush for the top plane is the next tool to add.
- The horns rise more steeply in the front view than in the *How to Draw* art. That art has them lower and curling up only at the tips.
- The zig-zag cheek crease under the eye is missing.
- The frill is still small next to the art.
- The upper head does not yet join the neck.
