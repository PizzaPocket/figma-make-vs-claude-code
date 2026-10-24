# Clay prototype

A 3D Clay built in Blender (`bpy`, Blender as a Python module) from a description of
his design written as data. Work in progress: **not on model yet.**

## How it works

- `clay_design.json` describes Clay as data, read from the side-view reference:
  - body cross-sections from nose to tail tip (head rows scanned from the outline,
    widths read from the shading), with where the dark back and cream belly begin;
  - the rule for each zone's plates and scales (dark back plates, the border of square
    plates, orange shingle rows, head plate segments and cheek pebbles, cream bands,
    leg grid), with sizes and a palette sampled from the art;
  - raised features: tail studs, wing-arm blocks, finger studs, hooked claws, a ridged
    horn per side, the mane, ear frills, eyes, mouth groove and nostrils.
- `build_clay.py` turns that into a rigged `.glb`: one continuous skin (legs, wing
  arms and features blended into the body), the large plates carved into the
  surface, a 52-bone skeleton with bone-heat weights, and per-vertex data (part,
  position along/around the body, colour zones) for the viewer. The bind pose is the
  reference pose (wings folded and raised).
- `clay-viewer.js` loads the `.glb` in three.js (r128), colours it and adds fine scale
  lines from the same rules, and drives rest / walk / fly poses procedurally.
- `fetch_reference.py` downloads the reference (fan art, not committed: the repo is public).

## Running it

```
python3 prototypes/clay/fetch_reference.py        # -> cache/clay/ref1400.png
pip install bpy numpy pillow scikit-image scipy   # bpy needs the matching Python (3.13 for bpy 5.2)
python3 prototypes/clay/build_clay.py --out cache/clay/clay.glb --design prototypes/clay/clay_design.json
```

## Where it stands

What works: the plate and scale system follows the reference from every angle, not
just the side, and every part comes from the data. One continuous skin on the rig.

Still off model, most visible first:
1. Head: from the front the snout is blunt and boxy, the eye barely shows, and it
   lacks the reference's clean wedge, brow and jaw shapes.
2. Proportions: the reference is more compact (deeper chest, shorter thicker neck,
   taller front legs); this reads long and low.
3. Wing arm: the leading-edge blocks don't show yet; membranes are pale, not peach.
4. The tail isn't curled into the reference's resting pose.

Not game-ready yet: colours and fine scales come from a web shader rather than baked
UV textures Godot can use directly; the mesh is dense (~114k vertices) with no clean
joint loops; no animation clips.
