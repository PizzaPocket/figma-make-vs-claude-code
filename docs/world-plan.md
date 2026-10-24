# World plan: Pyrrhia

Status: draft for discussion. Nothing here is built yet.

## Goals

- **Pyrrhia only** for now. Pantala and the Lost Continent are out of scope.
- **As vast as possible while still realistically playable.** Flying is the main way to travel, so the world can be much bigger than a walking game's.
- **Godot 4** is the engine.

## Source material

| Source | What it gives us |
| --- | --- |
| `PyrrhiaColored.png` (wiki, 2327×1768) | The main layout reference: coastlines, kingdoms, rivers, mountains, landmarks |
| `Pyrrhia AGttDW.png` (wiki, 1703×990) | The newer map from *A Guide to the Dragon World*, used to cross-check |
| Era maps (Darkstalker, Dragonslayer, Moon Rising) | Variants for later; the layout is the same, the labels differ |
| Wiki location pages (99 total, 48 in *AGttDW*) | Text descriptions of terrain, buildings and what is near what |

No elevation or 3D data exists. Every height in the world is our own interpretation of the art and the text.

The repo is **public**, so the wiki's map images are **not committed**. A script downloads them into a git-ignored folder instead.

## Scale

**Proposal: a world area of 64 km × 48 km**, matching the map's roughly 4:3 shape and including the sea around the continent.

- About 40% of that is land, so roughly **1,200 km² of land**. For comparison, Skyrim is about 37 km² and GTA V about 80 km².
- Crossing Pyrrhia at a 40 m/s cruise (about 145 km/h) takes about **25 minutes**. At an 80 m/s boost it takes about **13 minutes**.
- 64 km fits inside Terrain3D's stated limit of 65.5 km at 1 m spacing. We would use 4 m spacing (next section), which raises the ceiling further.

At this scale one pixel of the source map covers about 28 m. Everything finer than that (ridges, gullies, dunes, riverbanks) has to be generated, not traced.

**The pipeline must be scale-independent.** Every stage takes the world size as a setting. We prototype at a small scale (for example 16 × 12 km) and scale up once it plays well. Picking the final size is then a number change, not a rebuild.

## Terrain resolution and memory

The player mostly sees the terrain from the air, so we can use a coarser grid than a walking game and add close-up detail in the shader.

| Vertex spacing | Grid for 64 × 48 km | Approx. memory (land regions only) |
| --- | --- | --- |
| 1 m | 65k × 49k | over 15 GB, not feasible |
| 2 m | 32k × 24k | about 4 GB, too heavy without streaming |
| **4 m** | **16k × 12k** | **about 1 GB, workable on a mid-range desktop GPU** |

The memory estimate assumes Terrain3D's height, control and color maps at 4 bytes each per sample, and that only regions containing land are stored. Open-sea regions cost nothing.

## Engine approach (Godot)

### Terrain

Use **[Terrain3D](https://github.com/TokisanGames/Terrain3D)**, a free Godot terrain plugin:

- It imports heightmaps and splits the world into regions stored as separate files.
- It has built-in level of detail and texture painting.
- It has an instancer for scattering vegetation.

**Risk:** Terrain3D does not yet stream regions in and out. It keeps every region loaded, so the 4 m spacing above is what keeps the memory budget sane. Streaming is on its roadmap, and if it arrives we can tighten the spacing.

### Floating-point precision

Standard Godot builds use 32-bit floats, and objects start to jitter a few kilometres from the world origin. A 64 km world needs one of two fixes:

1. **Double-precision Godot build** ("large world coordinates"). This means compiling Godot ourselves, and Terrain3D also has to be built for double precision.
2. **Floating origin.** Periodically shift the whole world back so the player stays near (0, 0, 0). This works with stock Godot, but every system has to tolerate the shift.

**Decision:** prototype both early, at full 64 km scale, before building anything else on top.

### Streaming everything except terrain

- Divide the world into a grid of cells, for example 1 km × 1 km. Each cell is its own scene with props, buildings and gameplay objects.
- Load nearby cells in the background (Godot's threaded resource loading) and unload far ones.
- Vegetation comes from the terrain instancer or MultiMesh, generated from the biome map rather than placed by hand.
- **Big landmarks are always present as low-detail versions**: Jade Mountain, the palaces, the Sky Kingdom peaks. Flying players will see them from tens of kilometres away. The detailed version swaps in when near.
- Atmospheric haze and distance fog hide the edge of what is loaded and sell the scale.

### Content density

A world this big is only fun if there is something to find. Plan:

- **Hand-built hubs** at canon locations: palaces, Jade Mountain, Burn's stronghold, Scavenger dens, the Sea Kingdom's islands.
- **Procedural fill** everywhere else: biome-based vegetation, rocks and points of interest.

## Map data pipeline

Each stage writes files the next stage reads, so any stage can be redone without repeating the others.

| Stage | Input | Output | Done by |
| --- | --- | --- | --- |
| 0. Fetch | Wiki | Source images, location pages (git-ignored) | Script |
| 1. Trace | Source map | `pyrrhia.geojson`: coastline, kingdom borders, rivers, lakes, mountain ranges, landmarks | Auto-extract, then corrected by hand |
| 2. Region rules | Traced data, wiki text | `regions.yaml`: per-kingdom height range, roughness, biome, landmark notes | Written together |
| 3. Heightmap | Stages 1–2 | Height image at the chosen world size: traced shapes, then noise, then erosion | Script |
| 4. Biome / splat maps | Stages 1–3 | Texture-control images (sand, mud, jungle, snow, rock, grass) and vegetation density | Script |
| 5. Godot import | Stages 3–4 | Terrain3D regions, landmark markers, cell grid | Godot import script |

The first automatic land/sea test on the colored map got the overall shape right. Its known failures, which hand correction in stage 1 will fix:

- Snowy Ice Kingdom areas read as water.
- The Sea Kingdom's small islands merged together.
- Fine coastline detail was lost.

## Kingdom terrain notes (first pass)

These are taken from the map art and need checking against the wiki text in stage 2.

| Region | Terrain intent |
| --- | --- |
| Ice Kingdom | High, cold plateau, glaciers, ice cliffs at the coast |
| Kingdom of Sand | Wide flat desert with dunes and rocky outcrops, oasis around the stronghold |
| Sky Kingdom | The continent's tallest range, the north–south spine; the palace is carved into peaks |
| Diamond Spray River and Delta | River valley from the Sky Kingdom into a broad wetland delta |
| Mud Kingdom | Low, flat swamp and marsh, many waterways |
| Rainforest Kingdom | Low to mid hills under a dense canopy, southern coast |
| Kingdom of the Sea | Ocean and scattered islands inside the eastern crescent, mostly underwater content |
| Jade Mountain | A single prominent mountain, a landmark visible from far away |

## Open questions

1. **Target hardware.** Desktop PC only? This decides the memory budget and the vertex spacing.
2. **How the player moves on the ground.** Mostly flying, or also a lot of walking? Walking needs finer ground detail.
3. **Underwater.** How much of the Kingdom of the Sea is playable underwater? This affects whether the seabed needs real terrain.
4. **Era.** Which point in the timeline? This changes labels, buildings and politics, not the land.
5. **Art style.** Stylized, like the book illustrations, or realistic? This affects terrain textures and shaders.

## Next steps

1. Write the fetch script and add the cache folder to `.gitignore`.
2. Stage 1: auto-extract the coastline and features, then hand-correct them.
3. A precision test in Godot: a flat 64 km Terrain3D world with a fast-flying camera. Try both a double-precision build and a floating origin.
