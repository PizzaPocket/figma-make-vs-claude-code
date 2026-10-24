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
| Front legs and hands | shoulder mass, upper arm, forearm, compact hand: big hooked claws, high dewclaw | to do |
| Hind legs and feet | thigh, shin, long digitigrade foot: heel spur, studs along the top | to do |
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

**Zones,** as a fraction of the visible side from back to belly:
- **Neck:** dark top to 0.3 (the border of small square plates), orange side, then the cream throat from about 0.7.
- **Torso behind the forelegs:** the cream comes all the way up to the dark back (0.42–0.45), with no orange band.
- **Tail:** a dark top and a cream underside meeting at mid-side.

**Rig:** hips → spine → chest → neck1–4 → head; tail1–12 from the hips, getting shorter toward the tip.

**Known differences**
- The sheet's tail tip hooks up; mine ends straight.
- Widths are estimates.
- No plates, scales, bands, studs or mane yet: the surface only has the zone colours.
- The orange of the neck reaches too far back.
