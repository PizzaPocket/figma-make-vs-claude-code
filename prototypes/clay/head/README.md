# Clay's head (rebuild, step 1)

The head built as articulated parts, following `docs/clay-model-review.md`:

- **Rigid upper head** (`head` bone), made of fitted pieces:
  - an orange face mass;
  - a dark banded roof shell over it, whose back corners carry on as the horns;
  - a nose crest with the nostrils;
  - eyes and ear frills.
- **Eyelids** on their own bones, hinged on each eye's canthal axis (blink).
- **Lower jaw:** hinges open on the `jaw` bone.
- **Mouth:** palate and floor, upper and lower teeth, and a tongue on `tongue1`–`tongue3`.

Each skin is a clean quad loft: rings of points around the head at measured stations.

All measurements live in `head_design.json`:
- stations;
- the dark plate edge;
- sculpt brushes (ridges, creases, dents);
- eye, horn and ear-frill frames.

The reasoning behind each number is in `head_sheets.md`, one sheet per element, following the `creature-sculpting` skill. `build_head.py` only turns the data into geometry.

```
python3 prototypes/clay/head/build_head.py --out cache/clay/head.glb
```

`head-viewer.js` colours the parts and poses them: jaw, tongue, lid bones, face morph
targets (muscle actions) and the named poses in `head_design.json`.

Review sheets (model beside the references) come from the skill's renderer and `views.json`:

```
python3 .claude/skills/creature-sculpting/scripts/render_sheet.py --viewer prototypes/clay/head/head-viewer.js \
    --mount mountHead --glb cache/clay/head.glb --three THREE_R128_DIR --views prototypes/clay/head/views.json \
    --set overview --design prototypes/clay/head/head_design.json --refs REFERENCE_CROPS_DIR --out sheet.jpg
```

## Still to do

See "Known differences" at the end of `head_sheets.md`. Beyond those:
- Eyelids and ear frills need their own bones, for blinks and ear flicks.
- The jaw has to join the throat skin, so the throat stretches when the mouth opens.
- The upper head's back edge has to meet the neck under the frill and the first plates.
