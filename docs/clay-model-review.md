# Clay: model review and build plan

A fresh-eyes review of the current prototype (`prototypes/clay/`, commit `fcb61fa`) from
the point of view of someone who knows Clay, a summary of what the official art
consistently shows, and a plan for how the model should be broken into parts.

Sources compared:
- **Official art:**
  - Joy Ang's covers: *The Dragonet Prophecy*, full wrap and limited edition.
  - Brianna C. Walsh's *The Official How to Draw*: the best view of his front three-quarters.
  - Mike Holmes' graphic novel.
  - The special-edition poster.
- **Fan art:** Spirit978's side-view reference sheet, the source of the prototype's measurements.

## 1. What a fan would say is broken

Most glaring first.

1. **The head isn't Clay's head.**
   - There's no visible eye. Clay's wide, warm brown eyes are the first thing anyone looks for.
   - It's a lumpy box with no brow, cheek or jaw structure. In every piece of official art the head is built from clear planes:
     - a broad, flat-topped muzzle with a squared-off front (MudWings have flat snouts);
     - a heavy brow shelf over the eye;
     - a cheek plate;
     - a deep lower jaw.
   - There is no mouth: no opening, teeth or tongue. He can't roar, eat or breathe fire.
   - The horns are plain cones. In the art they are slim, ridged, and sweep back from behind the brow.
   - The ear frill is a flat triangle. In the art it is a rounded, ribbed, pale fin.
2. **The colour zones are wrong on the body.** Behind the forelegs, the cream underbelly comes all the way up the side to meet the brown back. There is no orange band along the flank. Orange belongs to:
   - the sides of the neck;
   - the cheeks;
   - the shoulders and upper forelegs;
   - the thighs and the legs (organic, roughly rectangular plates, not a grid).

   The model paints an orange stripe the length of the torso.
3. **The back and tail look like brick walls.** The dark back is covered in long, overlapping, curved plates (like shingles or feathers) with clear outlines, not staggered rectangles. The tail top is the same dark plating, with a row of leaf-shaped studs down the centre line. The cream underside of the tail is a grid of 2–3 columns of plates, which the model roughly has.
4. **Proportions read as a different, leaner dragon.** Clay is described as large, burly and stocky, with a thick neck and enormous feet, and the art agrees. The model is too long and low:
   - The neck is too long and thin.
   - The chest isn't deep enough.
   - The forelegs are too short.
   - The hands and feet are too small.
   - The claws are tiny nubs instead of big, dark, hooked claws.
   - The front hands and hind feet are built the same way, but in the art they differ (see section 2).
5. **The wings are off.**
   - Finger bones are thick tubes ending in balls; in the art they are slim, jointed bones.
   - The row of square plates along the wing arm, present in every official image, doesn't show.
   - The membrane colour varies across the art (pale cream to warm peach). The model is closer to pale; pick one.
6. **The mane looks like bristles.** In the art it is a fringe of thin dark spines lying back along the neck and shoulders. It is subtle on the official covers and stronger on the fan sheet.
7. **The tail isn't in a believable rest pose.** It should rest curled on the ground.
8. **The surface is only shaded.** The fine scales exist only in the shader, and the big plates are bumps in a single blobby skin. Nothing has the crisp, layered armour look of the art.

## 2. What the official art consistently shows

These hold across the covers, the How to Draw guide and the graphic novel, so they can be
written down as data:

- **Silhouette:** heavy, front-loaded body with a deep chest and a sloping back. The neck is thick and fairly short. The tail is long and thick at the base. Legs are pillar-like with big hands and feet.
- **Ventral shield:** one continuous cream band of wide horizontal plates.
  - It runs from the chin down the throat, across the chest, along the belly and under the tail.
  - On the chest it is wide and rises up the sides behind the forelegs to meet the dark back.
  - Some art shows a central seam on the chest plates.
- **Dark dorsal armour:** long overlapping curved plates from the back of the skull, over the back and down the tail. It is bordered by a line of small square plates where it meets the lighter skin.
- **Orange regions:** neck sides (rows of rounded scales), cheeks (small pebble scales), shoulders and limbs. On the limbs the plates are organic and roughly rectangular, not a grid: they vary in size, curve with the muscles and taper toward the joints. The backs of the forelegs are cream.
- **Head:** the dark plate runs from the nose over the brow to the horns, in segments. Then the cheek plate, the cream lower jaw, the brow shelf over the eye and the pale ribbed ear frill.
- **Wings:**
  - The wing arm carries a row of square plates along its leading edge.
  - Five slim fingers, each with a claw at the tip.
  - A thumb claw at the wrist, and the wrist rests on the ground when folded.
  - The membrane has a scalloped trailing edge.
- **Front hands and hind feet are built differently:**
  - **Front hand:** compact and broad, with the wrist close to the ground at the end of a column-like forearm. Three to four short, knuckly toes each end in a very large, thick claw that hooks down. A dewclaw sits high on the back of the wrist, pointing backward.
  - **Hind foot:** long and digitigrade. The foot runs nearly flat along the ground back to a slightly raised heel, which has a spur claw pointing backward. The toes are longer, slimmer and splayed (four in the How to Draw art), with claws. A row of dark square studs runs along the top of the foot, and the back of the shin and heel is cream.

The covers differ on hue (golden orange to red-orange) and membrane colour. The layout of zones and plates is consistent.

## 3. What should be one mesh, and what should be separate

