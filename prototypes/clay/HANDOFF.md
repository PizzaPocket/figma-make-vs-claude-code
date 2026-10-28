# Clay model: handoff

## Follow-up: cheek fullness and folded shell inversion

User rejected puffy cheeks, shoulder roll, outward orange wrist, palm-face claw and nearly coincident resting fingers in `aef4ee2`. Corrective source now adds planar cheek walls; explicit outward arm dorsal frames; humerus-based shoulder material transport; forearm-based palm tissue; a distal-knuckle claw; and a roughly 41-degree resting fan. See the new sections in the element sheets and `wing_surface_review`. Earlier “candidate” descriptions are historical, not acceptance. Keep current scale sizing. Do not equate fan-order/weight checks with visual reference agreement.

## Latest review candidate, 2026-10-28

This is a new review candidate, not user approval. Measurements use official How to Draw, limited-edition and flight drawings; ref1400 is excluded from head proportions because it is a three-quarter view. An anterior-only map shortens the actual down/forward head axis, keeping the rear skull attachment stable. All head parts, keys and bones share it; body oral tissue receives it once.

The external upper lip has its own spline, separate from the structural bite bed: shallow front arc, anterior side lobe, rising flatter rear line. Cheek inflation is reduced. The lower chin has a wider faceted front and a backward-sloping underside. A cream closing lip seals the front without pulling the entire mouth floor upward. Repeated oral-host fitting now uses stored rest shares instead of compounding weights.

Review: `lip_profile_review`; full model renders include actual surface shaders and a plain-clay view. The previous narrow chin/red front gap was rejected during this pass. The final front seal is closed. The overall likeness, nose and lip character remain subject to visual review; projected drawing measurements are not an orthographic reconstruction. The user's current orange scale sizing is approved and unchanged.

The prior helper-driven shoulder was rejected by the user: a stretched, twisted strap is not acceptance. `wing_rig.py` replaces it with humerus/forearm frames, a shared wrist/palm, a compact shoulder field and pose-local soft-tissue corrections sampled across the fold. Arm skin and armor follow the same moving anatomy.

Four segmented digits retract toward the body while preserving fan order and segment lengths. The elbow accessory points more neutrally/forward and telescopes to half length when folded, explicitly authorized by the user; its claw has separate rigid attachment. The wrist claw is attached dorsally to the forearm's ending knuckle, independent of finger motion. Short embedded branches merge the digit roots into the palm. Membrane boundaries, scallops, sag and pleats follow the new posed skeleton.

The animation exports rotation, translation and scale; the viewer resets bind transforms and drives eight corrective shapes. Validation covers 17 fold samples, increasing fan angles, rigid finger-segment lengths and accessory scale 1→0.5. Exported weights are finite, nonnegative and normalized. These checks support review but do not prove a reference match. Review set: `canonical_wing_review` with open/intermediate/closed arm, wrist and reference views.


State at the end of the session on branch `wings-of-fire-game`. Read with `CHECKLIST.md` (open fixes), `head/head_sheets.md` and `body/body_sheets.md` (what each part is and why), and the skill `.claude/skills/creature-sculpting/SKILL.md` (how we work).

## Latest user review: outstanding anatomy and surface issues

The user is listing additional known problems, not asking for all of them to be
changed in one pass. They are recorded as open items in `CHECKLIST.md`:

- Ear bases remain separated from the face; the ears must grow out of the cheek.
- A patchy dark-brown gap breaks the dorsal head–neck transition.
- An unidentified internal artifact clips into the back of the throat when the
  jaw opens. Diagnose it before naming its cause. The mouth needs a coherent
  interior designed for speech and fire-breathing poses.
- Teeth still read as jagged shards; the user suspects insufficient density.
  Reassess solid tooth anatomy, count and spacing against the art. Upper teeth
  must root inside the upper gums/jaw and normally sit behind the upper lip,
  rather than appearing attached along its edge. The old completed teeth item
  is reopened. Treat mouth lining, gums, dentition and jaw movement together.
