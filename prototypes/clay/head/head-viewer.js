// Test viewer for the head parts: colours from the design rules, jaw and tongue on bones.
(function () {
  "use strict";
  // parts: 1 face, 2 jaw, 3 mouth interior, 4 teeth, 5 tongue, 6 eye, 7 eyelid, 8 horn, 9 ear frill, 10 roof underlay, 12 caruncle, 13 roof plates (nose crest sculpted in)
  const GLSL = `
    varying vec3 vObj; varying float vPart; varying vec3 vAB;
    vec3 srgb(vec3 c) { return pow(c / 255.0, vec3(2.2)); }
    float isP(float p) { return 1.0 - step(0.5, abs(vPart - p)); }
    vec3 hash3(vec3 p) { p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6))); return fract(sin(p) * 43758.5453); }
    float cellEdge(vec3 x) { vec3 p = floor(x), f = fract(x); float d1 = 8.0, d2 = 8.0;
      for (int k = -1; k <= 1; k++) for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
        vec3 b = vec3(float(i), float(j), float(k)); vec3 r = b + hash3(p + b) * 0.8 - f; float d = dot(r, r);
        if (d < d1) { d2 = d1; d1 = d; } else if (d < d2) d2 = d; }
      return sqrt(d2) - sqrt(d1); }
    // overlapping shingle scales in rows (p in scale spacings: x along the body toward the tail, y round it), each a
    // disc a little wider than the spacing, the one nearer the head lying on top (the side sheet's neck): returns the
    // distance in from the free edge of the scale showing at p (x) and that scale's id (y)
    vec2 shingle(vec2 p) { float best = 1e9; vec2 r = vec2(1.0, 0.0);
      for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
        float row = floor(p.y) + float(j), off = mod(row, 2.0) * 0.5;
        vec2 c = vec2(floor(p.x - off) + float(i) + off + 0.5, row + 0.5);
        vec3 h = hash3(vec3(c, 7.0)); c += (h.xy - 0.5) * 0.12;
        float d = length(p - c);
        if (d < 0.74 && c.x < best) { best = c.x; r = vec2(0.74 - d, h.z); } }
      return r; }
    float lineAtW(float f, float w) { float e = min(f, 1.0 - f); return 1.0 - smoothstep(w, w + fwidth(f) * 1.5 + 0.01, e); }
    // plates in brick rows (p: rows, columns), organically warped: returns the joint line (x) and a per-plate tint (y)
    vec3 plates(vec2 p) { float r = p.x, c = p.y + 0.5 * floor(p.x);
      r += 0.14 * sin(c * 1.7 + floor(c) * 2.3); c += 0.1 * sin(r * 1.3 + floor(r) * 1.7);
      return vec3(max(lineAtW(fract(r), 0.05), lineAtW(fract(c), 0.045)), hash3(vec3(floor(r), floor(c), 5.0)).x, 0.0); }
    float lineAt(float f, float w) { float e = min(f, 1.0 - f); return 1.0 - smoothstep(w, w + fwidth(f) * 1.5 + 0.01, e); }
  `;
  function material(THREE, clay) {
    const m = new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, roughness: 0.6, skinning: true, morphTargets: true, morphNormals: true });
    if (clay) m.defines = { CLAY: '' }; // plain clay render: judge the forms without paint
    m.onBeforeCompile = (sh) => {
      sh.vertexShader = sh.vertexShader
        .replace("#include <common>", "#include <common>\nattribute float _part; attribute vec3 _abz;\nvarying vec3 vObj; varying float vPart; varying vec3 vAB;")
        .replace("#include <begin_vertex>", "#include <begin_vertex>\nvObj = position; vPart = _part; vAB = _abz;");
      sh.fragmentShader = sh.fragmentShader
        .replace("#include <common>", "#include <common>\n" + GLSL)
        .replace("#include <map_fragment>", `
          vec3 dark = srgb(vec3(98.0, 45.0, 33.0)), line = srgb(vec3(58.0, 24.0, 17.0));
          vec3 orange = srgb(vec3(229.0, 88.0, 41.0)), cream = srgb(vec3(241.0, 196.0, 142.0));
          vec3 col = orange; float rough = 0.6; float groove = 0.0;
          if (isP(1.0) > 0.5) { // orange face with pebble scales
            float pe = (1.0 - smoothstep(0.02, 0.05, cellEdge(vObj * 30.0))) * (1.0 - vAB.z); // the overhang's underside is smooth skin
            col = mix(orange, line, pe * 0.22);
            float ear = 1.0 - smoothstep(0.010, 0.015, length(vec2(vObj.z - 1.410, vObj.y - 1.652)));
            float pit = 1.0 - smoothstep(0.004, 0.008, length(vec2(vObj.z - 1.796, vObj.y - 1.505)));
            col = mix(col, line * 0.5, max(ear, pit) * step(0.08, abs(vObj.x)));
            groove = pe * 0.5;
          }
          if (isP(10.0) > 0.5) { // roof: overlapping bands (geometry), outlined at each band's back edge and along the eave
            float f = vAB.y;
            col = mix(dark * 1.12, dark * 0.88, f);
            col = mix(col, line, smoothstep(0.93, 0.99, f) * 0.9);
            col = mix(col, line, (1.0 - smoothstep(0.0, 0.025, min(vAB.z, 1.0 - vAB.z))) * step(0.0, vAB.z) * 0.9);
            if (vAB.z < 0.0) col = line;
            rough = 0.5;
          }
          if (isP(13.0) > 0.5) { // roof plates: solid tiles; their bevelled edges and the gaps between them make the lines
            col = mix(dark * 0.92, dark * 1.12, vAB.y);
            col = mix(line, col, smoothstep(0.0, 0.004, vAB.x));
            col = mix(col, vec3(0.012, 0.006, 0.005), smoothstep(0.25, 0.55, vAB.z)); // nostrils, sculpted into the nose plate
            rough = 0.5;
          }
          if (isP(20.0) > 0.5) { // trunk: dark back, orange side, cream underside (vAB: s along the spine, the trunk's share, zone)
            float zv = vAB.z;
            // the sides: shingle scales ~0.065 along x 0.06 round (side sheet's neck), free edges facing back; vPart carries
            // the distance round the trunk (20 + around / 4)
            vec2 sc = shingle(vec2(vAB.x / 0.065, (vPart - 20.0) * 4.0 / 0.06));
            float pe = 1.0 - smoothstep(0.03, 0.08, sc.x);
            // the legs (where the trunk's share is low): plates in brick rows across the limb, ~0.07 x 0.075, organically
            // warped (How to Draw); rows by height up the leg, and along the ground (by z) on the feet and toes
            float limb = 1.0 - smoothstep(0.3, 0.6, vAB.y), foot = 1.0 - smoothstep(0.1, 0.17, vObj.y);
            vec3 legP = plates(vec2(vObj.y / 0.07, (vObj.x + vObj.z) / 0.075)), footP = plates(vec2(vObj.z / 0.07, vObj.x / 0.075));
            float lp = mix(legP.x, footP.x, foot), lt = mix(legP.y, footP.y, foot); // the two patterns blended, not their coordinates
            pe = mix(pe, lp, limb); sc.y = mix(sc.y, lt, limb); sc.x = mix(sc.x, 0.4, limb);
            vec3 back = mix(dark, line, lineAt(fract(vAB.x / 0.10), 0.04) * 0.6); // back plates ~0.08-0.12 apart (measured)
            vec3 side = mix(orange * (0.93 + 0.1 * sc.y) * (0.9 + 0.1 * smoothstep(0.0, 0.4, sc.x)), line, pe * 0.45); // each scale lit toward its middle
            vec3 belly = mix(cream, line, lineAt(fract(vAB.x / 0.095), 0.035) * 0.45 * smoothstep(0.5, 0.8, vAB.y)); // ventral bands ~0.09-0.10 apart (measured), on the trunk only (vAB.y: its share)
            float mer = (1.0 - smoothstep(0.004, 0.008, abs(vObj.x))) * smoothstep(0.1, 0.25, vAB.x) * (1.0 - smoothstep(1.35, 1.55, vAB.x)) * smoothstep(0.5, 0.8, vAB.y);
            belly = mix(belly, line, mer * 0.55); // the meridian: a seam down the middle of the plates, throat to mid-thorax (How to Draw, box set)
            col = zv < 0.5 ? mix(back, side, zv * 2.0) : mix(side, belly, zv * 2.0 - 1.0);
            // the ear opening sits on the cheek line, so half of it is on this skin (the head's, behind the line)
            float earHole = 1.0 - smoothstep(0.010, 0.015, length(vec2(vObj.z - 1.410, vObj.y - 1.652)));
            col = mix(col, line * 0.5, earHole * step(0.08, abs(vObj.x)));
            groove = pe * 0.3 * (1.0 - abs(zv - 0.5) * 2.0) + mer * 0.5 * smoothstep(0.5, 1.0, zv);
          }
          if (isP(21.0) > 0.5) { // limb skin: plates in columns along the limb, ~0.10 long x 0.075 across (measured), organically warped
            float r = vAB.x / 0.10, c = vAB.y / 0.075;
            r += 0.16 * sin(c * 1.7 + floor(c) * 2.3); c += 0.1 * sin(r * 1.3 + floor(r) * 1.7);
            float pl = max(lineAt(fract(r), 0.045), lineAt(fract(c), 0.04));
            float tint = hash3(vec3(floor(r), floor(c), 3.0)).x;
            col = mix(mix(orange * (0.94 + 0.12 * tint), cream, vAB.z), line, pl * 0.5); groove = pl * 0.6;
          }
          if (isP(22.0) > 0.5) { col = mix(dark, dark * 1.15, vAB.x); rough = 0.5; } // dark shoulder mass
          if (isP(23.0) > 0.5) { col = srgb(vec3(72.0, 50.0, 58.0)); rough = 0.25; } // claws
          if (isP(24.0) > 0.5) { // wing arm and fingers: orange pebbled skin, dark square plates in rows over the top (Umber, the side sheet)
            float pe = 1.0 - smoothstep(0.02, 0.05, cellEdge(vObj * 30.0));
            float a = fract(vAB.x / 0.075), top = smoothstep(0.58, 0.68, vAB.y);
            vec3 skin = mix(orange * 0.92, line, pe * 0.25);
            vec3 plate = mix(dark * mix(0.9, 1.08, hash3(vec3(floor(vAB.x / 0.075), 7.0, 1.0)).x), line, lineAt(a, 0.06) * 0.85);
            col = mix(skin, plate, top); rough = 0.5; groove = pe * 0.4 * (1.0 - top) + lineAt(a, 0.06) * top * 0.5;
          }
          if (isP(25.0) > 0.5) { // wing membrane: peach, lighter toward the tips, inked along the trailing edge
            col = mix(srgb(vec3(232.0, 128.0, 70.0)), srgb(vec3(246.0, 168.0, 106.0)), vAB.x);
            col = mix(col, line, smoothstep(0.985, 1.0, vAB.y) * 0.9); rough = 0.7;
          }
          if (isP(2.0) > 0.5) { // cream lower jaw: faint pebble scales, larger and softer than the face's (no bands: those start on the neck)
            float pe = 1.0 - smoothstep(0.02, 0.06, cellEdge(vObj * 20.0));
            col = mix(cream, line, pe * 0.14); groove = pe * 0.35;
          }
          if (isP(3.0) > 0.5) { col = srgb(vec3(120.0, 40.0, 45.0)); rough = 0.4; }
          if (isP(4.0) > 0.5) { col = srgb(vec3(245.0, 238.0, 220.0)); rough = 0.25; }
          if (isP(5.0) > 0.5) { col = srgb(vec3(170.0, 70.0, 75.0)); rough = 0.35; }
          if (isP(6.0) > 0.5) { // eyeball: _a is the angle from the gaze direction (0..1 over 180 degrees)
            float a = vAB.x;
            col = srgb(vec3(242.0, 236.0, 226.0));
            // wide-open eye: a white ring shows all round a warm brown iris, as in every official image
            col = mix(col, srgb(vec3(112.0, 66.0, 34.0)), 1.0 - smoothstep(0.155, 0.165, a)); // dark warm brown iris, as in every official image
            col = mix(col, srgb(vec3(92.0, 44.0, 14.0)), (1.0 - smoothstep(0.15, 0.185, abs(a - 0.152) + 0.15)) * 0.95); // a rich brown rim round the iris
            col = mix(col, vec3(0.01), 1.0 - smoothstep(0.085, 0.095, a)); // large pupil
            rough = 0.08;
          }
          if (isP(12.0) > 0.5) { col = mix(line * 0.6, srgb(vec3(226.0, 140.0, 150.0)), smoothstep(0.2, 0.45, vAB.x)); rough = 0.3; } // caruncle and tear tail, the tail rimmed dark
          if (isP(7.0) > 0.5) { float pl = 1.0 - smoothstep(0.02, 0.05, cellEdge(vObj * 30.0)); col = mix(line * 0.6, mix(orange, line, pl * 0.22), max(smoothstep(0.2, 0.28, vAB.x), vAB.y)); } // lid: a heavy dark ring round the opening (only between the eye's corners)
          if (isP(8.0) > 0.5) { col = mix(dark * 1.15, dark * 0.8, smoothstep(0.6, 1.0, vAB.x)); col = mix(col, line, smoothstep(0.25, 0.7, vAB.y) * 0.85); rough = 0.35; } // smooth horn, incised ring lines inked
          if (isP(9.0) > 0.5) { // ear: pale peach hollow, the upper front edge rolled over in an orange rim with a dark fold
            // line where it turns in, a thin orange lower edge, dark outline; orange behind (vAB: along, across 0 lower -> 1 upper, back)
            // the hollow's front edge sweeps from the upper rim at a third of the way along down to the lower edge at half way (side sheet)
            float front = vAB.x - (0.5 - 0.2 * (vAB.y - 0.1) / 0.62);
            float rimU = smoothstep(0.70, 0.76, vAB.y), rimL = 1.0 - smoothstep(0.06, 0.12, vAB.y), rimF = 1.0 - smoothstep(-0.02, 0.03, front);
            col = mix(srgb(vec3(250.0, 200.0, 150.0)), srgb(vec3(246.0, 166.0, 107.0)), vAB.x * 0.5);
            col = mix(col, orange, max(max(max(rimU, rimL), rimF), vAB.z));
            float fold = max((1.0 - smoothstep(0.012, 0.03, abs(vAB.y - 0.73))) * step(0.0, front), (1.0 - smoothstep(0.008, 0.025, abs(front))) * step(vAB.y, 0.73));
            float edge = max(1.0 - smoothstep(0.0, 0.025, vAB.y), smoothstep(0.975, 1.0, vAB.y));
            col = mix(col, line, max(fold * (1.0 - vAB.z), edge) * 0.85); }
          #ifdef CLAY
          col = srgb(vec3(190.0, 180.0, 170.0)); groove = 0.0; rough = 0.7;
          #endif
          diffuseColor.rgb = col;
        `)
        .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = rough;")
        // the wing membrane is thin: lit from behind it glows with the light through it (every flying cover, seen from below)
        .replace("#include <emissivemap_fragment>", "#include <emissivemap_fragment>\n#ifndef CLAY\nif (isP(25.0) > 0.5) totalEmissiveRadiance += diffuseColor.rgb * 0.4;\n#endif")
        .replace("#include <normal_fragment_begin>", `#include <normal_fragment_begin>
          { vec3 sp = -vViewPosition; vec3 dx = dFdx(sp), dy = dFdy(sp); vec3 r1 = cross(dy, normal), r2 = cross(normal, dx);
            float det = dot(dx, r1); float h = -groove * 0.003; vec3 grad = sign(det) * (dFdx(h) * r1 + dFdy(h) * r2);
            normal = normalize(abs(det) * normal - grad); }`);
    };
    return m;
  }
  async function mountHead(THREE, el, opts) {
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    renderer.outputEncoding = THREE.sRGBEncoding; renderer.toneMapping = THREE.ACESFilmicToneMapping;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene(); scene.background = new THREE.Color(0x15110e);
    const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
    scene.add(new THREE.HemisphereLight(0xe8ecf2, 0x4a3a2c, 0.9));
    const key = new THREE.DirectionalLight(0xfff4e6, 1.5); key.position.set(3, 4, 4); scene.add(key);
    const rim = new THREE.DirectionalLight(0xb8c8ff, 0.5); rim.position.set(-3, 2, -3); scene.add(rim);
    const gltf = await new Promise((res, rej) => new THREE.GLTFLoader().load(opts.glbUrl, res, undefined, rej));
    let sk = null; gltf.scene.traverse(o => { if (o.isSkinnedMesh) sk = o; });
    sk.material = material(THREE, opts.clay); sk.frustumCulled = false;
    scene.add(gltf.scene);
    const bones = {}; sk.skeleton.bones.forEach(b => (bones[b.name] = b));
    const bind = {}; for (const n in bones) bind[n] = bones[n].quaternion.clone();
    // the wings rest spread; the "wings_fold" clip turns their bones to the side sheet's folded pose (0 spread, 1 folded)
    const fold = (gltf.animations || []).find(a => /wings_fold/.test(a.name));
    const foldTracks = fold ? fold.tracks.filter(tr => /\.quaternion$/.test(tr.name))
      .map(tr => ({ node: gltf.scene.getObjectByName(THREE.PropertyBinding.parseTrackName(tr.name).nodeName), it: tr.createInterpolant() }))
      .filter(t => t.node) : [];
    function resize() { const w = el.clientWidth, h = el.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
    resize();
    const Q = new THREE.Quaternion(), X = new THREE.Vector3(1, 0, 0);
    function setPose(jawOpen, tongue, lids, morphs, wings, headTurn) {
      // rotations about the model's x axis, converted into each bone's frame
      for (const n in bones) bones[n].quaternion.copy(bind[n]);
      const w = wings === undefined ? 1 : Math.max(0, Math.min(1, wings));
      for (const t of foldTracks) t.node.quaternion.fromArray(t.it.evaluate(w * fold.duration));
      const apply = (n, ang) => {
        const b = bones[n]; const wq = new THREE.Quaternion(); b.parent.getWorldQuaternion(wq);
        const axis = X.clone().applyQuaternion(wq.clone().invert()).normalize();
        b.quaternion.premultiply(Q.setFromAxisAngle(axis, ang));
      };
      gltf.scene.updateMatrixWorld(true);
      // head turn: [pitch, yaw] in radians (pitch about the model's x, yaw about its y), spread evenly down the
      // neck and the head as a neck bends
      if (headTurn) {
        const chain = ["neck1", "neck2", "neck3", "neck4", "head"].filter(n => bones[n]);
        const Y = new THREE.Vector3(0, 1, 0);
        for (const n of chain) {
          const b = bones[n]; const wq = new THREE.Quaternion(); b.parent.getWorldQuaternion(wq); const inv = wq.clone().invert();
          b.quaternion.premultiply(Q.setFromAxisAngle(X.clone().applyQuaternion(inv).normalize(), (headTurn[0] || 0) / chain.length));
          b.quaternion.premultiply(Q.setFromAxisAngle(Y.clone().applyQuaternion(inv).normalize(), (headTurn[1] || 0) / chain.length));
          gltf.scene.updateMatrixWorld(true);
        }
      }
      apply("jaw", jawOpen);
      gltf.scene.updateMatrixWorld(true);
      apply("tongue1", -tongue * 0.3); gltf.scene.updateMatrixWorld(true);
      apply("tongue2", -tongue * 0.4); gltf.scene.updateMatrixWorld(true);
      apply("tongue3", -tongue * 0.5);
      // lids: each lid bone lies along the eye's canthal axis; a positive turn about it closes the lid
      const L = lids || [0, 0, 0];
      for (const n in bones) {
        const k = n.startsWith("lidUpperIn") ? 0 : n.startsWith("lidUpperOut") ? 1 : n.startsWith("lidLower") ? 2 : -1;
        if (k >= 0) bones[n].quaternion.copy(bind[n]).multiply(Q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), L[k]));
      }
      // face: muscle actions as morph targets
      const dict = sk.morphTargetDictionary || {};
      const m = Object.assign({ wingfold: w }, morphs || {});
      // blink: in-between shapes blink1..blinkN along the lids' arc; a weight w blends the two steps either side of it
      const nb = Object.keys(dict).filter(k => /^blink\d+$/.test(k)).length;
      if (nb && m.blink !== undefined) {
        const w = Math.max(0, Math.min(1, m.blink)) * nb, i = Math.floor(w), f = w - i;
        if (i >= 1) m["blink" + i] = 1 - f;
        if (i < nb) m["blink" + (i + 1)] = f;
      }
      for (const name in dict) sk.morphTargetInfluences[dict[name]] = m[name] || 0;
    }
    return {
      // pose: {jaw, tongue, lids: [upperIn, upperOut, lower], morphs: {action: weight}, wings: 0 spread .. 1 folded (the default),
      // head: [pitch, yaw] turned down the neck}
      // (see head_design.json "expressions")
      shot(cam, target, pose, fov) {
        pose = pose || {};
        setPose(pose.jaw || 0, pose.tongue || 0, pose.lids, pose.morphs, pose.wings, pose.head);
        camera.fov = fov || 30; camera.updateProjectionMatrix();
        camera.position.set(...cam); camera.lookAt(...target);
        renderer.render(scene, camera);
      },
    };
  }
  window.mountHead = mountHead;
})();
