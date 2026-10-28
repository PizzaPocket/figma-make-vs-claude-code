# Clay model: open fixes

## Current review status, 2026-10-28

- [x] Implement replacement ordered wing rig, half-length folded elbow accessory, shared palm and arm-knuckle claw; validate 17 fold samples.
- [x] Implement compact head axis, independent upper-lip silhouette and faceted chin; inspect front seal.
- [ ] User visual review of head proportions, lip character and open/intermediate/closed wings. Previous shoulder pass is rejected.
- [x] Preserve current orange scale sizing: user says it is good now.

Historical unchecked items below remain open unless separately reviewed.


Work top to bottom: the head first, because the neck and body join onto it. Tick an item only once it has been checked against the references (see "Checks" below) and committed.

## Head

- [ ] **Nose: latest revision still rejected.** The user explicitly says the nose in `ccd16b4` remains incorrect. Construction checks, a closed mesh, and the cap's model angle did not establish a reference match. The following replace the earlier placement and nostril prescriptions:
  - **Placement on the shield:** it is still too far forward. Measure the cap and bridge against identifiable shield landmarks in the reference images, including the visible shield surface ahead of the cap. Record the reference coordinates and normalized distances before choosing the setback; do not make another arbitrary small parameter shift.
  - **Front-side planes:** the reference's front sides angle inward. Identify and trace those planes from front and three-quarter views, distinguishing transverse taper from the cap's side-profile tilt. Preserve the raised, angled leather cap; neither a parallel-sided block nor a flattened cap resolves this.
  - **Nostril placement and orientation:** remeasure each opening's location on the cap/side plane, its long-axis direction, opening direction and surrounding rim. Position and carve it on the corrected surface in that surface's local frame. Do not reuse the old path or assume its orientation is correct.
  - **Acceptance:** show reference close-ups beside matched model views in profile, front, three-quarter and shield-normal/top views. Check placement, taper, cap elevation/tilt and nostril orientation separately. The geometry must visibly agree with the references before this item can be marked complete; a numerical angle or topology result is only a supporting check.
- [x] **Eye opening and blink.** One teardrop outline (round eye, inner corner drawn into the pink point), one dark ring round it; the blink covers the eyeball and the caruncle (see head_sheets.md).
- [ ] **Eye ring width.** Even in side view, but it reads wide behind the eye in three-quarter views, where the lid follows the face turning away.
- [ ] **Mouth interior and throat.** Reopened after the user's latest review: opening the jaw exposes an unidentified internal artifact clipping into the back of the throat. Diagnose the actual mesh and its deformation; do not assume it is a particular mouth part. Model a coherent palate, upper/lower gums, tongue, mouth floor, cheek lining and throat entrance, and check them throughout the jaw's range. The mouth must support speech and fire breathing, with a clear emission path and no exposed construction geometry. Do not invent unsupported internal organs to explain fire breathing.
- [ ] **Teeth: anatomy, density and upper gum attachment.** The user reports shard-like teeth, possibly too few, and upper teeth apparently attached along the lip edge rather than seated inside the upper jaw. Build solid animal-like crowns with real volume and roots seated in upper/lower gum tissue. Recheck count, spacing, size and bite against the references; do not simply add teeth to reach an invented count. Upper teeth should generally be concealed by the upper lip in the reference's closed/neutral poses. Check closure, speaking poses and a wide fire-breathing gape together with the mouth interior. The earlier completed "mouth map and teeth" item is superseded by this review.
- [ ] **Roof edge plates.** The plates along the traced edge of the brown roof read as one long strip. They should be separate square plates, with a small step at each joint.
- [ ] **Ear curl.** The jaw line's curl round the ear opening is faint and can only climb straight up. Cut the ear opening as a notch so the edge can hook forward, as drawn.
- [ ] **Ear roots.** The user reports that the ears remain visibly separated at their bases. Their roots should grow naturally out of the cheek surface, with a continuous transition through ear articulation, rather than hovering or looking planted on it. This is separate from the ear-edge curl.
- [ ] **Jaw back edge.** It sits a little high and steep compared with the side sheet's line toward the throat notch.

## Neck and its join to the head

- [ ] **Dorsal head–neck continuity.** The user reports a patchy dark-brown gap where the back of the head meets the top/back of the neck. Inspect both geometry and surface treatment across the join; the carapace should read continuously across it. Check neutral and articulated poses before deciding whether the cause is a gap, overlap, weights or shading.
- [ ] **Throat colour.** Right under the jaw the side sheet is cream with bands; the model shows a strip of orange.
- [ ] **Neck scale rows.** The rounded scale rows on the neck are not built.
- [ ] **Neck back plates.** The brown back plates on the neck bunch together on the inside of the bend.

