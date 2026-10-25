# Clay's body: element sheets

The working notes behind `body_design.json`, following the `creature-sculpting` skill. The head
has its own sheets in `../head/head_sheets.md`.

**Coordinates:** reference pixels are on the 1400-px side sheet (Spirit978). Model units use `z = (700 - px) / 343` and `y = (830 - py) / 343`. x is Clay's left.

**Bind pose:** the side sheet's pose, so the side render can be laid directly against the sheet. Two exceptions:
- The tail's lower run, which the sheet draws below the feet (nearer the viewer), rests on the ground.
- That run curls toward the viewer (+x).

## Plan: pieces and order

| Element | Pieces | Status |
| --- | --- | --- |
| Neck, torso, tail | one continuous loft along a curved spine (the "trunk"), skinned to spine bones | first pass |
| Head join | the trunk runs on into the head's back; head bone parented to the last neck bone | first pass |
| Carapace (the dark back) | its own shell fitted over the trunk: transverse bands, and a rim of square marginal scutes with rolled edges | first pass |
| Neck scales, ventral bands, tail studs | sculpted rows and plates on the trunk | to do |
| Mane | spines along the neck and back, on spring bones | to do |
| Front legs and hands | shoulder sculpted into the trunk (dark patch), upper arm, forearm, compact hand: big hooked claws, high dewclaw | first pass |
| Hind legs and feet | thigh + shin loft, long digitigrade foot loft, four splayed toes, heel spur, studs on top | first pass |
| Wings | arm with square plates along the leading edge, five fingers, membrane with a scalloped trailing edge | first pass |

## Bone, muscle, skin (the body's construction)

The body is built from the inside out (`skin.py`, data in `body_design.json` "anatomy"):
- **Trunk:** the measured sections along the spine. The chest is a deep **keel**, widest up at the shoulders and narrowing toward the breastbone (box set, *How to Draw*, limited edition). The belly tucks up into a waist before the haunches, and the tail is taller than it is wide.
- **Skeleton:** the shoulder blade, humerus (with the point of the elbow), forearm bones and wrist, femur, tibia and heel. Front leg measured on the side sheet:
  - shoulder joint at px 425, py 495, under the dark patch, at the front of the upper arm;
  - shoulder blade running up and back to px 540, py 330;
  - elbow at px 625, py 605;
  - slim wrist at px 515, py 790.
- **Muscles:** ellipsoid bellies laid from origin to insertion, each with the reference it comes from:
  - shoulder cap (supraspinatus, infraspinatus, deltoid): the dark rounded shoulder patch;
  - triceps, biceps, pectoral (ties the arm to the breastbone), latissimus;
  - forearm extensors (front, orange) and flexors (back, cream);
  - gluteals, quadriceps, hamstrings and adductors: the haunch;
  - caudofemoralis: a reptile's great tail muscle, from the tail root to the thigh;
  - calf (cream) and shin front;
  - flat hand and long foot.
  The legs follow a great cat's: elbows tucked in, legs hanging close beside the keel. The feet follow birds and dinosaurs.
