"""Clay's head as articulated parts, built in Blender from measured cross-sections.

Parts: rigid upper head (muzzle, brow, skull to the ear) carrying horns, eyes,
eyelids and ear frills; a lower jaw that hinges open; mouth interior, teeth and a
tongue on its own bone chain. Each skin is a clean quad loft (rings of points
along the head), so it has proper topology and natural texture coordinates.
Model space: x = Clay's left, y = up, z = forward; 1 unit = 343 px of the reference.
"""
import math
import sys

import bpy  # bmesh is only importable once bpy is loaded
import numpy as np

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
OUT = ARGS.get("--out", "head.glb")

# ---------------------------------------------------------------- measurements
# Upper head, nose to the back of the skull: z, top, lower edge (mouth line in front of
# the corner, cheek edge behind it), half-width of the top plane, half-width at the lip/cheek.
UPPER = np.array([
    [2.030, 1.465, 1.395, 0.058, 0.072],
    [2.005, 1.490, 1.385, 0.084, 0.104],
    [1.950, 1.520, 1.395, 0.099, 0.123],
    [1.900, 1.580, 1.410, 0.104, 0.133],
    [1.860, 1.660, 1.420, 0.110, 0.144],
    [1.820, 1.720, 1.430, 0.113, 0.153],
    [1.780, 1.770, 1.440, 0.117, 0.162],
    [1.740, 1.830, 1.455, 0.120, 0.177],
    [1.700, 1.860, 1.470, 0.123, 0.190],
    [1.650, 1.885, 1.485, 0.130, 0.201],
    [1.600, 1.890, 1.500, 0.136, 0.210],
    [1.550, 1.890, 1.520, 0.142, 0.218],
    [1.500, 1.885, 1.470, 0.146, 0.219],
    [1.450, 1.875, 1.440, 0.150, 0.215],
    [1.400, 1.860, 1.430, 0.155, 0.215],
    [1.340, 1.830, 1.450, 0.150, 0.200],
])
# Lower jaw, chin to hinge: z, top (mouth line), bottom, half-width.
JAW = np.array([
    [2.020, 1.383, 1.345, 0.067],
    [2.000, 1.380, 1.335, 0.095],
    [1.950, 1.390, 1.310, 0.112],
    [1.900, 1.403, 1.285, 0.122],
    [1.850, 1.413, 1.255, 0.132],
    [1.800, 1.428, 1.222, 0.141],
    [1.750, 1.443, 1.210, 0.149],
    [1.700, 1.458, 1.225, 0.156],
    [1.650, 1.473, 1.260, 0.162],
    [1.600, 1.488, 1.310, 0.168],
    [1.550, 1.498, 1.360, 0.167],
    [1.500, 1.488, 1.400, 0.161],
    [1.460, 1.478, 1.420, 0.151],
])
HINGE = (0.0, 1.47, 1.47)
EYE = dict(z=1.70, y=1.665, r=0.042)
# where the dark top plate's edge runs: height fraction of the side, nose -> back
VISOR = np.array([[2.03, 0.35], [1.90, 0.45], [1.78, 0.58], [1.70, 0.66], [1.60, 0.72], [1.45, 0.78], [1.34, 0.80]])
HORN = dict(path=[(0.10, 1.86, 1.62), (0.14, 2.08, 1.52), (0.18, 2.07, 1.22)], radius=(0.042, 0.026, 0.005), ring_every=0.06)
FRILL = [(0.20, 1.74, 1.45), (0.20, 1.60, 1.38), (0.25, 1.80, 1.29), (0.27, 1.90, 1.27)]  # base front, base low, outer low, tip

N_AROUND = 28  # points around the outer contour


def interp(table, z, col):
    zs = table[:, 0]
    return float(np.interp(-z, -zs, table[:, col]))


