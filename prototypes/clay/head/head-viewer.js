// Test viewer for the head parts: colours from the design rules, jaw and tongue on bones.
(function () {
  "use strict";
  // parts: 1 face, 2 jaw, 3 mouth interior, 4 teeth, 5 tongue, 6 eye, 7 eyelid, 8 horn, 9 ear frill, 10 roof, 11 nose crest
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
    const m = new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, roughness: 0.6, skinning: true });
    if (clay) m.defines = { CLAY: '' }; // plain clay render: judge the forms without paint
    m.onBeforeCompile = (sh) => {
      sh.vertexShader = sh.vertexShader
        .replace("#include <common>", "#include <common>\nattribute float _part; attribute float _a; attribute float _b; attribute float _zone;\nvarying vec3 vObj; varying float vPart; varying vec3 vAB;")
        .replace("#include <begin_vertex>", "#include <begin_vertex>\nvObj = position; vPart = _part; vAB = vec3(_a, _b, _zone);");
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
            float pit = 1.0 - smoothstep(0.004, 0.008, length(vec2(vObj.z - 1.805, vObj.y - 1.513)));
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
          if (isP(11.0) > 0.5) { // nose crest, nostrils dark under the flares
            col = mix(dark * 1.05, line, (1.0 - smoothstep(0.0, 0.06, min(vAB.z, 1.0 - vAB.z))) * step(0.0, vAB.z) * 0.8);
            col = mix(col, vec3(0.012, 0.006, 0.005), smoothstep(0.25, 0.55, vAB.y));
            if (vAB.z < 0.0) col = line;
            rough = 0.5;
          }
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
          if (isP(7.0) > 0.5) { col = mix(line * 0.6, orange * 0.9, smoothstep(0.18, 0.3, vAB.x)); } // lid, dark rim at the margin
          if (isP(8.0) > 0.5) { col = mix(dark * 1.15, dark * 0.8, smoothstep(0.6, 1.0, vAB.x)); col = mix(col, line, smoothstep(0.25, 0.7, vAB.y) * 0.85); rough = 0.35; } // smooth horn, incised ring lines inked
          if (isP(9.0) > 0.5) { col = mix(srgb(vec3(246.0, 166.0, 107.0)), srgb(vec3(250.0, 205.0, 160.0)), vAB.x * 0.7); col = mix(col, srgb(vec3(200.0, 120.0, 80.0)), lineAt(fract(vAB.y * 3.0), 0.05) * 0.7); col = mix(col, line, (1.0 - smoothstep(0.0, 0.06, min(vAB.y, 1.0 - vAB.y))) * 0.8); }
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
    function setPose(jawOpen, tongue, blink) {
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
      // blink: each lid bone lies along the eye's canthal axis; a positive turn about it closes the lid
      for (const n in bones) if (n.startsWith("lid")) {
        const up = n.startsWith("lidUpper");
        bones[n].quaternion.copy(bind[n]).multiply(Q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), blink * (up ? 1.2 : 0.25)));
      }
    }
    return {
      shot(cam, target, jawOpen, tongue, fov, blink) {
        setPose(jawOpen || 0, tongue || 0, blink || 0);
        camera.fov = fov || 30; camera.updateProjectionMatrix();
        camera.position.set(...cam); camera.lookAt(...target);
        renderer.render(scene, camera);
      },
    };
  }
  window.mountHead = mountHead;
})();