- **Chest (a lion's):** smooth, with no lumps. The trunk's surface runs as smooth curves through the measured stations (a spline, interpolated continuously along the spine), not straight segments, which creased it at every station. The pectoral is broad and flat, set back from the front of the chest, and an inner upper-arm mass (biceps, brachialis, the triceps' inner head) fills the inside of each shoulder where it merges into the chest (TDP limited-edition cover).
- **Skin:** one surface over all of it, a smooth union meshed with marching cubes. The shoulders grow out of the chest and back, and the haunches out of the hips and the tail root, with no seam. The dark back's plates are lifted onto the skin where the muscles swell it.

- **Tail:** a chain of 36 caudal vertebrae, like a lizard's, each turning a little in pitch and yaw from the last, with its top always up. It drops from the hips to the ground behind the hind legs, then snakes round sideways (to Clay's left, toward the viewer of the side sheet) and forward along the ground, outside the hind foot. The side sheet draws that lower run below the feet because it is nearer the viewer. The tightest bend is about 16 degrees per vertebra. *Earlier, wrong:* the side view's loop was built as a bend straight down and over, so the tail lay upside down.
- **Tail taper:** like a gecko's, the tail is fat at its root and tapers steadily all the way to a point. *Earlier, wrong:* following the sheet's depths kept it nearly the same thickness down its lower run, like an earthworm.
- **Spikes:** a mane of blades raked back along the neck, their tips on the sheet's outline (tallest, about 0.12, at mid-neck), falling to small spikes along the back; and leaf-shaped spikes down the middle of the tail, one per band.
- **Hips:** the section broadens over the hips, and the gluteals are one broad, flat pad from the spine to the hip joint, like a cat's croup. The haunch (one round thigh mass) grows out of the hip with no pit. The wing hides all of this on the sheet, so it mirrors the shoulder.
- **Shell:** the dark back is one smooth shell over the skin's whole dark region: the back, both shoulder caps, both hip caps (the dark edge dips over the hip as it does over the shoulder) and the top of the tail. A rolled rim runs continuously round its whole edge. The dark region covers whatever lies under it, muscle or trunk, on the body's upper side only. *Earlier, wrong:* separate band plates and rim scutes, and colour painted on from the side view; the plates flared off the muscles like fins.

**Earlier, wrong:** the legs were tubes stuck onto the outside of a barrel-shaped trunk, with a single bump for a shoulder and nothing for a haunch, so their tops looked chopped off.

## Trunk (neck, torso, tail)

**References**
- Side sheet: traced with `trunk_trace.py`; see the overlay `trunk_overlay.jpg`, not committed.
- Official front and three-quarter art for widths.

**Primary mass:** one continuous body, measured as depths from a traced spine to the dorsal and ventral outlines, perpendicular to the spine.
- **Neck:** short and thick, about 0.45–0.55 deep. It runs from behind the skull down and back into the chest.
- **Torso:** a deep barrel, about 0.9 from back to belly.
- **Tail:** thick (0.25–0.38) nearly to its tip. It curls down at the hips, then runs forward along the ground to its tip.

**Widths:** not in the side sheet. Taken as a factor of the mean depth: 0.85 at the neck, 1.0 at the chest (a broad barrel), 0.85 on the tail. They still need checking against the front art.

**Zones.** On the neck and torso the edges are measured side-view lines, not fractions of the side:
- **Dark edge:** the line of small square plates. From behind the ear it runs back, then straight *down* the side of the neck into the shoulder. It goes round the bottom of the dark shoulder patch, then back along the wing arm (`dark_edge_px`).
- **Cream edge:** bounds the wide throat band, down the front of the neck into the chest. Behind the forelegs the cream rises to meet the dark edge, with no orange band (`cream_edge_px`).
- **Tail:** a dark top and a cream underside meeting at mid-side, by fraction.

A level fraction was wrong: it kept the dark edge high along the neck instead of sweeping down to the shoulder.

**Pattern rhythms,** measured with scanlines across the ink lines on the sheet:
- Ventral bands: ~0.09–0.10 apart on the belly, throat and tail underside.
- Back plates: ~0.08–0.12 along the back.
- Limb plates: ~0.10 along the limb by ~0.07–0.075 across, in columns down the limb, organically warped. Not staggered, never bricks.

Patterns are laid out in model units along and around each part, so they stay the same size on thick and thin parts. Pattern seams sit on hidden sides.

**Rig:** hips → spine → chest → neck1–4 → head; tail1–12 from the hips, getting shorter toward the tip.

**Known differences**
- The neck's orange side needs its rows of rounded scales, and the throat and belly bands should be real stepped plates.
- The toes are separate tubes pushed into the hands and feet. They should be sculpted into them, with only the claws separate.
- The hind thigh pokes up the side of the torso; in the sheet it stays below the dark edge.
- The sheet's tail tip hooks up; mine ends straight.
- Widths are estimates.
- No plates, scales, bands, studs or mane yet: the surface only has the zone colours.
- The orange of the neck reaches too far back.

## Carapace (the dark back)

**References:** the side sheet (neck and torso line maps) and the official art, where the dark back always ends in a rim of small square plates.

**What it is:** not paint. Like the head's roof, the dark back is a shell fitted over the trunk and standing proud of it: a turtle-shell carapace.
- **Bands:** transverse bands, about 0.09–0.12 apart on the sheet (0.105 in the model; ×0.8 on the tail), wrap over the top and down each side to the rim.
- **Rim:** a row of small square marginal scutes (~0.06 tall, joints every ~0.055) along the measured dark edge. They are thicker than the bands, with outer edges rolled outward like a turtle shell's margin.

**How it follows the body:** the rim follows the dark edge line, so it sweeps down the side of the neck into the shoulder and runs back along the wing arm and down the tail.

**Build:** the plates are laid on the trunk surface (`trunk_surface(s, θ)`), between the dorsal line and the edge angle found from the zone lines. Each is bevelled, thicker toward its back edge, and overlaps the next one back. They are skinned to the spine bones.

**Known differences**
- The bands on the neck converge on the inside of the curve; the sheet's neck plates look broader.
- The mane spikes along the top are not built yet.

## Haunch (How to Draw)

**What it is:** the thigh is one long oval mass that blends into the flank. The calf below it is orange, the same colour as the thigh; it is not a cream peg.
- Thigh muscle radii are [0.14, 0.24] with blend k 0.14.
- The calf zone is 0.5.

**Shell:** any skin area under the island size (200 verts) that the dark zone surrounds is filled in, so the shell has no pinholes.

## Tail spikes

**From the side sheet:** the tail's spikes are thorns lying flat along its top. Each one's base is on the surface, its outer edge is convex, and its point faces back. They are about 2.4 times as long as they are tall. They are not raised blades.

**Build:** each is the same leaf as a mane blade, but one-sided: the leaf's lower half sinks into the shell, and its axis lies 6° off the surface (the `thorn` shape in the tail row).

## Wings

**What it is:** a bat's arm. Every official image draws it so: the limited-edition and full renders spread the wings, and *How to Draw* raises one. It is built bone first, then muscle, then membrane.
- **Upper arm:** short and heavily muscled. A fleshy belly (biceps and triceps) over the humerus swells out of a round mound on the shoulder: the deltoid and the wing's pectoral insertion, the side sheet's scaly mound (px 490–560, py 340–400). The mound's front end dives into the shoulder, so the arm grows out of the body.
- **Forearm:** long. It is thick and fleshy for its first third below the elbow (the flexors and extensors), then a bony shaft to a knobby wrist (the carpals). The elbow's point (the olecranon) stands out behind.
- **Thumb:** a short digit on the wrist's leading side, ending in a hooked claw.
- **Fingers:** four long ones from the wrist. Each is a metacarpal to a knuckle partway out (0.45), then a phalanx bent a little back, ending in a small hooked claw past the membrane.
- **Membrane:** peach, between the forearm and the fingers, scalloped between the tips.

**Pose:** the side sheet's folded wing.
- The arm runs from the shoulder back along the flank to the elbow (px 525,385 → 785,425). It is a broad band 0.19 tall.
- The forearm drops straight down to a low wrist (765,760).
- The fingers fan up and back to their tips, nearly parallel, with narrow strips of membrane between them.
- Out from the body, the arm lies on the flank and the fan stands just outside the hind thigh (0.57).

**Build:**
- The arm is its own small skin (`skin.py`, with no trunk): bone capsules and muscle bellies joined with a smooth minimum, meshed at 0.008, and weighted by nearest piece to `wing_humerus` and `wing_forearm`.
- The fingers and thumb are tubes (with bones `wing_fingerN`, `wing_fingerNb` and `wing_thumb`).
- Each membrane panel is a grid between two spars. It sags back between the tips and billows slightly. Its weights follow the bone under each spar.
- **Surface:** dark brown pebble scales, with a row of square plates along the outer edge (the side sheet).

**To do:** the membrane panel from the last finger to the flank (hidden when folded). A raised pose like *How to Draw*'s.

## Hands and feet

**References:** How to Draw, the SE poster, the GN cover and render, the limited edition and the side sheet.
- **One form:** the foot is one mass, not separate toes. The fingers are thick and close together, like a lizard's or a raptor's. They fuse at the palm and part by grooves toward the tips.
- **Fingers:** three segments each, rising to a knuckle bump and arching down to a rounded tip with a pad under it.
- **Claws:** thick, dark sickles. Each springs from the top of its toe's tip, runs forward and hooks down to the ground.
- **Thumb:** the front hand has an opposable thumb on its inner side, about a third of the way from the wrist (How to Draw's hooked claw high on the inner foot; the poster's thumb branching off the inner hand). Standing, it points down and in, its claw hooked toward the fingers.

**Build:**
- Each toe, finger and thumb is part of the skin field (`toe_pieces`, `digit_specs`): a bone per segment and a pad under the tip. The first segment fuses into the hand or foot mass (blend 0.03); the rest part cleanly (0.012).
- The claws are separate dark pieces (keratin). `claw_tube` now hooks toward `down`; it used to hook up.
- The floating studs on the hind feet are gone.

**To do:** the dark plates across the top of each finger segment (SE poster). Cream soles and palm.
