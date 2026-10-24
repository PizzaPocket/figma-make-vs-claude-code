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
            float pe = 1.0 - smoothstep(0.02, 0.05, cellEdge(vObj * 30.0));
            col = mix(orange, line, pe * 0.22);
            float ear = 1.0 - smoothstep(0.010, 0.015, length(vec2(vObj.z - 1.420, vObj.y - 1.638)));
            float pit = 1.0 - smoothstep(0.004, 0.008, length(vec2(vObj.z - 1.818, vObj.y - 1.505)));
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
          if (isP(20.0) > 0.5) { // trunk: dark back, orange side, cream underside (vAB: s along the spine, side fraction, zone)
            float zv = vAB.z;
            float pe = 1.0 - smoothstep(0.02, 0.05, cellEdge(vObj * 14.0));
            vec3 back = mix(dark, line, lineAt(fract(vAB.x / 0.10), 0.04) * 0.6); // back plates ~0.08-0.12 apart (measured)
            vec3 side = mix(orange, line, pe * 0.25);
            vec3 belly = mix(cream, line, lineAt(fract(vAB.x / 0.095), 0.035) * 0.45); // ventral bands ~0.09-0.10 apart (measured)
            col = zv < 0.5 ? mix(back, side, zv * 2.0) : mix(side, belly, zv * 2.0 - 1.0);
            groove = pe * 0.3 * (1.0 - abs(zv - 0.5) * 2.0);
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
          if (isP(2.0) > 0.5) { // cream lower jaw with bands
            float band = lineAt(fract((2.05 - vObj.z) / 0.06), 0.03);
            col = mix(cream, line, band * 0.3); groove = band * 0.5;
          }
          if (isP(3.0) > 0.5) { col = srgb(vec3(120.0, 40.0, 45.0)); rough = 0.4; }
          if (isP(4.0) > 0.5) { col = srgb(vec3(245.0, 238.0, 220.0)); rough = 0.25; }
          if (isP(5.0) > 0.5) { col = srgb(vec3(170.0, 70.0, 75.0)); rough = 0.35; }
          if (isP(6.0) > 0.5) { // eyeball: _a is the angle from the gaze direction (0..1 over 180 degrees)
            float a = vAB.x;
            col = srgb(vec3(242.0, 236.0, 226.0));
            // wide-open eye: a white ring shows all round a warm brown iris, as in every official image
            col = mix(col, srgb(vec3(150.0, 92.0, 44.0)), 1.0 - smoothstep(0.155, 0.165, a));
            col = mix(col, srgb(vec3(70.0, 38.0, 20.0)), (1.0 - smoothstep(0.15, 0.17, abs(a - 0.16) + 0.15)) * 0.8);
            col = mix(col, vec3(0.01), 1.0 - smoothstep(0.065, 0.075, a));
            rough = 0.08;
          }
          if (isP(12.0) > 0.5) { col = srgb(vec3(226.0, 140.0, 150.0)); rough = 0.3; } // caruncle
          if (isP(7.0) > 0.5) { float pl = 1.0 - smoothstep(0.02, 0.05, cellEdge(vObj * 30.0)); col = mix(line * 0.6, mix(orange, line, pl * 0.22), smoothstep(0.18, 0.3, vAB.x)); } // lid, dark rim at the margin
          if (isP(8.0) > 0.5) { col = mix(dark * 1.15, dark * 0.8, smoothstep(0.6, 1.0, vAB.x)); col = mix(col, line, smoothstep(0.25, 0.7, vAB.y) * 0.85); rough = 0.35; } // smooth horn, incised ring lines inked
          if (isP(9.0) > 0.5) { // ear frill: pale peach hollow, orange rolled rim round the edge
            float rim = max(smoothstep(0.5, 0.7, abs(vAB.y * 2.0 - 1.0)), smoothstep(0.8, 0.95, vAB.x));
            col = mix(srgb(vec3(250.0, 200.0, 150.0)), srgb(vec3(246.0, 166.0, 107.0)), vAB.x * 0.5);
            col = mix(col, orange, rim); col = mix(col, line, smoothstep(0.93, 0.99, abs(vAB.y * 2.0 - 1.0)) * 0.8); }
          #ifdef CLAY
          col = srgb(vec3(190.0, 180.0, 170.0)); groove = 0.0; rough = 0.7;
          #endif
          diffuseColor.rgb = col;
        `)
        .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = rough;")
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
    function resize() { const w = el.clientWidth, h = el.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); }
    resize();
    const Q = new THREE.Quaternion(), X = new THREE.Vector3(1, 0, 0);
    function setPose(jawOpen, tongue, lids, morphs) {
      // rotations about the model's x axis, converted into each bone's frame
      for (const n in bones) bones[n].quaternion.copy(bind[n]);
      const apply = (n, ang) => {
        const b = bones[n]; const wq = new THREE.Quaternion(); b.parent.getWorldQuaternion(wq);
        const axis = X.clone().applyQuaternion(wq.clone().invert()).normalize();
        b.quaternion.premultiply(Q.setFromAxisAngle(axis, ang));
      };
      gltf.scene.updateMatrixWorld(true);
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
      for (const name in dict) sk.morphTargetInfluences[dict[name]] = (morphs && morphs[name]) || 0;
    }
    return {
      // pose: {jaw, tongue, lids: [upperIn, upperOut, lower], morphs: {action: weight}} (see head_design.json "expressions")
      shot(cam, target, pose, fov) {
        pose = pose || {};
        setPose(pose.jaw || 0, pose.tongue || 0, pose.lids, pose.morphs);
        camera.fov = fov || 30; camera.updateProjectionMatrix();
        camera.position.set(...cam); camera.lookAt(...target);
        renderer.render(scene, camera);
      },
    };
  }
  window.mountHead = mountHead;
})();