Two kinds of "separate" are worth telling apart:

- **Regions of the same skinned mesh** that are weighted rigidly to one bone, welded so there is never a crack.
- **Separate objects** parented to a bone or skinned on their own, which can overlap and slide over the skin.

Real game creatures use both.

### One continuous skinned mesh: the "under-skin"

The neck, torso, limbs, tail, wing arms, lower jaw and throat. These stretch and bend together, so they must be one welded surface with clean edge loops at every joint. Fine scales live here as normal-map detail: neck rows, cheek pebbles, the limb plates.

**Lower jaw and throat stay part of this skin.** When the jaw opens, the throat skin under it has to stretch, as you described.

### Upper head: its own rigid piece

The upper head (muzzle, brow, cranium, back to the ear frill), with the horns attached, moves as one rigid unit on the head bone. There is a natural seam for it in the art: the edge of the dark head plate and the ear frill. Two ways to build it:
- as a rigid region of the main mesh, welded along that seam (safest: no gaps);
- as its own object whose back edge tucks under the ear frill and the first neck plates (simplest to model).

The lower jaw hinges below it at the jaw joint. The mouth interior is its own small mesh: gums, palate and inside of the cheeks.

### Separate rigid objects, each on its own bone

| Part | Parented to | Why separate |
| --- | --- | --- |
| Horns | head | rigid, own ridged geometry |
| Eyes | head (a bone each, for aim) | spheres that rotate inside lids |
| Eyelids | head (bones or shape keys) | blinking |
| Teeth, upper / lower | head / jaw | rigid, visible when roaring or breathing fire |
| Tongue | 3–4 bone chain | articulates |
| Ear frills | a small bone each | flick and fold; thin ribbed fin with thickness |
| Claws (hands, feet, wing tips, thumbs) | each toe's last bone | rigid, crisp, glossy |
| Tail studs | the tail bone under each | rigid plates that ride the tail as it bends |

### Overlapping armour plates as their own geometry

Where the art draws distinct plates, building them as real overlapping solids, rather than painting them on the skin, keeps them crisp and lets them slide instead of stretch when the body bends, like an armadillo. Each plate is a small solid with thickness and a bevel, placed along the body by rule, so it can be calculated from the data:

| Plates | Rule | Bound to |
| --- | --- | --- |
| Dorsal plates | rows of long curved shingles along the back and down the tail top, overlapping toward the tail | 1–2 spine or tail bones each |
| Border squares | a line of small squares along the edge of the dark armour | the nearest spine or neck bone |
| Ventral bands | wide horizontal bands from chin to tail tip, overlapping toward the tail like a snake's belly scales; chest bands can split at a central seam | the spine, neck or tail bone at their position |
| Head plates | segments of the dark plate over the muzzle and brow | the head (rigid) |
| Wing-arm plates | squares along the leading edge of the upper arm and forearm | the wing bone under them |
| Finger studs | small squares along each finger | each finger segment |

### Wing membranes: their own skinned meshes

The membranes are thin, double-sided sheets with a little thickness, skinned to the finger bones and to the body and hind leg along their roots. Optional extra bones (or cloth simulation) let them billow.

### Mane

Cards or thin spines in rows, bound to the neck and spine bones. Spring bones (Godot 4's spring-bone simulation) give them secondary motion.

## 4. Rig: what has to articulate

| Area | Bones / controls | Used for |
| --- | --- | --- |
| Spine | hips, 3 spine, chest | walking, breathing |
| Neck | 4–5 bones | looking, roaring |
| Head | head bone, jaw hinge, tongue chain, eye aim ×2, upper and lower eyelids ×2, ear frills ×2 | talking, roaring, fire breath, blinking, ear flicks |
| Tail | 10–12 bones with spring bones for follow-through | resting curl, balance, swim |
| Each leg | thigh or upper arm, shin or forearm, foot or hand, toe bones (3 + dewclaw, 2 joints each) | IK foot placement |
| Each wing | humerus, forearm, wrist, 5 fingers × 3 segments, thumb, optional membrane helpers | fold, spread, flap, glide |
| Chest | breathing bone or shape key | idle |

**Motion set for the game:** idle (breathing, look-around, tail sway), walk, run, swim, take-off, flap, glide, land, roar, fire breath, bite/claw attack, hit and death, and blink and talk on the face layer.

## 5. What this means for the build

The prototype's main technique doesn't fit this plan:

- **The current approach:** one melted surface from a distance field, decimated, with detail in a shader.
- **What it can't do:** produce welded clean loops, rigid head regions, separate overlapping plates or a mouth.

The data approach still applies, but each layer gets built differently:

1. **Under-skin:** a clean quad mesh built from the measured cross-sections (rings along the body, limbs and wing arms joined with planned edge flow), so it has UVs and proper joint loops by construction.
2. **Rigid head and jaw:** the upper head and the lower jaw as shaped solids, plus the mouth interior and teeth.
3. **Plates:** generated as solids from the rules in section 3, each with its bone.
4. **Attachments:** eyes, eyelids, horns, ear frills, claws, studs and mane as separate pieces on their bones.
5. **Membranes:** thin solids on the finger bones.
6. **Textures:** baked from the zone rules into UV textures, so Godot can use the model without a custom shader.

An artist pass (sculpting the head and the large forms against the official art) would still be the fastest way to get the face right. The plate system, attachments and rig in this plan can be built from data around that sculpt.
