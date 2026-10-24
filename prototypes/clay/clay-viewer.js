// Viewer for the Blender-built Clay (.glb): colours and fine scale detail come from the
// design rules (clay_design.json), and the rig is driven procedurally (rest, walk, fly).
(function () {
  "use strict";

  // Surface parts written by build_clay2.py: 0 body, 1 limb, 2 wing bone, 3 claw, 4 tail stud,
  // 5 wing plate/stud, 6 membrane, 7 mane, 8 horn, 9 ear frill, 10 eye.
  const GLSL = /* glsl */`
    varying vec3 vObj;
    varying float vPart;
    varying vec2 vUV;
    varying vec3 vZone;
    varying float vH;
    vec3 srgb(vec3 c) { return pow(c / 255.0, vec3(2.2)); }
    float isPart(float p) { return 1.0 - step(0.5, abs(vPart - p)); }
    vec3 hash3(vec3 p) { p = vec3(dot(p, vec3(127.1, 311.7, 74.7)), dot(p, vec3(269.5, 183.3, 246.1)), dot(p, vec3(113.5, 271.9, 124.6))); return fract(sin(p) * 43758.5453); }
    vec2 cells(vec3 x) { // x: gap to the nearest cell edge, y: cell id
      vec3 p = floor(x), f = fract(x); float d1 = 8.0, d2 = 8.0, id = 0.0;
      for (int k = -1; k <= 1; k++) for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) {
        vec3 b = vec3(float(i), float(j), float(k)); vec3 h = hash3(p + b); vec3 r = b + h * 0.8 - f; float d = dot(r, r);
        if (d < d1) { d2 = d1; d1 = d; id = h.x; } else if (d < d2) d2 = d; }
      return vec2(sqrt(d2) - sqrt(d1), id);
    }
    float lineAt(float f, float w) { float e = min(f, 1.0 - f); float aa = fwidth(f) * 1.5; return 1.0 - smoothstep(w, w + aa + 0.01, e); }
  `;

  function clayMaterial(THREE) {
    const mat = new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, roughness: 0.6, metalness: 0, skinning: true });
    mat.onBeforeCompile = (shader) => {
      shader.vertexShader = shader.vertexShader
        .replace("#include <common>", `#include <common>
          attribute float _part; attribute float _u; attribute float _v; attribute float _zback; attribute float _zbelly; attribute float _zedge; attribute float _h;
          varying vec3 vObj; varying float vPart; varying vec2 vUV; varying vec3 vZone; varying float vH;`)
        .replace("#include <begin_vertex>", `#include <begin_vertex>
          vObj = position; vPart = _part; vUV = vec2(_u, _v); vZone = vec3(_zback, _zbelly, _zedge); vH = _h;`);
      shader.fragmentShader = shader.fragmentShader
        .replace("#include <common>", "#include <common>\n" + GLSL)
        .replace("#include <map_fragment>", `
          // palette and layout rules from clay_design.json
          vec3 dark = srgb(vec3(98.0, 45.0, 33.0)), line = srgb(vec3(58.0, 24.0, 17.0));
          vec3 orange = srgb(vec3(229.0, 88.0, 41.0)), orangeL = srgb(vec3(240.0, 122.0, 62.0));
          vec3 cream = srgb(vec3(241.0, 196.0, 142.0)), creamS = srgb(vec3(214.0, 156.0, 101.0));
          vec3 peach = srgb(vec3(246.0, 166.0, 107.0)), peachL = srgb(vec3(250.0, 200.0, 150.0));
          vec3 col = orange; float groove = 0.0; float rough = 0.6;
          float s = vUV.x, v = vUV.y;
          if (isPart(0.0) > 0.5) {
            float head = smoothstep(1.3, 1.4, vObj.z);
            // dark back: long overlapping plates in staggered rows (head: segments across the plate)
            float row = floor(v / 0.12);
            float f = fract(s / 0.16 + 0.5 * row);
            float plateLine = max(lineAt(f, 0.035), lineAt(fract(v / 0.12), 0.03));
            vec3 backC = mix(dark * 0.82, dark * 1.1, f);
            float hseg = lineAt(fract(s / 0.09), 0.05);
            backC = mix(backC, mix(dark, dark * 1.08, fract(s / 0.09)), head);
            float bl = mix(plateLine, hseg, head);
            backC = mix(backC, line, bl * 0.85);
            // border of square plates along the edge of the dark back
            float sq = lineAt(fract(s / 0.05), 0.1);
            vec3 edgeC = mix(dark * 1.15, line, sq * 0.9);
            // orange: rows of half-round scales on the neck and body, pebbles on the head
            vec2 g = vec2(s / 0.065, v / 0.13);
            float r2 = floor(g.x); vec2 fr = vec2(fract(g.x), fract(g.y + 0.5 * mod(r2, 2.0)));
            float dd = length(vec2((fr.x + 0.08) * 0.065, (fr.y - 0.5) * 0.13)) / (0.56 * 0.13);
            float arc = (1.0 - smoothstep(0.0, fwidth(dd) * 1.5 + 0.05, abs(dd - 1.0))) * step(fr.x * 0.065, 0.56 * 0.13);
            vec3 flank = mix(orange * 1.04, orange * 0.86, smoothstep(0.4, 1.0, dd));
            flank = mix(flank, line, arc * 0.7);
            vec2 pc = cells(vObj * 30.0);
            vec3 headC = mix(orange, line, (1.0 - smoothstep(0.02, 0.08, pc.x)) * 0.55);
            flank = mix(flank, headC, head);
            // cream: bands across the throat, belly and tail; three columns under the tail
            float period = vObj.z > 0.95 ? 0.06 : 0.09;
            float bandL = lineAt(fract(s / period), 0.06);
            float tailCols = (1.0 - step(-1.15, vObj.z)) * lineAt(fract(abs(v) / 0.07), 0.06);
            vec3 bellyC = mix(cream, creamS, 0.35 * smoothstep(0.5, 1.0, fract(s / period)));
            bellyC = mix(bellyC, line, max(bandL, tailCols) * 0.75);
            col = mix(flank, backC, vZone.x);
            col = mix(col, edgeC, step(0.5, vZone.z) * (1.0 - head));
            col = mix(col, bellyC, vZone.y);
            // outline where the zones meet
            float seam = max(1.0 - smoothstep(0.0, 0.12, abs(vZone.x - 0.5)), 1.0 - smoothstep(0.0, 0.12, abs(vZone.y - 0.5)));
            col = mix(col, line, seam * 0.8);
            groove = max(max(bl * vZone.x, arc * (1.0 - vZone.x) * (1.0 - vZone.y)), max(bandL, tailCols) * vZone.y);
          }
          if (isPart(1.0) > 0.5) {
            float gl = max(lineAt(fract(s / 0.06), 0.06), lineAt(fract(v / 0.06), 0.06));
            col = mix(mix(orange, orangeL, 0.3 * fract(s / 0.06)), cream, vZone.y);
            col = mix(col, line, gl * 0.7);
            groove = gl;
          }
          if (isPart(2.0) > 0.5) { vec2 pc = cells(vObj * 34.0); col = mix(dark * 1.05, line, (1.0 - smoothstep(0.02, 0.08, pc.x)) * 0.6); }
          if (isPart(3.0) > 0.5) { col = srgb(vec3(72.0, 50.0, 58.0)); rough = 0.3; }
          if (isPart(4.0) > 0.5) { col = dark * 0.85; rough = 0.45; }
          if (isPart(5.0) > 0.5) { col = dark * 0.78; rough = 0.45; }
          if (isPart(6.0) > 0.5) {
            col = mix(peach, peachL, smoothstep(0.6, 1.0, s) * 0.6);
            col = mix(col, dark, vZone.x * 0.85);
            col = mix(col, line, smoothstep(0.96, 1.0, s) * 0.8);
            rough = 0.72;
          }
          if (isPart(7.0) > 0.5) col = mix(srgb(vec3(60.0, 26.0, 30.0)), srgb(vec3(110.0, 52.0, 58.0)), s);
          if (isPart(8.0) > 0.5) { col = mix(dark * 0.9, dark * 1.3, s); col = mix(col, line, step(0.05, v) * 0.7); rough = 0.4; }
          if (isPart(9.0) > 0.5) {
            col = mix(peach, cream, s);
            col = mix(col, creamS, max(lineAt(fract(v * 3.0), 0.04), lineAt(s, 0.04)) * 0.8);
          }
          if (isPart(10.0) > 0.5) {
            vec3 iris = srgb(vec3(120.0, 72.0, 34.0));
            col = srgb(vec3(242.0, 236.0, 226.0));
            col = mix(col, iris, smoothstep(0.78, 0.8, s));
            col = mix(col, vec3(0.01), smoothstep(0.93, 0.945, s));
            col = mix(col, line, (1.0 - smoothstep(0.0, 0.05, abs(s - 0.6))) * 0.9);
            rough = 0.1;
          }
          diffuseColor.rgb = col;
        `)
        .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = rough;")
        .replace("#include <normal_fragment_begin>", `#include <normal_fragment_begin>
          {
            // fine scale lines read as shallow grooves
            vec3 sp = -vViewPosition; vec3 dx = dFdx(sp), dy = dFdy(sp);
            vec3 r1 = cross(dy, normal), r2 = cross(normal, dx); float det = dot(dx, r1);
            float h = -groove * 0.004;
            vec3 grad = sign(det) * (dFdx(h) * r1 + dFdy(h) * r2);
            normal = normalize(abs(det) * normal - grad);
          }`);
    };
    return mat;
  }

  // ---------- Rig helpers ----------
  // Rotations are written in world axes of the bind pose and converted to each
  // bone's own axes, so the pose code doesn't depend on how Blender oriented the bones.
  function prepareRig(THREE, skinned) {
    const bones = {};
    skinned.skeleton.bones.forEach(b => (bones[b.name] = b));
    skinned.updateMatrixWorld(true);
    const rootInv = new THREE.Quaternion();
    skinned.getWorldQuaternion(rootInv).invert();
    const info = {};
    for (const [name, b] of Object.entries(bones)) {
      const B = new THREE.Quaternion();
      b.getWorldQuaternion(B); B.premultiply(rootInv);
      const p = new THREE.Vector3(); b.getWorldPosition(p); skinned.worldToLocal(p);
      info[name] = { bindLocal: b.quaternion.clone(), B, Binv: B.clone().invert(), pos: p };
    }
    return { bones, info };
  }

  // Spread-wing directions (world, left side) for flight; the rest pose is the bind pose.
  const SPREAD = {
    wing1L: [0.83, 0.43, -0.22], wing2L: [0.94, 0.25, -0.30],
    f1: [0.95, 0.15, -0.27], f2: [0.85, -0.05, -0.52], f3: [0.68, -0.22, -0.70], f4: [0.48, -0.36, -0.80], f5: [0.25, -0.45, -0.86],
  };

  function spreadRotations(THREE, rig) {
    const out = {}, world = {};
    const chain = [["wing1L", null, "wing2L"], ["wing2L", "wing1L", "f1aL"]];
    for (let f = 1; f <= 5; f++) chain.push([`f${f}aL`, "wing2L", `f${f}bL`], [`f${f}bL`, `f${f}aL`, null]);
    for (const s of [1, -1]) {
      const n = (b) => (b && s < 0 ? b.slice(0, -1) + "R" : b);
      for (const [name, parent, child] of chain) {
        const I = rig.info[n(name)];
        if (!I) continue;
        let dir;
        if (child) dir = rig.info[n(child)].pos.clone().sub(I.pos).normalize();
        else { const bb = rig.bones[n(name)]; const tip = new THREE.Vector3(0, 1, 0).applyQuaternion(I.B); dir = tip.normalize(); }
        const key = name.startsWith("f") ? name.slice(0, 2) : name;
        const d = SPREAD[key];
        const target = new THREE.Vector3(s * d[0], d[1], d[2]).normalize();
        const Q = new THREE.Quaternion().setFromUnitVectors(dir, target);
        world[n(name)] = Q;
        const pq = parent ? world[n(parent)] : new THREE.Quaternion();
        out[n(name)] = pq.clone().invert().multiply(Q);
      }
    }
    return out;
  }

  async function mountClay(THREE, el, opts) {
    const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: !!opts.preserve });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x15110e);
    scene.fog = new THREE.Fog(0x15110e, 14, 32);
    // opts.orthoSide: a camera that lines up pixel-for-pixel with the 1400x1020 reference
    const camera = opts.orthoSide
      ? new THREE.OrthographicCamera(-700 / 343, 700 / 343, 510 / 343, -510 / 343, 0.1, 100)
      : new THREE.PerspectiveCamera(32, 1, 0.1, 100);
    if (opts.orthoSide) { camera.position.set(20, 320 / 343, 0); camera.lookAt(0, 320 / 343, 0); } else camera.position.set(6.5, 2.6, 6.5);
    scene.add(new THREE.HemisphereLight(0xe8ecf2, 0x4a3a2c, 0.9));
    const key = new THREE.DirectionalLight(0xfff4e6, 1.6); key.position.set(5, 9, 6);
    key.castShadow = true; key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { left: -6, right: 6, top: 6, bottom: -6, near: 1, far: 30 });
    key.shadow.bias = -0.0005; scene.add(key);
    const rim = new THREE.DirectionalLight(0xb8c8ff, 0.6); rim.position.set(-6, 4, -7); scene.add(rim);

    const gcan = document.createElement("canvas"); gcan.width = gcan.height = 256;
    const gg = gcan.getContext("2d");
    gg.fillStyle = "#2a241e"; gg.fillRect(0, 0, 256, 256);
    for (let i = 0; i < 900; i++) { gg.fillStyle = `rgba(${20 + Math.random() * 40},${15 + Math.random() * 30},${10 + Math.random() * 20},0.25)`; gg.fillRect(Math.random() * 256, Math.random() * 256, 3 + Math.random() * 8, 3 + Math.random() * 8); }
    const gtex = new THREE.CanvasTexture(gcan); gtex.wrapS = gtex.wrapT = THREE.RepeatWrapping; gtex.repeat.set(12, 12); gtex.encoding = THREE.sRGBEncoding;
    const ground = new THREE.Mesh(new THREE.CircleGeometry(16, 64), new THREE.MeshStandardMaterial({ map: gtex, roughness: 0.95 }));
    ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

    const gltf = await new Promise((res, rej) => new THREE.GLTFLoader().load(opts.glbUrl, res, undefined, rej));
    let skinned = null;
    gltf.scene.traverse(o => { if (o.isSkinnedMesh) skinned = o; });
    skinned.material = clayMaterial(THREE);
    skinned.castShadow = true; skinned.receiveShadow = true; skinned.frustumCulled = false;
    scene.add(gltf.scene);
    const rig = prepareRig(THREE, skinned);
    const spread = spreadRotations(THREE, rig);

    const helper = new THREE.SkeletonHelper(gltf.scene); helper.visible = false;
    helper.material.depthTest = false; helper.material.transparent = true; scene.add(helper);

    let controls = null;
    const target = [0, 1.05, -0.2];
    if (THREE.OrbitControls && !opts.orthoSide) {
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.target.set(...target); controls.enableDamping = true; controls.minDistance = 2.5; controls.maxDistance = 22;
      controls.maxPolarAngle = Math.PI * 0.49; controls.autoRotateSpeed = 0.5; controls.update();
    } else if (!opts.orthoSide) camera.lookAt(...target);

    const Q = new THREE.Quaternion(), E = new THREE.Euler(), D = {};
    const TAU = Math.PI * 2;
    const state = { mode: "idle", spread: 0, spreadTarget: 0 };
    const rootBone = rig.bones.hips, rootY = rootBone.position.y;
    function pose(t) {
      for (const name in rig.bones) (D[name] || (D[name] = new THREE.Quaternion())).identity();
      const add = (name, x, y, z) => { if (D[name]) D[name].multiply(Q.setFromEuler(E.set(x, y, z))); };
      const walk = state.mode === "walk", fly = state.mode === "fly";
      const br = Math.sin(t * 1.6);
      add("spine2", 0.012 * br, 0, 0); add("chest", -0.015 * br, 0, 0);
      let yaw = 0.1 * Math.sin(t * 0.37), pitch = 0.04 * Math.sin(t * 0.53);
      // at rest the tail drops to the ground and curls forward along it, as in the reference
      const restTail = state.mode === "idle" ? [[-0.22, 0], [-0.28, 0.08], [0.05, 0.38], [0.25, 0.55], [0.12, 0.6], [0.05, 0.55]] : null;
      ["tail1", "tail2", "tail3", "tail4", "tail5", "tail6"].forEach((n, i) => {
        if (restTail) add(n, restTail[i][0], restTail[i][1], 0);
        const curl = 0;
        const amp = walk ? 0.15 : fly ? 0.07 : 0.05, sp = walk ? 4.2 : 1.3;
        add(n, fly ? -0.05 : 0.02 * Math.sin(t * 0.9 - i * 0.5), curl + amp * Math.sin(t * sp - i * 0.7) * (0.6 + i * 0.2), 0);
      });
      for (const s of [1, -1]) {
        const n = (b) => (s > 0 ? b : b.slice(0, -1) + "R");
        for (const name in spread) if (name.endsWith(s > 0 ? "L" : "R")) D[name].copy(new THREE.Quaternion().slerp(spread[name], state.spread));
        if (fly) {
          const ph = t * TAU * 0.8, flap = Math.sin(ph);
          add(n("wing1L"), 0, s * 0.12 * Math.cos(ph), s * (0.7 * flap - 0.05));
          add(n("wing2L"), 0, 0, s * 0.35 * Math.sin(ph - 0.7));
          for (let f = 1; f <= 5; f++) add(n(`f${f}aL`), 0, 0, s * 0.25 * Math.sin(ph - 1.2));
        }
        if (walk) {
          const base = t / 1.3;
          const leg = (ph) => { const a = TAU * (base + ph); return { swing: Math.sin(a), lift: Math.max(0, -Math.cos(a)) }; };
          const h = leg(s > 0 ? 0 : 0.5), f = leg(s > 0 ? 0.25 : 0.75);
          add(n("thighL"), -0.35 * h.swing, 0, 0); add(n("shinL"), 0.5 * h.lift, 0, 0); add(n("metaL"), -0.6 * h.lift, 0, 0); add(n("footL"), 0.35 * h.lift, 0, 0);
          add(n("upperArmL"), -0.3 * f.swing, 0, 0); add(n("foreArmL"), -0.55 * f.lift, 0, 0); add(n("handL"), 0.65 * f.lift, 0, 0);
        } else if (fly) {
          add(n("thighL"), 0.5, 0, 0); add(n("shinL"), 0.45, 0, 0); add(n("metaL"), -0.35, 0, 0); add(n("footL"), 0.55, 0, 0);
          add(n("upperArmL"), 0.5, 0, 0); add(n("foreArmL"), -1.0, 0, 0); add(n("handL"), 0.7, 0, 0);
        }
      }
      rootBone.position.y = rootY;
      if (walk) {
        const a = TAU * t / 1.3;
        add("hips", 0, 0, 0.03 * Math.sin(a)); add("spine1", 0, 0.04 * Math.sin(a), 0); add("chest", 0, -0.04 * Math.sin(a), 0);
        yaw = -0.05 * Math.sin(a) + 0.06 * Math.sin(t * 0.37);
      }
      if (fly) { add("hips", -0.06, 0, 0); pitch = 0.1 + 0.03 * Math.sin(t * TAU * 0.8); }
      add("neck1", pitch * 0.4, yaw * 0.3, 0); add("neck2", pitch * 0.3, yaw * 0.3, 0); add("neck3", pitch * 0.2, yaw * 0.25, 0); add("head", -pitch * 0.4, yaw * 0.15, 0);
      // world-axis deltas -> each bone's local rotation
      for (const name in rig.bones) {
        const I = rig.info[name];
        rig.bones[name].quaternion.copy(I.bindLocal).multiply(I.Binv.clone().multiply(D[name]).multiply(I.B));
      }
      gltf.scene.position.y = fly ? 0.7 + 0.12 * Math.sin(t * TAU * 0.8 + Math.PI) : walk ? -0.02 * Math.abs(Math.sin(TAU * t / 1.3)) : 0;
    }

    function resize() {
      const w = el.clientWidth, h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h, false);
      if (camera.isPerspectiveCamera) { camera.aspect = w / h; camera.fov = w / h < 1 ? 50 : 32; camera.updateProjectionMatrix(); }
    }
    resize();
    if (window.ResizeObserver) new ResizeObserver(resize).observe(el);
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let last = performance.now(), clock = 0, frozen = false;
    function frame(now) {
      const dt = Math.min(0.05, (now - last) / 1000); last = now;
      if (!frozen && (!reduce || state.mode !== "idle")) clock += dt;
      if (!frozen) state.spread += (state.spreadTarget - state.spread) * Math.min(1, dt * 2.5);
      pose(clock);
      if (state.mode === "walk" && !frozen) gtex.offset.y -= dt * 0.15;
      if (controls) controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    const info = skinned.geometry.attributes.position.count;
    return {
      stats: { vertices: info, triangles: skinned.geometry.index.count / 3, bones: skinned.skeleton.bones.length },
      setMode(m) { state.mode = m; state.spreadTarget = m === "fly" || state.wantSpread ? 1 : 0; },
      setWings(spreadOn) { state.wantSpread = spreadOn; state.spreadTarget = spreadOn || state.mode === "fly" ? 1 : 0; },
      setSkeleton(on) { helper.visible = on; },
      setWireframe(on) { skinned.material.wireframe = on; },
      setAutoRotate(on) { if (controls) controls.autoRotate = on; },
      renderAt(t, mode, spreadV, camPos, tgt) {
        frozen = true; state.mode = mode; state.spread = state.spreadTarget = spreadV; clock = t;
        if (camPos) { camera.position.set(...camPos); if (controls) { controls.target.set(...(tgt || target)); controls.update(); } else camera.lookAt(...(tgt || target)); }
      },
    };
  }

  window.mountClay = mountClay;
})();
