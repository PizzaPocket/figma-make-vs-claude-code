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

## Underside

**Seen from below:** there were pits where the trunk, the thigh and the arm met. A real quadruped's muscles fill those places, so the fix is the muscles, not smoothing:
- **Groin** (0.06 deep): the adductors now run from the underside of the pelvis (under the belly's midline) to the inner knee, as a broad fan.
- **In front of the thigh** (0.04): a flank fold from the belly to the front of the knee, as on a cat.
- **Behind the thigh, beside the tail's root** (0.03): the semitendinosus, the inner hamstring, from the ischium to the back of the knee.
- **Armpit** (0.03): the latissimus and the triceps' long head, from the chest wall behind the elbow to the back of the upper arm.

The four use a wider blend (0.18), so they melt into the belly rather than sitting on it. The remaining crease, under the tail's root where the two inner hamstrings meet, is natural.

**How I measured:** marching cubes at 0.02, then each surface point's depth below a 60-step Laplacian smoothing of the mesh. Clusters deeper than 0.025 are pits.

## Lower legs (forearm, wrist, shin, ankle)

**Foreleg:**
- **On the side sheet:** the forearm is a column about 0.2 wide in profile, carried right down to a wrist that does not narrow. Below it a short, broad hand lies flat, with the toes in front.
- **Before the fix:** the forearm muscles were ellipsoids ending in points above the wrist, leaving a thin, boneless-looking wrist.
- **The fix:** the muscles now run down to the wrist, and the radius and ulna thicken toward it (0.065 → 0.075).

**Hind leg:**
- **References:** the side sheet's wing hides it. The hanging hind feet on the limited edition, the SE poster and the Umber render (house style) show a long metatarsus with the heel raised.
- **Before the fix:** the heel sat on the ground 0.48 behind the toes, like a crouching frog.
- **The fix:** the leg is now digitigrade, like a cat's or a dog's. The knee is forward at mid-height (0.46, z −0.46). The hock (heel) is raised behind it to about a quarter of the hip's height (0.22, z −0.86), with the spur on its back. The metatarsus runs down and forward to the toes (z −0.6). The calf and shin muscles are re-hung on the new joints and thickened.

**Not used:** the Japanese design sheet, whose style differs from the rest of the official art.

## Wings: one rig, folded to spread

**References:** the covers seen from below: The Dragonet Prophecy (US and the full render), the Hybrid Prince cover (Umber, a MudWing, in house style), the limited edition and the SE poster.
- **Arm:** spread, the humerus runs out, up and a little back from the shoulder. The forearm runs out and forward to the wrist, forming the leading edge.
- **Fingers:** the longest finger carries the leading edge on to the wing's tip. On the folded sheet it is the outermost one, reaching highest. The shorter fingers fan back, the shortest pointing nearly straight back.
- **Elbow finger:** a short plated finger springs from the elbow, up and back, to a small claw at the membrane's edge. On the side sheet it runs from px 785,425 to 912,347. On the TDP cover render it rises from the arm beside the body.
- **Membrane:** it runs from the elbow finger across to the fingers and between them, scalloped between the tips. It also runs from the elbow finger back along the flank to the hip (the Umber render). Folded, that flank piece gathers in a few soft folds along his side.
- **Light:** the membrane is thin. Seen from below against the sky it glows peach, so the shader adds the light coming through it.

**Build:** one rig with real joints, so the wing moves through any pose.
- The wing rests spread. Its bones pivot at the shoulder, the elbow, the elbow finger's root, the wrist, each knuckle and the thumb.
- The side sheet's folded wing is a pose of those bones: per bone, a turn from rest, computed so the joints land where the sheet measures them. It is exported as the animation `wings_fold` (rest at 0, folded at its end).
- Folded, the flank membrane's folds are the `wingfold` blend shape, set together with the fold.
- The viewer's pose takes `wings` (0 spread, 1 folded, the default) and blends each bone's rotation between them, so every in-between is a real pose.
- The anatomy is still measured folded (`wing.joints`, `wing.fingers`, `wing.anatomy`); `wing.spread` gives the rest pose's directions, and the bones keep their lengths.
- The arm's muscles are carried to rest with their bone: those on the humerus turn about the shoulder, those on the forearm about the elbow.

**To do:** the elbow pinches a little when folded (the bones' weights blend there).

## Review round: front half, wing root, spikes, colours

**Front half, against the side sheet at its angle (the sheet is turned about 25° toward us):**
- **Chest:** one rounded mass. The keel over the forelegs is gentle (0.12–0.15), and one broad pectoral runs from the breastbone. There used to be a groove down the chest between the shoulder balls.
- **Upper arm:** smoother, with a smaller triceps ball and wider blends.
- **Throat:** the collar behind the jaw was a bump in the traced ventral depth (0.232 at s 0.23). It's smoothed.

**Inner thighs:** slimmer, as on the Hybrid Prince cover. The thigh is a distinct oval meeting a slim belly in a clean crease.

**Wing:**
- **Root:** directly behind the shoulder armor, where the carapace gives onto the cream.
- **Carapace edge:** between the shoulder armor and the hip armor, the carapace's lower edge is one smooth arc, with cream below. The membrane meets the body just under it.
- **Flank membrane:** laid out from the wing's root, between the arm (the humerus, then the elbow finger) and the body. It meets the whole upper arm with no gap.
- **Elbow finger:** about 0.88 long, twice its apparent length on the sheet (foreshortened there; the spread covers show it long). It has a knuckle and a hooked claw.
- **Fingers:** a metacarpal and two phalanges each, with knuckle bulges and hooked claws.
- **Arm:** heavier, with the upper arm as thick as the leg and the forearm fleshy past halfway.
- **Surface:** orange skin with dark plates in rows over the top. "Top" is measured with the wing spread, so it is the same on both wings; before, the plates were mirrored, under one arm and on top of the other.

**Spikes:** one continuous run. Mane blades go to the withers, then thorns lie back over the back, hips and tail. All have body (about 0.03 thick), and the tail's thorns are 0.065 tall at its root.

**Legs:** coloured by which way the skin faces. They are orange on the outside and front, cream on the inside, back and underside (the side sheet's forelegs).

## Review round: clipping, shoulders, wing armor

- **Folded wing, clear of the body:** the fan stands outside the haunch (wrist x 0.72, tips 0.80–0.86; the thigh reaches 0.57–0.6). The elbow finger lies inside the fingers (x 0.5), back along the side. Every finger, the forearm, the elbow finger and the membrane between them clear the body by at least 0.088 (`clipcheck`).
- **Rolled fold:** the fold also rolls the arm and the fingers about their own axes. The arm's armor faces outward and its orange flesh inward (all the references). The membrane billows outward, not into the leg.
- **Flank membrane, folded:** it spans straight from the folded arm to the body, in soft outward folds. The `wingfold` shape puts each point exactly where the fold's bones carry it there. Its body edge holds only a strip next to the body; the rest rides the arm. Before, it stood up as a flap over the back.
- **Shoulders:** the foreleg's shoulder joint is 0.06 higher, as read at the sheet's own angle. The shoulder armor reaches less far down, and its hind point rises.
- **Wing root:** at the shoulder armor's hind point, lower and nearer the foreleg's shoulder, so the wing branches off the same shoulder.
- **Carapace edge:** one arc from the shoulder armor to the hip armor, with cream right below. The membrane meets the body along it, and the hip armor's front starts where it ends.
- **Wing arm armor:** a distinct shell built by the back's carapace builder (`wing.armor`), with banded plates and a rolled rim over the arm's top. The arm under it is orange skin. The fingers are plain orange.

## Review round: wing shoulder, membrane line, chest cream, finger bones

- **Wing shoulder:** a muscle mass in the wing arm's own mesh, from the arm's socket forward over the top of the foreleg's shoulder (every reference). It lies on top of the shoulder armor, about 0.12 proud, armored on top and orange beneath. Weighted mostly to the chest, it stays on the shoulder as the wing moves. The socket is a separate small piece under it.
- **Membrane line:** sampled every 12 px along the carapace's lower edge (`zones.dark_edge_px`) between the wing's root and the hip armor. Each sample sits on the body's surface just under the rim, so the membrane follows the arch exactly.
- **Chest cream:** the throat band broadens over the chest to the front of the foreleg shoulders (about 0.33–0.37 either side of the midline) and merges with the belly.
- **Finger bones:** three per finger (metacarpal, two phalanges), meeting at the knuckles. The skin, claw and membrane follow the bone under each segment. The fold turns each finger's bones together, so the knuckles stay coherent from spread to folded.

## Head and neck junction

**On the side sheet:** the neck's dark top runs up under the back of the skull, and the orange side of the neck wraps up under the ear and round behind the jaw.
- **Before:** the head read as a separate piece plugged onto the neck. The head's back ends at half-width 0.21–0.23 and its jaw corners stood out of a neck only 0.195 wide.

**The fix:**
- **Width:** the neck at the head is as wide as the skull's back (width factor 1.02 at s 0, easing back by s 0.5).
- **New body pieces, carried by the head bone,** so the neck blends into them and stays closed as the head moves:
  - the jaw muscle (masseter and temporalis), from under the ear frill to the jaw's corner;
  - the ear frill's fleshy base, under the horn;
  - the occiput under the roof's last band.
- **Articulation:** the viewer's pose takes `head: [pitch, yaw]`, spread evenly down the four neck bones and the head. Up, down, left and right all keep the junction closed.

## Head and neck weld: one skin from the cheek back

**User's note:** the head and neck still read as two pieces, in shape and in surface. Also: sculpt the ear and around it; should the lower jaw join the throat's skin; check the three-quarter view against the side sheet.

**Correction to the round above:** the jaw muscle, ear base and occiput pieces made a hood. The neck's skin wrapped over the cheek's back edge and stood proud of it, and the occiput was a dark dome that buried the ear. All three are removed.

**What the references show:**
- **Side sheet:** the face's fine pebbles end at the heavy S line behind the cheek, which runs from under the ear down to the ear opening and on along the jaw's back edge. The neck's big scales start there. The cream jaw runs straight on into the cream throat strip.
- **Dragonet Prophecy cover (three-quarter):** the same. The cheek flows into the neck with no step, and the jaw's cream flows into the throat.

**Yes, the jaw joins the throat.** The jaw is a defined form (the drawn line round its back edge), but the throat's skin is continuous with its underside, and opening the mouth stretches it.

**Build (`anatomy.head_weld`):**
- **Head in the skin's field:** the face and jaw join the body's field as pieces built from their own cross-sections (`skin.SectionPiece`, the head's contours closed across the mouth). They match the head's meshes to within 0.003.
- **Cheek line (`cheek_line`, traced):** behind it the face and jaw meshes are trimmed away (every face touching the region behind), and the body's skin is the head's surface there, with the neck's fillet swelling out of it.
- **In front of the line:** the skin is kept inside the face and jaw (`skin.CLIP`), hidden under their meshes.
- **Behind it:** the skin is let out gradually (`rise`, with a smooth maximum), so nothing kinks.
- **Weights:** skin at and in front of the line moves with the head and jaw, and hands over to the neck behind it. The trimmed edges never part from the skin, through head turns and jaw opening.
- **Ear opening:** painted on the skin too, since it sits on the line.

**Failed on the way, for the record:**
- **A distance field from the meshes:** nearest-face normals gave the wrong inside/outside, which made floating blobs and a flat sheet. The cross-sections give an exact inside test.
- **Skin standing out over the face behind the line:** the surfaces crossed at a shallow angle, a sawtooth.
- **A hard clip:** a kink the marching cubes stepped on.
- **Snapping the trimmed edge onto the line:** sliver faces with bad normals, a rib in the light.
- **A crease along the line:** you could see into the open jaw through it.

**Ear:**
- **Tip:** re-measured on a gridded crop (px 258, py 190). It was 0.05 too far back and 0.04 too high, standing up behind the horn like a spike.
- **Seating:** the neck shell's rim stands at x 0.26–0.27 under the ear's base, which buried it. It now sits outside the rim (base x 0.285), a pale leaf at the back corner of the head, as on the cover.

**Still to do:**
- a faint shading line along the cheek line in plain clay;
- a thin slit at the mouth's back corner;
- the neck's scales are cells, where the art draws large overlapping shingles;
- the ear's shape itself (cup, rolled rim) is unchanged from the head pass.

## Neck and flank scales: shingles

**Side sheet:** the orange of the neck and flank is covered in large overlapping scales, like roof shingles, about 0.065 long and 0.06 across. Their free edges are arcs facing back toward the body, and the scale nearer the head lies on top. Before, the model had irregular polygon cells of about the right size and the wrong shape.

**Built (viewer shader, part 20):**
- **Layout:** the scales are discs in offset rows, along the spine (s) and round the trunk. The distance round the trunk (angle from the top of the spine times the section's mean radius) is carried in `_PART`'s fraction (20 + around / 4), since the other vertex attributes are full.
- **Overlap:** at each point the scale nearest the head among those covering it is on top. Its free edge is drawn as the line, and each scale is lit a little toward its middle.
- **Seams:** the pattern's seams fall at the top of the spine and under the belly, inside the dark and cream zones.
- **Behind the cheek line:** the skin there takes the neck's own colours (orange shingles, the cream throat strip running up to the jaw), not the face's and jaw's. Before, it showed a pale band without scales. The pattern's along-the-spine coordinate is continuous now (nearest station plus the offset along the spine), and runs on past the neck's first station, so the shingles reach the ear opening instead of stopping short of the head.

## Neck bending: bands as the head turned

**Symptom:** light bands with stair-stepped edges across the neck whenever the head turned.

**Causes:** the weights jumped across single edges of the mesh.
1. **Spine weights at the joints:** the bones on either side of a joint each gave themselves 0.75 there, so the weights flipped from 0.75/0.25 to 0.25/0.75 across one edge, at every spine joint. Invisible at rest, they crease as soon as the spine bends. Each side now gives exactly half and half at the joint.
2. **Spine position:** on the inside of the neck's bend, the nearest spine station flips between stations far apart from one vertex to the next. The spine position the weights are read at is now smoothed over the skin (`anatomy.rig_smooth_iters`).
3. **Neck blends:** the neck's joints blended over ±0.05 of bones 0.16 long, so the neck bent in kinks. They now blend over half a bone (`trunk.bones.neck_blend`), so the neck bends in one curve.

**Check:** the largest weight difference across any edge on the neck is now under 0.2. Head up, down, left and right render without bands.

## Leg plates

**Problem:** the shingle layout (last round) uses the distance round the trunk, which has no meaning on a leg. It smeared into long vertical stripes on the legs and feet.

**Built:** where the trunk's share of the skin is low (the limbs), the skin draws plates in brick-offset rows, about 0.07 by 0.075, organically warped. This matches How to Draw and the side sheet's legs.
- **Legs:** the rows run across the leg (by height).
- **Feet and toes:** they lie along the ground, so the rows run across the toes (by z).
- **Between the two:** the finished patterns are blended, not their coordinates, which made moiré at the wrists and ankles.
- **Soles:** the undersides of the feet stay cream (`limb_zone`).

## Checked: the folded fan's width (no change)
In a true side overlay the model's folded fan is narrow (about 9° between the first and last finger), while the side sheet's looks broad. Zoomed in, the sheet draws two layers:
- the near wing's studded fingers, ending at claws at (1055, 255), (1165, 140), (1260, 55) and (1365, 20), which are the model's finger tips exactly;
- the far wing's plain fingers behind them, offset up and toward the head by the sheet's slight elevation, ending at (915, 195), (1030, 95), (1140, 45) and (1265, 20).

The broad fan is the two wings overlapping. Evaluated at the fold animation's end, the built model's claws land on the near wing's tips.