## Body

- [ ] **Belly plates.** The stepped belly bands are painted; build them as real plates.
- [ ] **Hind thigh.** Its top pokes up through the side of the torso.
- [ ] **Toes.** Sculpt the toes into the hands and feet; only the claws are separate pieces.
- [ ] **Tail.** Build the hook at the tip and the row of tail spikes.
- [ ] **Mane.** Not built.
- [ ] **Wings.** First pass built in the side sheet's folded pose (`wing` in body_design.json): the arm along the flank, the forearm down to a low wrist with a thumb claw, four plated fingers with claws, and the membrane scalloped between the tips. Still to do: posing (the official art raises them), membrane colour and thickness at the edges, and plates with depth.
- [ ] **Wing-arm shoulder continuity.** The user reports that the upper shoulder section appears disconnected from the rest of the wing arm. Make the shoulder, upper arm and subsequent arm structure read as one continuous anatomical limb, and verify the transition in folded and spread poses.
- [x] **Wing-finger surface.** The user finds the orange fingers inappropriate and proposes the same texture/style as the carapace. Implemented dark carapace treatment along every digit; checked with the final shaded folded and spread renders.
- [ ] **Widths.** Body widths are estimates; check them against the front and three-quarter art.

## Checks (before ticking anything)

- Trace colour edges and outlines from the reference pixels; never place them by eye.
- Blend a true side view, framed at the side sheet's scale, over the side sheet.
- Render three-quarter views at the angles of the official art and compare them side by side.
- One commit and push per fix, with the design notes, element sheet and skill updated in the same commit.


## Latest implementation and validation (2026-10-27)

- Nose: setback, inward cap taper and surface-oriented nostrils implemented; the
  attachment tangent now ignores individual plate grooves. Reference likeness
  remains open, rather than being accepted from clearance measurements alone.
- Mouth: independent floor/tongue bed, recessed throat chamber, weighted lining,
  solid rooted crowns and palate-seated upper gums implemented. Final closed and
  open poses are in `oral_review`. Boundary material-ID interpolation was also
  corrected so lining does not render as unrelated horn/armor stripes.
- Fire guide: five rays across a 0.024-wide bundle travel 0.8 units unobstructed
  at jaw angle 0.85. This checks the emission guide, not a fire effect or every
  possible talking pose.
- Teeth: both crown meshes have zero nonmanifold edges and zero degenerate
  triangles. Upper crowns are hidden in the neutral rendered bite.
- Ears: 42 root samples per ear are seated 0.004 inside final skin; corresponding
  root loops and local cheek relaxation replace the earlier twisted footprint.
  Root shape and the ear opening still need likeness/detail work.
- Neck: fitted collar, matched weights and restored dorsal shell thickness are
  implemented. The surface still needs aesthetic smoothing and plate-flow review.
- Wings: each arm and armor shell is a single connected component; chest/humerus
  attachment endpoints are separate. Folded, intermediate and spread renders
  show continuous underlying skin. Armor transitions still warrant polish.
- Final glTF: finite positions, nonnegative weights and maximum weight-sum error
  1.8e-7. Python compilation, JavaScript syntax and whitespace checks pass.


## User review corrections (2026-10-28)

- Removed the painted cheek/ear-opening and snout-pit dots at their shader source.
- Doubled neck scale spacing after comparing the official How to Draw and flight
  crops. This applies only to the neck, fading into the chest. The discarded
  interpretation of smaller overall orange scales is not implemented.
- Leg pattern coordinates now follow actual limb segments in the rest skeleton;
  front, rear and hind-leg views are included in `surface_review`.
- Lower gums continue behind the final tooth, span down to the actual jaw floor
  and taper into the rear tissue. Oral overlap weights now match their rigid
  host; intermediate oral bones retain cheek/throat volume at wide gape.
  Rendered angles 0–1.05 radians show the previous floor flap and spikes removed.
- Wing shoulder weights now follow both muscle attachments. A shared arm bend
  plane removes the independent elbow roll. All five fold stages, a top view
  and clay render are in `wing_motion_review`. Fine socket and armor-edge
  shaping remains open; connected topology alone is not the acceptance test.

Current proofs are `out/surface_review-corrected.jpg`,
`out/gape_stress-corrected.jpg` and `out/wing_motion_review-corrected.jpg`.