- The wing-arm shoulder appears disconnected from the rest of the arm.
- Wing fingers should move toward the carapace's surface style rather than the
  present orange treatment.

The user has explicitly rejected the nose in `ccd16b4`: it is still too far
forward on the shield, the front sides should angle inward, and the nostrils'
placement and orientation still need correction. The detailed nose checklist
supersedes the older placement and nostril directions. Measure these features
from the reference images before changing parameters again. The user also
caught a flattened leather cap in an intermediate render: retain its raised,
angled form while correcting the other features. Numerical construction checks
did not establish a visual match; do not describe the nose as resolved.
The historical "done" descriptions below are not approval of the reopened items.

## How the user works with us

- They review rendered sheets and name what's wrong. Fix exactly that, at its source, then show them the same views next to the reference.
- Measure from the references; never invent. When they name a part you don't recognise, restate your reading in one line before building; several rounds this session were lost building the wrong thing.
- Keep it simple. "Too complicated" means rebuild from fewer, plainer pieces.
- Don't stop at a list of faults you can see and could fix.
- One commit and push per fix. Never commit reference images or `.glb` files (the repo is public).

## Build and render

Run `prototypes/clay/tools/setup_env.sh` once per session (a few minutes the first time, then instant). To run it automatically, add a `SessionStart` hook in `.claude/settings.json` (see below). It installs, outside the repo:
- Blender as a Python module (bpy 5.2.3) plus numpy, scipy and Pillow, in `~/.cache/clay-env`;
- three.js r128 for the render viewer, in `~/.cache/clay-three`;
- the reference images, downloaded from the wiki into `prototypes/clay/refs/`. That folder is git-ignored; only the list of sources is committed (`tools/fetch_refs.py`). They're fetched with `format=original` so the side sheet is byte-identical to the one everything was measured on.

Then `prototypes/clay/tools/render.sh head|body SET OUT.jpg` builds and renders a `views.json` set beside the references; `NOBUILD=1` reuses the last build. Build output goes to the git-ignored `prototypes/clay/out/`. Study crops made by hand during the session (`refs/study/*`) aren't recreated: sheets show "missing reference" tiles until they're remade with the skill's `study_crop.py`.

Session-start hook to add to `.claude/settings.json` (not added automatically):

```json
{"hooks": {"SessionStart": [{"hooks": [{"type": "command", "timeout": 600,
  "command": "[ \"$CLAUDE_CODE_REMOTE\" = \"true\" ] || exit 0; \"$CLAUDE_PROJECT_DIR\"/prototypes/clay/tools/setup_env.sh >/tmp/clay-setup.log 2>&1 || echo 'clay setup failed: see /tmp/clay-setup.log'"}]}]}}
```

## Done this session (head)

- **Roof:** a gable (crisp ridge, mirrored plate pairs), its top on the side sheet's traced outline. The front band is one piece and carries on down the snout's front as the **front ridge** (`front_skirt` in `build_head.py`). Its bottom edge meets the orange front muzzle at y 1.37 and rises with the lip's lifted corners.
- **Front muzzle:** no flat front wall. Its front is convex (from above and in profile), its lip edge arcs down, and its corners pull up. The lip starts at the **bite point** (z 1.86); the front muzzle's underside has no teeth.
- **Nose (historical):** superseded by the reference-calibrated raised cap described below; the user rejected the previous placement.
- **Jaw:** a separate piece outlined by the traced line, with a jowl and pebble skin.
- **Teeth (historical):** superseded by solid recurved crowns seated inside gum beds.
- **Eye:** round, with a dark-brown iris and a rich brown rim (opening and lids since rebuilt, below).

## Eye (done in the next session)

Rebuilt simply: the opening is one teardrop outline (round eye, inner corner drawn down and forward into the pink point), measured from the side sheet; the lids are two sheets over it, and the blink covers the eyeball and the caruncle. See head_sheets.md, "Eye: one teardrop opening". Close-up views: the `tear` set in `head/views.json`.

