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

`head-viewer.js` colours the parts from the design rules and can open the jaw and move
the tongue.

## Still to do

See "Known differences" at the end of `head_sheets.md`. Beyond those:
- Eyelids and ear frills need their own bones, for blinks and ear flicks.
- The jaw has to join the throat skin, so the throat stretches when the mouth opens.
- The upper head's back edge has to meet the neck under the frill and the first plates.
