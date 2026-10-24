# Clay's body: element sheets

The working notes behind `body_design.json`, following the `creature-sculpting` skill. The head
has its own sheets in `../head/head_sheets.md`.

**Coordinates:** reference pixels are on the 1400-px side sheet (Spirit978). Model units use `z = (700 - px) / 343` and `y = (830 - py) / 343`. x is Clay's left.

**Bind pose:** the side sheet's pose, so the side render can be laid directly against the sheet. Two exceptions:
- The tail's lower run, which the sheet draws below the feet (nearer the viewer), rests on the ground.
- That run curls toward the viewer (+x).

## Plan: pieces and order

| Element | Pieces | Status |
| --- | --- | --- |
| Neck, torso, tail | one continuous loft along a curved spine (the "trunk"), skinned to spine bones | first pass |
| Head join | the trunk runs on into the head's back; head bone parented to the last neck bone | first pass |
| Dorsal plates, border squares, neck scales, ventral bands, tail studs | plates and sculpted rows on the trunk | to do |
| Mane | spines along the neck and back, on spring bones | to do |
| Front legs and hands | shoulder sculpted into the trunk (dark patch), upper arm, forearm, compact hand: big hooked claws, high dewclaw | first pass |
| Hind legs and feet | thigh + shin loft, long digitigrade foot loft, four splayed toes, heel spur, studs on top | first pass |
| Wings | arm with square plates along the leading edge, five fingers, membrane with a scalloped trailing edge | to do |

## Trunk (neck, torso, tail)

**References**
- Side sheet: traced with `trunk_trace.py`; see the overlay `trunk_overlay.jpg`, not committed.
- Official front and three-quarter art for widths.

**Primary mass:** one continuous body, measured as depths from a traced spine to the dorsal and ventral outlines, perpendicular to the spine.
- **Neck:** short and thick, about 0.45–0.55 deep. It runs from behind the skull down and back into the chest.
- **Torso:** a deep barrel, about 0.9 from back to belly.
- **Tail:** thick (0.25–0.38) nearly to its tip. It curls down at the hips, then runs forward along the ground to its tip.

**Widths:** not in the side sheet. Taken as a factor of the mean depth: 0.85 at the neck, 1.0 at the chest (a broad barrel), 0.85 on the tail. They still need checking against the front art.

**Zones.** On the neck and torso the edges are measured side-view lines, not fractions of the side:
- **Dark edge:** the line of small square plates. From behind the ear it runs back, then straight *down* the side of the neck into the shoulder. It goes round the bottom of the dark shoulder patch, then back along the wing arm (`dark_edge_px`).
- **Cream edge:** bounds the wide throat band, down the front of the neck into the chest. Behind the forelegs the cream rises to meet the dark edge, with no orange band (`cream_edge_px`).
- **Tail:** a dark top and a cream underside meeting at mid-side, by fraction.

A level fraction was wrong: it kept the dark edge high along the neck instead of sweeping down to the shoulder.

**Pattern rhythms,** measured with scanlines across the ink lines on the sheet:
- Ventral bands: ~0.09–0.10 apart on the belly, throat and tail underside.
- Back plates: ~0.08–0.12 along the back.
- Limb plates: ~0.10 along the limb by ~0.07–0.075 across, in columns down the limb, organically warped. Not staggered, never bricks.

Patterns are laid out in model units along and around each part, so they stay the same size on thick and thin parts. Pattern seams sit on hidden sides.

**Rig:** hips → spine → chest → neck1–4 → head; tail1–12 from the hips, getting shorter toward the tip.

**Known differences**
- The dark back is still paint on the trunk. Like the head's roof, it should be its own overlapping plates fitted over the trunk, with the border squares as a row of small tiles along the dark edge.
- The neck's orange side needs its rows of rounded scales, and the throat and belly bands should be real stepped plates.
- The toes are separate tubes pushed into the hands and feet. They should be sculpted into them, with only the claws separate.
- The hind thigh pokes up the side of the torso; in the sheet it stays below the dark edge.
- The sheet's tail tip hooks up; mine ends straight.
- Widths are estimates.
- No plates, scales, bands, studs or mane yet: the surface only has the zone colours.
- The orange of the neck reaches too far back.
