# Clay model: handoff

State at the end of the session on branch `wings-of-fire-game`. Read with `CHECKLIST.md` (open fixes), `head/head_sheets.md` and `body/body_sheets.md` (what each part is and why), and the skill `.claude/skills/creature-sculpting/SKILL.md` (how we work).

## How the user works with us

- They review rendered sheets and name what's wrong. Fix exactly that, at its source, then show them the same views next to the reference.
- Measure from the references; never invent. When they name a part you don't recognise, restate your reading in one line before building; several rounds this session were lost building the wrong thing.
- Keep it simple. "Too complicated" means rebuild from fewer, plainer pieces.
- Don't stop at a list of faults you can see and could fix.
- One commit and push per fix. Never commit reference images or `.glb` files (the repo is public).

## Build and render

Blender as a Python module lives in the session scratchpad (`blenv/bin/python`), along with the references (`clayref/`, `covers/`, `study/`) and helper scripts. A new session needs these set up again:
- `head/build_head.py --out head.glb` builds the head; `body/build_body.py --out clay.glb` builds the whole creature.
- `.claude/skills/creature-sculpting/scripts/render_sheet.py` renders a `views.json` set beside reference images (see the skill's Toolkit section).

## Done this session (head)

- **Roof:** a gable (crisp ridge, mirrored plate pairs), its top on the side sheet's traced outline. The front band is one piece and carries on down the snout's front as the **front ridge** (`front_skirt` in `build_head.py`). Its bottom edge meets the orange front muzzle at y 1.37 and rises with the lip's lifted corners.
- **Front muzzle:** no flat front wall. Its front is convex (from above and in profile), its lip edge arcs down, and its corners pull up. The lip starts at the **bite point** (z 1.86); the front muzzle's underside has no teeth.
- **Nose:** an extruded shield-section mass coming out of the roof's front; the user said to leave it as it is.
- **Jaw:** a separate piece outlined by the traced line, with a jowl and pebble skin.
- **Teeth:** flat blades, a front row across the bite plus side rows, each perpendicular to its lip edge with the tip raked back.
- **Eye:**
  - round, with a dark-brown iris and a rich brown rim;
  - corners projected onto the side sheet: inner corner 58° below horizontal, back corner 25° above;
  - the blink turns about the canthal axis, stored as 6 in-between shapes.

## In progress when stopped

- **Tear tail** (`tear_tail` in `build_head.py`; `eye.lids.caruncle.tail_*` in `head_design.json`): a pink teardrop from the eye's inner corner, forward and down past the eyeball, rimmed dark. It's committed but too long and thin. The next step was `tail_reach` 1.17 (from 1.3) and `tail_width` 0.22 (from 0.17), then compare with the side sheet's teardrop.

## Known faults (head), most visible first

1. Tear tail proportions (above).
2. Front ridge:
   - faint stretch marks in the shading across it;
   - a small fold where the side edge plates meet the front corners;
   - from straight in front, the turn from the roof slope to the front reads as a crease, where the flight render shows a soft round.
3. Nostrils barely show on the nose.
4. Lids still dome slightly behind the eye.
5. Ear curl and jaw back edge (see `CHECKLIST.md`).

Then the neck and body items in `CHECKLIST.md`.
