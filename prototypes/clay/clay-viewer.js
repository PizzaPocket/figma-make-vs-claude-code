// Viewer for the Blender-built Clay (.glb): projects the reference art onto the
// parts of the skin the reference shows, fills the rest with matching colours,
// and drives the rig procedurally (rest, walk, fly).
(function () {
  "use strict";

  const GLSL = /* glsl */`
    varying vec3 vObj;
    varying vec3 vObjN;
    varying float vPart;
    varying vec2 vUV;
    varying vec2 vZone;
    varying float vProj;
    uniform sampler2D refMap;
    uniform float debugGray;
    vec3 srgb(vec3 c) { return pow(c, vec3(2.2)); }
    float isPart(float p) { return 1.0 - step(0.5, abs(vPart - p)); }
  `;

  function clayMaterial(THREE, refTex) {
    const mat = new THREE.MeshStandardMaterial({ side: THREE.DoubleSide, roughness: 0.62, metalness: 0, skinning: true });
    mat.onBeforeCompile = (shader) => {
      shader.uniforms.refMap = { value: refTex };
      shader.uniforms.debugGray = { value: window.CLAY_GRAY ? 1 : 0 };
      shader.vertexShader = shader.vertexShader
        .replace("#include <common>", `#include <common>
          attribute float _part; attribute float _u; attribute float _v; attribute float _zback; attribute float _zbelly; attribute float _proj;
          varying vec3 vObj; varying vec3 vObjN; varying float vPart; varying vec2 vUV; varying vec2 vZone; varying float vProj;`)
        .replace("#include <begin_vertex>", `#include <begin_vertex>
          vObj = position; vObjN = normal; vPart = _part; vUV = vec2(_u, _v); vZone = vec2(_zback, _zbelly); vProj = _proj;`);
      shader.fragmentShader = shader.fragmentShader
        .replace("#include <common>", "#include <common>\n" + GLSL)
        .replace("#include <map_fragment>", `
          // palette sampled from the reference art
          vec3 dark = srgb(vec3(98.0, 45.0, 33.0) / 255.0), orange = srgb(vec3(229.0, 88.0, 41.0) / 255.0);
          vec3 cream = srgb(vec3(241.0, 196.0, 142.0) / 255.0), line = srgb(vec3(60.0, 25.0, 18.0) / 255.0);
          vec3 peach = srgb(vec3(246.0, 166.0, 107.0) / 255.0), peachHi = srgb(vec3(250.0, 200.0, 150.0) / 255.0);
          float body = isPart(0.0), limb = isPart(1.0), wingb = isPart(2.0), claw = isPart(3.0);
          float horn = isPart(4.0), memb = isPart(5.0), mane = isPart(6.0), frill = isPart(7.0);

          // colours for the parts the reference doesn't show, in the art's style:
          // flat colour with thin dark outlines between plates and scales
          vec3 fill = orange;
          if (body > 0.5) {
            float plate = fract(vUV.x / 0.17);
            vec3 backC = mix(dark, line, (1.0 - smoothstep(0.0, 0.05, min(plate, 1.0 - plate))) * 0.7);
            float band = fract(vUV.x / 0.09);
            vec3 bellyC = mix(cream, line, (1.0 - smoothstep(0.0, 0.07, min(band, 1.0 - band))) * 0.55);
            float sc = fract(vUV.x / 0.07 + 0.5 * floor(vObj.x * 14.0)), scy = fract(vObj.x * 14.0);
            vec3 flankC = mix(orange, line, (1.0 - smoothstep(0.0, 0.08, min(min(sc, 1.0 - sc), min(scy, 1.0 - scy)))) * 0.35);
            fill = mix(mix(flankC, backC, vZone.x), bellyC, vZone.y);
            fill = mix(fill, line, (1.0 - smoothstep(0.0, 0.12, abs(vZone.x - 0.5))) * 0.7);
            fill = mix(fill, line, (1.0 - smoothstep(0.0, 0.12, abs(vZone.y - 0.5))) * 0.7);
          }
          if (limb > 0.5) {
            float r = fract(vObj.y * 9.0);
            fill = mix(orange, line, (1.0 - smoothstep(0.0, 0.06, min(r, 1.0 - r))) * 0.3);
          }
          if (wingb > 0.5) {
            float seg = fract(length(vObj) * 12.0);
            fill = mix(dark * 1.15, line, (1.0 - smoothstep(0.0, 0.1, min(seg, 1.0 - seg))) * 0.8);
          }
          if (claw > 0.5) fill = srgb(vec3(75.0, 46.0, 42.0) / 255.0);
          if (horn > 0.5) fill = mix(dark * 0.8, dark * 1.4, vUV.x);
          if (memb > 0.5) {
            fill = mix(peach, peachHi, smoothstep(0.75, 1.0, vUV.x) * 0.6);
            fill = mix(fill, dark, vZone.x * 0.85);
            fill = mix(fill, srgb(vec3(200.0, 110.0, 70.0) / 255.0), smoothstep(0.94, 1.0, vUV.x));
          }
          if (mane > 0.5) fill = mix(srgb(vec3(60.0, 26.0, 26.0) / 255.0), srgb(vec3(110.0, 50.0, 45.0) / 255.0), vUV.x);
          if (frill > 0.5) fill = mix(peach, cream, vUV.x);

          // the reference art, projected from the side, only where the reference shows
          // that same part of Clay: head, neck, chest, front legs, front of the body and
          // the wing arm (the rear of the body and the wing fingers are covered or drawn
          // differently in the reference)
          float refX = 700.0 - vObj.z * 343.0;
          vec2 ruv = vec2(refX / 1400.0, 1.0 - (830.0 - vObj.y * 343.0) / 1020.0);
          vec3 art = srgb(texture2D(refMap, ruv).rgb); // the image is sRGB; lighting works in linear
          float facing = smoothstep(0.15, 0.5, abs(normalize(vObjN).x));
          float trusted = max(body + limb + mane + frill, 0.0) * (1.0 - smoothstep(690.0, 740.0, refX))
                        + wingb * (1.0 - smoothstep(800.0, 830.0, refX)) * step(0.55, vObj.y);
          float useArt = vProj * facing * trusted * step(0.0, ruv.y) * step(ruv.y, 1.0);
          vec3 col = mix(fill, art, useArt);
          if (debugGray > 0.5) col = vec3(0.5);
          diffuseColor.rgb = col;
          float rough = mix(0.62, 0.35, max(claw, horn));
          rough = mix(rough, 0.72, memb);
        `)
        .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\nroughnessFactor = rough;")
        .replace("#include <emissivemap_fragment>", `#include <emissivemap_fragment>
          // the art already has its own painted shading; lift it a little so lighting doesn't double it
          totalEmissiveRadiance += col * (0.08 * useArt + 0.2 * memb);`);
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

    const refTex = await new Promise((res, rej) => new THREE.TextureLoader().load(opts.refUrl, res, undefined, rej));
    refTex.encoding = THREE.sRGBEncoding; refTex.anisotropy = 8;
    const gltf = await new Promise((res, rej) => new THREE.GLTFLoader().load(opts.glbUrl, res, undefined, rej));
    let skinned = null;
    gltf.scene.traverse(o => { if (o.isSkinnedMesh) skinned = o; });
    skinned.material = clayMaterial(THREE, refTex);
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