def upper_contour(z):
    """Outer contour of the upper head at z: from the left lip edge, over the top,
    to the right lip edge. Boxy: flat top, near-vertical sides, cheeks wider than the top."""
    top, low, wt, wb = (interp(UPPER, z, c) for c in (1, 2, 3, 4))
    b = top - low
    pts = []
    for i in range(N_AROUND + 1):
        th = math.pi * i / N_AROUND  # 0 = right lip, pi/2 = top, pi = left lip
        c, s = math.cos(th), math.sin(th)
        n = 3.6
        yy = b * abs(s) ** (2 / n)
        a = wb + (wt - wb) * (yy / b) ** 1.6
        x = a * math.copysign(abs(c) ** (2 / n), c)
        pts.append((x, low + yy))
    return pts, low


def jaw_contour(z):
    top, bot, w = (interp(JAW, z, c) for c in (1, 2, 3))
    b = top - bot
    pts = []
    for i in range(N_AROUND + 1):
        th = math.pi * i / N_AROUND  # 0 = right edge, pi/2 = chin bottom, pi = left edge
        c, s = math.cos(th), math.sin(th)
        n = 2.6
        x = w * math.copysign(abs(c) ** (2 / n), c)
        pts.append((x, top - b * abs(s) ** (2 / n)))
    return pts, top


def loft(contour_fn, zs, cap_front=True, cap_back=True):
    """Rings of the contour along z, closed across the open side (palate / mouth floor)
    and capped at both ends. Returns verts, quads, and per-vertex (along, around) coords."""
    verts, faces, uv = [], [], []
    rings = []
    for k, z in enumerate(zs):
        pts, edge_y = contour_fn(z)
        ring = []
        for i, (x, y) in enumerate(pts):
            ring.append(len(verts)); verts.append((x, y, z)); uv.append((z, i / N_AROUND))
        # inner (mouth-side) surface between the two lip edges, slightly recessed
        inner = []
        for j in range(1, 6):
            t = j / 6
            x = pts[-1][0] + (pts[0][0] - pts[-1][0]) * t
            inner.append(len(verts)); verts.append((x, edge_y, z)); uv.append((z, -1.0))
        rings.append(ring + inner)
    M = len(rings[0])
    for k in range(len(rings) - 1):
        a, b = rings[k], rings[k + 1]
        for i in range(M):
            j = (i + 1) % M
            faces.append([a[i], a[j], b[j], b[i]])
    for k, cap in ((0, cap_front), (len(rings) - 1, cap_back)):
        if not cap:
            continue
        r = rings[k]
        c = len(verts)
        cx = sum(verts[i][0] for i in r) / M; cy = sum(verts[i][1] for i in r) / M
        verts.append((cx, cy, zs[k] + (0.006 if k == 0 else -0.006))); uv.append((zs[k], 0.5))  # caps are outer skin
        for i in range(M):
            j = (i + 1) % M
            faces.append([r[j], r[i], c] if k == 0 else [r[i], r[j], c])
    return verts, faces, uv


def tube(path_pts, radii, segs=24, around=12, ring_every=None):
    q = lambda t: (1 - t) ** 2 * path_pts[0] + 2 * (1 - t) * t * path_pts[1] + t * t * path_pts[2]
    total = sum(np.linalg.norm(q((i + 1) / 40) - q(i / 40)) for i in range(40))
    verts, faces, uv = [], [], []
    for i in range(segs + 1):
        t = i / segs
        c = q(t); tan = q(min(1, t + 0.02)) - q(max(0, t - 0.02)); tan /= np.linalg.norm(tan)
        s = np.cross(tan, [1.0, 0, 0]); s /= np.linalg.norm(s); u = np.cross(s, tan)
        r = radii[0] + (radii[1] - radii[0]) * t * 2 if t < 0.5 else radii[1] + (radii[2] - radii[1]) * (t - 0.5) * 2
        ring = 0.0
        if ring_every:
            ring = 1.0 if math.cos(2 * math.pi * t * total / ring_every) > 0.7 else 0.0
        for k in range(around):
            a = 2 * math.pi * k / around
            verts.append(tuple(c + (s * math.cos(a) + u * math.sin(a)) * r * (1 + 0.07 * ring))); uv.append((t, ring))
    for i in range(segs):
        for k in range(around):
            a = i * around + k; b = i * around + (k + 1) % around
            faces.append([a, b, b + around, a + around])
    return verts, faces, uv