## Known faults (head), most visible first

1. Eye ring reads wide behind the eye in three-quarter views.
2. Front ridge:
   - faint stretch marks in the shading across it;
   - a small fold where the side edge plates meet the front corners;
   - from straight in front, the turn from the roof slope to the front reads as a crease, where the flight render shows a soft round.
3. Nostrils barely show on the nose.
5. Ear curl and jaw back edge (see `CHECKLIST.md`).

Then the neck and body items in `CHECKLIST.md`.


## Current anatomy build (2026-10-27)

`out/body-anatomy-final.glb` is the full-body build with the oral chamber, lowered
independent tongue/floor bed, post-warp dentition, corresponding ear-root loops,
fitted dorsal collar, restored dorsal shell thickness, moving wing-muscle endpoints
and dark carapace wing digits. `out/body-parts.blend` is its unjoined inspection
cache; `body-final-parts.blend` is an older rejected intermediate and must not be
used as the final source. Output and reference assets remain ignored.

The successful build alone does not close the user's review issues. Check the
`oral_review`, `join_review` and `muzzle_correction` sheets using this final GLB.
The prior throat obstruction was identified as body skin at the tongue root,
partly caused by using the ascending jaw crest as the oral floor. Upper teeth
previously also warped with the snout; they now seat against the final palate.

Keep nose likeness, wide-gape throat/fire-path clearance, ear integration and
dorsal collar animation open until their final renders support acceptance. Fire
breathing currently has an attachment guide only, not effects or a fire animation.


Final verification: `out/oral_review-final.jpg`, `out/join_review-final.jpg` and
`out/muzzle_correction-final.jpg` use the rebuilt full-body GLB and the actual
three.js shaders. The final oral lining uses a negative zone mask within the
body's existing material family; never restore ID 3/20 interpolation across
triangles, which produced false teeth/horn/armor streaks. Five guide rays at a
0.85-radian gape have no mesh hits over 0.8 units. This is a finite emission-path
check, not completed fire effects or exhaustive speech validation. Exported
weights are normalized even though the unjoined Blender cache retains some
unnormalized influence totals. The open checklist distinguishes implemented
geometry from reference likeness and remaining surface polish.


## Current review build (2026-10-28)

Use the `*-corrected.jpg` sheets listed in CHECKLIST.md. They replace the older
`*-final.jpg` review images for these issues. The latest full-body build and
unjoined cache include grounded extended lower gums, oral floor/roof attachment
weights, intermediate oral bones, larger neck-only scales, bone-aligned leg
patterns and the revised wing articulation. Black cheek/snout dots are removed.

The model exports `skin_pattern` and `mouth_rig` metadata. The viewer reads the
neck density settings and rotates oral1/oral2 by the configured fractions when
it opens the jaw. External animation clients must drive those oral bones too.
The wing fold clip now uses consistent construction/inverse joint frames; its
shoulder muscle uses a spatial chest-to-humerus influence gradient.

`fit_oral_lining` must run after the finished head/body surfaces exist: near-floor
lining that keeps a partial head weight becomes a flap at wide gape, even with
a volume-preserving wall rig. The corrected final export applied this function
to the full source-built cache before assembly; the same call is in body main.
Final numerical checks: finite export and deformed mouth vertices, normalized
weights, connected wing skins/armor, closed tooth crowns, no added elbow axial
twist, clear fire-guide bundles at jaw 0.85 and 1.05. Reference likeness and fine
surface polish remain open as recorded in the checklist.


Wing shoulder follow-up: `wing_shoulder1/2.L/R` are deformation helper frames at
the humeral socket, sampled at one-third and two-thirds of its fold rotation.
The fold clip drives them. They prevent the deltoid/armor cap from flattening
between chest and humerus after the influence-gradient fix. Both complete-source
wing construction and the final unjoined cache contain these helpers.
