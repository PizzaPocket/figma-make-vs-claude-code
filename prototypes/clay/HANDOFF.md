# Clay model: handoff

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
- **Nose:** an extruded shield-section mass coming out of the roof's front; the user said to leave it as it is.
- **Jaw:** a separate piece outlined by the traced line, with a jowl and pebble skin.
- **Teeth:** flat blades, a front row across the bite plus side rows, each perpendicular to its lip edge with the tip raked back.
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
