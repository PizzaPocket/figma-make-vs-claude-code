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

# ---------------------------------------------------------------- measurements (head_design.json)
import json
import os
D = json.load(open(ARGS.get("--design", os.path.join(os.path.dirname(os.path.abspath(__file__)), "head_design.json"))))
UPPER = np.array(D["upper_head"]["rows"])
JAW = np.array(D["lower_jaw"]["rows"])
HINGE = tuple(D["lower_jaw"]["hinge"])
EYE = dict(z=D["eye"]["centre_zy"][0], y=D["eye"]["centre_zy"][1], r=D["eye"]["radius"])
PLATE_EDGE = np.array(D["dark_plate_edge"]["zy"])
HORN = D["horn"]
FRILL = D["ear_frill"]


def seg_dist(z, y, pts):
    """Distance in the side view (z, y) from a point to a polyline."""
    best = 1e9
    for (az, ay), (bz, by) in zip(pts[:-1], pts[1:]):
        dz, dy = bz - az, by - ay
        t = max(0.0, min(1.0, ((z - az) * dz + (y - ay) * dy) / (dz * dz + dy * dy)))
        best = min(best, math.hypot(z - az - t * dz, y - ay - t * dy))
    return best


def brush_offset(z, y):
    """Outward (+) / inward (-) offset of the side surface from the sculpt brushes."""
    off = 0.0
    for b in D["brushes"]:
        if b["kind"] == "dent":
            d = math.hypot(z - b["zy"][0], y - b["zy"][1])
            off -= b["depth"] * math.exp(-(d / b["radius"]) ** 2)
        else:
            d = seg_dist(z, y, b["zy"])
            amt = b["height"] if b["kind"] == "ridge" else -b["depth"]
            off += amt * math.exp(-(d / b["width"]) ** 2)
    return off


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
        n = D["upper_head"].get("squareness", 3.6)  # higher = crisper edge between top and side planes
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
    z0, z1 = UPPER[0, 0], UPPER[-1, 0]
    zs = np.concatenate([np.linspace(z0, 1.86, 14), np.linspace(1.85, z1, 34)])
    v, f, uv = loft(upper_contour, zs)
    V = np.array(v)
    zone = np.full(len(v), -1.0); hf = np.zeros(len(v))  # underside: below the plate
    for i, (x, y, z) in enumerate(v):
        top, low, wb = interp(UPPER, z, 1), interp(UPPER, z, 2), interp(UPPER, z, 4)
        hf[i] = (y - low) / max(top - low, 1e-6)
        if uv[i][1] < 0:
            continue
        edge_y = float(np.interp(-z, -PLATE_EDGE[:, 0], PLATE_EDGE[:, 1]))
        zone[i] = y - edge_y  # signed height above the plate edge; interpolates to a clean line in the shader
        # brushes act on the sides of the head (fading out toward the top and the lip)
        side = min(1.0, max(0.0, (abs(x) / wb - 0.35) / 0.4))
        V[i, 0] += math.copysign(brush_offset(z, y) * side, x)
    # the closed underside in front of the jaw is the overhanging upper lip (skin), not the palate
    part = [1.0 if uv[i][1] >= 0 or v[i][2] > JAW[0, 0] - 0.01 else 3.0 for i in range(len(v))]
    objs.append(add_part("UpperHead", V.tolist(), f, {"_PART": part, "_A": [u[0] for u in uv], "_B": hf, "_ZONE": zone},
                         [[("head", 1.0)]] * len(v)))

    # lower jaw skin
    zj = np.concatenate([np.linspace(JAW[0, 0], 1.80, 10), np.linspace(1.79, JAW[-1, 0], 24)])
    v, f, uv = loft(jaw_contour, zj)
    part = [2.0 if u[1] >= 0 else 3.0 for u in uv]
    objs.append(add_part("Jaw", v, f, {"_PART": part, "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                         [[("jaw", 1.0)]] * len(v)))

    # teeth: a row along each lip edge, fangs near the front
    for jaw_side, bone in ((False, "head"), (True, "jaw")):
        vs, fs, ws = [], [], []
        for sgn in (1, -1):
            for k, z in enumerate(np.linspace(1.86, 1.62, 8)):
                if jaw_side:
                    w, edge = interp(JAW, z, 3) - 0.018, interp(JAW, z, 1)
                else:
                    w, edge = interp(JAW, z, 3) + 0.004, interp(UPPER, z, 2)
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
        t = (1.84 - z) / (1.84 - 1.56)
        w = 0.055 * min(1, 0.4 + t * 1.5)
        y0 = interp(JAW, z, 1) - 0.004
        pts = []
        for i in range(N_AROUND + 1):
            th = math.pi * i / N_AROUND
            pts.append((w * math.cos(th), y0 + 0.022 * math.sin(th) ** 0.7))
        return pts, y0
    zt = np.linspace(1.84, 1.56, 16)
    v, f, uv = loft(tongue_contour, zt)
    tw = []
    for (x, y, z) in v:
        t = (1.84 - z) / 0.28
        tw.append([("tongue3", max(0, 1 - t * 3)), ("tongue2", max(0, 1 - abs(t - 0.5) * 3)), ("tongue1", max(0, t * 3 - 2) + 1e-3)])
    objs.append(add_part("Tongue", v, f, {"_PART": [5] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, tw))

    for sgn in (1, -1):
        # eye: find the head surface beside the eye and sink the eyeball into it
        pts, _ = upper_contour(EYE["z"])
        top, low = interp(UPPER, EYE["z"], 1), interp(UPPER, EYE["z"], 2)
        sx = max(abs(x) for x, y in pts if abs(y - EYE["y"]) < 0.03)
        c = (sgn * (sx - EYE["r"] * 0.55), EYE["y"], EYE["z"])
        g = D["eye"]["gaze"]; look = (sgn * g[0], g[1], g[2])
        v, f, uv = sphere(c, EYE["r"], up=look)
        objs.append(add_part("Eye" + ("L" if sgn > 0 else "R"), v, f, {"_PART": [6] * len(v), "_A": [u[0] for u in uv], "_B": [0] * len(v), "_ZONE": [0] * len(v)},
                             [[("head", 1.0)]] * len(v)))
        # eyelids: an upper and a lower shell around the eyeball
        for lid, up, cover in (("Upper", (sgn * 0.45, 1, 0.15), D["eye"]["upper_lid_cover"]), ("Lower", (sgn * 0.35, -1, 0.1), D["eye"]["lower_lid_cover"])):
            v, f, uv = sphere(c, EYE["r"] * 1.12, lat=8, lon=18, theta_max=cover, up=up)
            objs.append(add_part(f"Lid{lid}{'L' if sgn > 0 else 'R'}", v, f, {"_PART": [7] * len(v), "_A": [u[0] for u in uv], "_B": [0] * len(v), "_ZONE": [0] * len(v)},
                                 [[("head", 1.0)]] * len(v)))
        # horn: ridged, arcing up and back
        pp = [np.array([sgn * p[0], p[1], p[2]]) for p in HORN["path"]]
        v, f, uv = tube(pp, HORN["radius"], segs=36, around=12, ring_every=HORN["ring_every"])
        objs.append(add_part("Horn" + ("L" if sgn > 0 else "R"), v, f, {"_PART": [8] * len(v), "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                             [[("head", 1.0)]] * len(v)))
        # ear frill: a leaf-shaped fin from base to tip; its front edge rolls over like a horse's ear
        base = np.array([sgn * FRILL["base"][0], FRILL["base"][1], FRILL["base"][2]])
        tipp = np.array([sgn * FRILL["tip"][0], FRILL["tip"][1], FRILL["tip"][2]])
        up_ = tipp - base; length = np.linalg.norm(up_); up_ /= length
        fwd = np.array([0, 0.3, 1.0]); fwd = fwd - up_ * (fwd @ up_); fwd /= np.linalg.norm(fwd)
        nrm = np.cross(up_, fwd); nrm /= np.linalg.norm(nrm)
        if nrm[0] * sgn < 0:
            nrm = -nrm
        G = 12; vs, fs, us, bs = [], [], [], []
        for side in (1, -1):
            b0 = len(vs)
            for i in range(G + 1):          # base -> tip
                for j in range(G + 1):      # front edge -> back edge
                    a, b = i / G, j / G
                    width = FRILL["width"] * math.sin(math.pi * min(1.0, 0.12 + a * 0.88)) ** 0.8
                    p = base + up_ * a * length * (1 - 0.25 * (2 * b - 1) ** 2) + fwd * (0.5 - b) * width
                    curl = FRILL["rolled_front_edge"] * max(0.0, 1 - b / 0.3) ** 2 * math.sin(math.pi * min(1.0, a * 1.1))
                    rib = math.cos(b * FRILL["ribs"] * 2 * math.pi) * 0.5 + 0.5
                    p = p + nrm * (curl + side * (0.004 + 0.003 * rib) * (1 - 0.6 * a))
                    vs.append(tuple(p)); us.append(a); bs.append(b)
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
    bone("head", (0, 1.57, 1.36), (0, 1.44, 2.017), "neck3")
    bone("jaw", HINGE, (0, 1.24, 1.86), "head")
    bone("tongue1", (0, 1.42, 1.56), (0, 1.38, 1.66), "jaw")
    bone("tongue2", (0, 1.38, 1.66), (0, 1.34, 1.75), "tongue1")
    bone("tongue3", (0, 1.34, 1.75), (0, 1.31, 1.84), "tongue2")
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
