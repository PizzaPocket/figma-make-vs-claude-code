# Clay prototype

A first 3D Clay, built with Blender (`bpy`, Blender as a Python module) and checked
against a side-view reference. Work in progress: **not on model yet.**

## How it works

- `build_clay.py` builds a rigged `clay.glb`:
  - The head, neck, body and tail are one shape driven by profiles measured from the
    reference (scanned column by column). Legs and wing arms are blended into it, so
    the skin is one continuous surface.
  - The bind pose is the reference pose (wings folded and raised), so the reference
    lines up with the model.
  - Blender decimates the mesh, builds a 52-bone skeleton and binds the skin with
    bone-heat weights. Wing membranes, mane, ear frills and horns are added as
    sheets on the same skeleton.
  - For every vertex it records whether the reference shows that spot directly
    (`_PROJ`), plus body coordinates and colour zones for everywhere else.
- `clay-viewer.js` loads the `.glb` in three.js (r128), projects the reference art
  onto the surfaces the reference shows (head, neck, chest, front legs, front of the
  body, wing arm), fills the rest with colours sampled from the art, and drives
  rest / walk / fly poses procedurally.

## Running it

```
python3 prototypes/clay/fetch_reference.py        # -> cache/clay/ref1400.png
pip install bpy numpy pillow scikit-image scipy   # bpy needs the matching Python (3.13 for bpy 5.2)
python3 prototypes/clay/build_clay.py --out cache/clay/clay.glb --ref cache/clay/ref1400.png
```

## Where it stands

What works:
- In the aligned side view, the body from neck to mid-back, the front legs and the
  wing arm read like the reference (projected art).
- One continuous skin with bone-heat weights; rest, walk and fly poses deform it.
- The inner wing membrane attaches down at the hind leg, as in the reference.

Known problems, in priority order:
1. **Head shape.** The last change (a soft minimum across the body's profile
   segments, meant to remove faint creases) inflated the snout into a bulbous
   shape. Next step: go back to the exact minimum and remove the creases with a
   light blur of the distance field instead (sigma about 1.6 cells).
2. Areas the reference doesn't show (top, underside, front, the rear behind the
   wing) use plain colours and look flat next to the projected art.
3. The resting tail should drop to the ground and curl forward; it needs tuning.
4. Projected art only exists for the side; other views need painted textures.

For a game-ready Clay, the realistic path is still a sculpt against the reference
(in Blender) or a base mesh from an image-to-3D tool, rigged with this skeleton.
The earlier attempt that wrote the geometry by hand in the browser was a dead end
and is not kept here.
