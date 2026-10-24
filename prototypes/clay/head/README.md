# Clay's head (rebuild, step 1)

The head built as articulated parts, following `docs/clay-model-review.md`:

- **Rigid upper head:** muzzle, brow and skull back to the ear, on the `head` bone.
  It carries the horns, eyes, eyelids and ear frills.
- **Lower jaw:** hinges open on the `jaw` bone.
- **Mouth:** palate and floor, upper and lower teeth, and a tongue on `tongue1`–`tongue3`.

Each skin is a clean quad loft: rings of points around the head at measured stations
(top line and jaw line scanned from the reference outline; widths from the official
front three-quarter art, since MudWings have broad, flat muzzles). The dark top plate,
brow shelf, eye socket and nostrils come from rules in `build_head.py`.

```
python3 prototypes/clay/head/build_head.py --out cache/clay/head.glb
```

`head-viewer.js` colours the parts from the design rules and can open the jaw and move
the tongue.

## Still to do

- Eyes read sleepy: the upper lid covers too much. Clay's eyes are wide and warm.
- Horns are still a little thick; the arc should sweep back more.
- The cheek crease from the mouth corner to the ear is only painted, not shaped.
- Eyelids and ear frills need their own bones (blink, ear flicks).
- The jaw has to join the throat skin so the throat stretches when the mouth opens,
  and the upper head's back edge has to meet the neck under the frill and first plates.