def sphere(c, r, lat=12, lon=18, theta_max=math.pi, up=(0, 1, 0)):
    up = np.array(up, float); up /= np.linalg.norm(up)
    a = np.cross(up, [0, 0, 1.0]) if abs(up[2]) < 0.9 else np.cross(up, [1.0, 0, 0]); a /= np.linalg.norm(a); b = np.cross(up, a)
    verts, faces, uv = [], [], []
    for i in range(lat + 1):
        th = theta_max * i / lat
        for j in range(lon):
            ph = 2 * math.pi * j / lon
            d = up * math.cos(th) + (a * math.cos(ph) + b * math.sin(ph)) * math.sin(th)
            verts.append(tuple(np.array(c) + d * r)); uv.append((th / math.pi, j / lon))
    for i in range(lat):
        for j in range(lon):
            p = i * lon + j; q = i * lon + (j + 1) % lon
            faces.append([p, q, q + lon, p + lon])
    return verts, faces, uv


# ---------------------------------------------------------------- Blender
def to_blender(p):
    p = np.asarray(p, float)
    return np.stack([p[..., 0], -p[..., 2], p[..., 1]], -1)


def add_part(name, verts, faces, attrs, bone_weights):
    me = bpy.data.meshes.new(name)
    me.from_pydata(to_blender(np.array(verts)).tolist(), [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    for an, vals in attrs.items():
        a = me.attributes.new(an, "FLOAT", "POINT"); a.data.foreach_set("value", np.asarray(vals, np.float32))
    for vi, wl in enumerate(bone_weights):
        for bone, w in wl:
            (ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)).add([vi], w, "ADD")
    return ob


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs = []

    # upper head skin: dense rings near the nose, where the shape changes fastest
    zs = np.concatenate([np.linspace(2.03, 1.90, 10), np.linspace(1.88, 1.34, 34)])
    v, f, uv = loft(upper_contour, zs)
    V = np.array(v)
    # brow shelf: push the edge of the top plate out over the eye
    zone = np.zeros(len(v)); hf = np.zeros(len(v))
    for i, (x, y, z) in enumerate(v):
        top, low = interp(UPPER, z, 1), interp(UPPER, z, 2)
        h = (y - low) / max(top - low, 1e-6); hf[i] = h
        vis = float(np.interp(-z, -VISOR[:, 0], VISOR[:, 1]))
        zone[i] = 1.0 if (uv[i][1] >= 0 and h > vis) else 0.0
        if uv[i][1] >= 0:
            # the brow juts out where the plate edge passes over the eye
            brow = math.exp(-((z - EYE["z"]) / 0.07) ** 2) * math.exp(-((h - vis) / 0.06) ** 2)
            V[i, 0] += math.copysign(0.03 * brow, x)
            # eye socket: a shallow dish around the eye
            d = math.hypot(y - EYE["y"], z - EYE["z"])
            V[i, 0] -= math.copysign(0.014 * math.exp(-(d / 0.05) ** 2), x)
            # nostrils: a dent on the top front corner
            dn = math.hypot(abs(x) - 0.038, z - 1.965)
            if h > 0.6:
                V[i, 1] -= 0.012 * math.exp(-(dn / 0.014) ** 2)
            # cheek crease from the mouth corner up toward the ear
    part = [1.0 if uv[i][1] >= 0 else 3.0 for i in range(len(v))]
    objs.append(add_part("UpperHead", V.tolist(), f, {"_PART": part, "_A": [u[0] for u in uv], "_B": hf, "_ZONE": zone},
                         [[("head", 1.0)]] * len(v)))

    # lower jaw skin
    zj = np.concatenate([np.linspace(2.02, 1.90, 8), np.linspace(1.88, 1.46, 24)])
    v, f, uv = loft(jaw_contour, zj)
    part = [2.0 if u[1] >= 0 else 3.0 for u in uv]
    objs.append(add_part("Jaw", v, f, {"_PART": part, "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                         [[("jaw", 1.0)]] * len(v)))

    # teeth: a row along each lip edge, fangs near the front
    for jaw_side, bone in ((False, "head"), (True, "jaw")):
        vs, fs, ws = [], [], []
        for sgn in (1, -1):
            for k, z in enumerate(np.linspace(1.98, 1.60, 9)):
                if jaw_side:
                    w, edge = interp(JAW, z, 3) - 0.018, interp(JAW, z, 1)
                else:
                    w, edge = interp(UPPER, z, 4) - 0.016, interp(UPPER, z, 2)
                length = 0.055 if k == 1 else 0.03 + 0.01 * (k % 2)
                base_r = 0.014 if k == 1 else 0.010
                tip = np.array([sgn * w, edge + (length if jaw_side else -length), z])
                base = np.array([sgn * w, edge, z])
                b0 = len(vs)
                for j in range(6):
                    a = 2 * math.pi * j / 6
                    vs.append(tuple(base + np.array([math.cos(a) * base_r, 0, math.sin(a) * base_r])))
                vs.append(tuple(tip))
                for j in range(6):
                    fs.append([b0 + j, b0 + (j + 1) % 6, b0 + 6])
                ws += [[(bone, 1.0)]] * 7
        objs.append(add_part("Teeth" + ("Lower" if jaw_side else "Upper"), vs, fs, {"_PART": [4] * len(vs), "_A": [0] * len(vs), "_B": [0] * len(vs), "_ZONE": [0] * len(vs)}, ws))

    # tongue: a flattened loft lying on the floor of the mouth, on three bones
    def tongue_contour(z):
        t = (1.93 - z) / (1.93 - 1.56)
        w = 0.055 * min(1, 0.4 + t * 1.5)
        y0 = interp(JAW, z, 1) - 0.004
        pts = []
        for i in range(N_AROUND + 1):
            th = math.pi * i / N_AROUND
            pts.append((w * math.cos(th), y0 + 0.022 * math.sin(th) ** 0.7))
        return pts, y0
    zt = np.linspace(1.93, 1.56, 16)
    v, f, uv = loft(tongue_contour, zt)
    tw = []
    for (x, y, z) in v:
        t = (1.93 - z) / 0.37
        tw.append([("tongue3", max(0, 1 - t * 3)), ("tongue2", max(0, 1 - abs(t - 0.5) * 3)), ("tongue1", max(0, t * 3 - 2) + 1e-3)])
    objs.append(add_part("Tongue", v, f, {"_PART": [5] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, tw))

    for sgn in (1, -1):
        # eye: find the head surface beside the eye and sink the eyeball into it
        pts, _ = upper_contour(EYE["z"])
        top, low = interp(UPPER, EYE["z"], 1), interp(UPPER, EYE["z"], 2)
        sx = max(abs(x) for x, y in pts if abs(y - EYE["y"]) < 0.03)
        c = (sgn * (sx - EYE["r"] * 0.65), EYE["y"], EYE["z"])
        look = (sgn * 0.85, 0.05, 0.52)
        v, f, uv = sphere(c, EYE["r"], up=look)
        objs.append(add_part("Eye" + ("L" if sgn > 0 else "R"), v, f, {"_PART": [6] * len(v), "_A": [u[0] for u in uv], "_B": [0] * len(v), "_ZONE": [0] * len(v)},
                             [[("head", 1.0)]] * len(v)))
        # eyelids: an upper and a lower shell around the eyeball
        for lid, up, cover in (("Upper", (sgn * 0.45, 1, 0.15), 1.25), ("Lower", (sgn * 0.35, -1, 0.1), 0.8)):
            v, f, uv = sphere(c, EYE["r"] * 1.12, lat=8, lon=18, theta_max=cover, up=up)
            objs.append(add_part(f"Lid{lid}{'L' if sgn > 0 else 'R'}", v, f, {"_PART": [7] * len(v), "_A": [u[0] for u in uv], "_B": [0] * len(v), "_ZONE": [0] * len(v)},
                                 [[("head", 1.0)]] * len(v)))
        # horn: ridged, arcing up and back
        pp = [np.array([sgn * p[0], p[1], p[2]]) for p in HORN["path"]]
        v, f, uv = tube(pp, HORN["radius"], segs=30, around=12, ring_every=HORN["ring_every"])
        objs.append(add_part("Horn" + ("L" if sgn > 0 else "R"), v, f, {"_PART": [8] * len(v), "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                             [[("head", 1.0)]] * len(v)))
        # ear frill: a rounded, ribbed fin with a little thickness, fanning up and back from its base
        base = np.array([sgn * 0.20, 1.68, 1.42]); up_ = np.array([sgn * 0.35, 0.75, -0.55]); up_ /= np.linalg.norm(up_)
        fwd = np.array([0, 0.35, 1.0]); fwd = fwd - up_ * (fwd @ up_); fwd /= np.linalg.norm(fwd)
        nrm = np.cross(up_, fwd); nrm /= np.linalg.norm(nrm)
        G = 10; vs, fs, us, bs = [], [], [], []
        for side in (1, -1):
            b0 = len(vs)
            for i in range(G + 1):          # i: base -> tip
                for j in range(G + 1):      # j: across the fin
                    a, b = i / G, j / G - 0.5
                    width = 0.11 * math.sin(math.pi * min(1, 0.15 + a * 0.85)) * (1 - 0.35 * a)
                    length = 0.19 * (1 - (2 * b) ** 2 * 0.35)
                    p = base + up_ * a * length + fwd * b * width
                    rib = math.cos((b + 0.5) * 3 * 2 * math.pi) * 0.5 + 0.5
                    p = p + nrm * side * (0.005 + 0.003 * rib) * (1 - 0.7 * a)
                    vs.append(tuple(p)); us.append(a); bs.append(b + 0.5)
            for i in range(G):
                for j in range(G):
                    a = b0 + i * (G + 1) + j
                    fs.append([a, a + G + 1, a + G + 2, a + 1] if side > 0 else [a, a + 1, a + G + 2, a + G + 1])
        objs.append(add_part("Frill" + ("L" if sgn > 0 else "R"), vs, fs, {"_PART": [9] * len(vs), "_A": us, "_B": bs, "_ZONE": [0] * len(vs)},
                             [[("head", 1.0)]] * len(vs)))

    # armature: neck stub, head, jaw hinge, tongue chain
    arm_data = bpy.data.armatures.new("HeadRig"); arm = bpy.data.objects.new("HeadRig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    def bone(name, head, tail, parent=None):
        b = arm_data.edit_bones.new(name); b.head = to_blender(head).tolist(); b.tail = to_blender(tail).tolist()
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b
    bone("neck3", (0, 1.30, 1.10), (0, 1.57, 1.36))
    bone("head", (0, 1.57, 1.36), (0, 1.45, 2.02), "neck3")
    bone("jaw", HINGE, (0, 1.33, 2.0), "head")
    bone("tongue1", (0, 1.44, 1.58), (0, 1.41, 1.70), "jaw")
    bone("tongue2", (0, 1.41, 1.70), (0, 1.40, 1.82), "tongue1")
    bone("tongue3", (0, 1.40, 1.82), (0, 1.39, 1.93), "tongue2")
    bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    head = objs[0]
    mod = head.modifiers.new("Armature", "ARMATURE"); mod.object = arm
    head.parent = arm
    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True); arm.select_set(True)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True, export_attributes=True,
                              export_yup=True, export_animations=False, export_materials="NONE")
    print(f"exported {OUT}: {len(head.data.vertices)} verts, {len(head.data.polygons)} faces")


main()
