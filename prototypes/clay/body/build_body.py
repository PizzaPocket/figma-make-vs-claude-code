"""Clay, head and body, built in Blender from measured data, exported as one rigged .glb.

The head comes from ../head/build_head.py. The body is built here, element by element (see
body_design.json and body_sheets.md):
- trunk: neck, torso and tail as one loft along a curved spine, with cross-sections perpendicular
  to it, skinned to a chain of spine bones;
- front legs: upper arm, forearm and compact hand as one loft along the limb, with toes, hooked
  claws and a dewclaw; the shoulder is sculpted into the trunk;
- hind legs: thigh and shin as one loft, the long digitigrade foot as another, four splayed toes,
  a heel spur and studs along the top of the foot.
Model space: x = Clay's left, y = up, z = forward; 1 unit = 343 px of the reference.

    python3 build_body.py --out clay.glb
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "head"))
import build_head as H  # noqa: E402  (also imports bpy)
import bpy  # noqa: E402
import numpy as np  # noqa: E402

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
OUT = ARGS.get("--out", "clay.glb")
B = json.load(open(ARGS.get("--body", os.path.join(HERE, "body_design.json"))))
TR = B["trunk"]


def table(rows, s, col=1):
    rows = np.array(rows, float)
    return float(np.interp(s, rows[:, 0], rows[:, col]))


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- trunk
def trunk_frames(step=0.01):
    """Spine points (bind pose), depths, and a parallel-transported frame (dorsal normal N, side B)."""
    st = np.array(TR["stations"], float)
    s_all = np.arange(-TR["front_overlap"], st[-1, 0] + 1e-9, step)
    pose = TR["tail_pose"]
    P, DU, DV = [], [], []
    for s in s_all:
        sc = max(s, 0.0)
        z, y, du, dv = (table(st, sc, c) for c in (1, 2, 3, 4))
        if s < 0:  # run on into the head along the first tangent, so the join is hidden inside it
            z1, y1 = table(st, 0.02, 1), table(st, 0.02, 2)
            z, y = z + (z - z1) / 0.02 * (-s), y + (y - y1) / 0.02 * (-s)
        lift = max(0.0, pose["ground_y"] + dv - y) * smoothstep(pose["ground_from_s"] - 0.4, pose["ground_from_s"], sc)
        x = pose["curl_x"] * smoothstep(pose["curl_from_s"], st[-1, 0], sc) ** 1.5
        P.append((x, y + lift, z)); DU.append(du); DV.append(dv)
    P = np.array(P)
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    N = []
    n = np.array([0, 1.0, 0]); n = H.norm(n - T[0] * (n @ T[0]))
    for i in range(len(P)):
        if i:
            n = H.norm(n - T[i] * (n @ T[i]))
        N.append(n)
    N = np.array(N); Bv = np.cross(T, N)
    if Bv[0, 0] < 0:
        Bv = -Bv
    return s_all, P, np.array(DU), np.array(DV), N, Bv


def px_to_model(pts):
    return [((700 - px) / 343, (830 - py) / 343) for px, py in pts]


def poly_sdist(z, y, poly):
    """Signed side-view distance to a closed polygon (negative inside)."""
    inside, best = False, 1e9
    n = len(poly)
    for i in range(n):
        (az, ay), (bz, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y) and z < (bz - az) * (y - ay) / (by - ay) + az:
            inside = not inside
        dz, dy = bz - az, by - ay
        t = max(0.0, min(1.0, ((z - az) * dz + (y - ay) * dy) / (dz * dz + dy * dy + 1e-12)))
        best = min(best, math.hypot(z - az - t * dz, y - ay - t * dy))
    return -best if inside else best


_ZONES = {}


def zone_value(s, f, z=None, y=None):
    """0 dark back, 0.5 orange side, 1 cream underside. On the neck and torso the edges are the measured
    side-view lines (zones.dark_edge_px, zones.cream_edge_px); on the tail, a side fraction f."""
    Zd = TR["zones"]
    if not _ZONES:
        _ZONES["dark"] = px_to_model(Zd["dark_region_px"]); _ZONES["cream"] = px_to_model(Zd["cream_region_px"])
    rows = Zd["rows"]
    fd, fc = table(rows, s, 1), table(rows, s, 2)
    by_fraction = 0.5 * smoothstep(fd - 0.015, fd + 0.015, f) + 0.5 * smoothstep(fc - 0.015, fc + 0.015, f)
    if z is None:
        return by_fraction
    w = 0.012
    dark = 1 - smoothstep(-w, w, poly_sdist(z, y, _ZONES["dark"]))
    cream = 1 - smoothstep(-w, w, poly_sdist(z, y, _ZONES["cream"]))
    by_lines = 0.5 * (1 - dark) + 0.5 * cream * (1 - dark)
    t = smoothstep(Zd["lines_until_s"] - 0.15, Zd["lines_until_s"] + 0.15, s)
    return by_lines * (1 - t) + by_fraction * t


def trunk_bones():
    """Spine bones (name, head, tail, parent) and, per bone, its s range."""
    s_all, P, *_ = trunk_frames()
    at = lambda s: tuple(P[int(np.argmin(abs(s_all - s)))])
    bones, ranges = [], []
    parent = None
    for name, s0, s1 in TR["bones"]["chain_forward"]:
        bones.append((name, at(s0), at(s1), parent)); ranges.append((name, min(s0, s1), max(s0, s1)))
        parent = name
    t0, n = TR["bones"]["tail_from"], TR["bones"]["tail_count"]
    t1 = TR["stations"][-1][0]
    edges = [t0 + (t1 - t0) * (k / n) ** 0.85 for k in range(n + 1)]  # shorter segments toward the tip
    parent = TR["bones"]["chain_forward"][0][0]
    for k in range(n):
        name = f"tail{k + 1}"
        bones.append((name, at(edges[k]), at(edges[k + 1]), parent)); ranges.append((name, edges[k], edges[k + 1]))
        parent = name
    return bones, ranges


def trunk_weights(s, ranges, blend=0.05):
    """Weights of the spine bones at s: the bone whose range holds s, blended with its neighbour near the joint."""
    ranges = sorted(ranges, key=lambda r: r[1])
    for i, (name, a, b) in enumerate(ranges):
        if a <= s <= b or (i == 0 and s < a) or (i == len(ranges) - 1 and s > b):
            w = [(name, 1.0)]
            if i + 1 < len(ranges) and s > b - blend:
                t = 0.5 * smoothstep(b - blend, b + blend, s); w = [(name, 1 - t), (ranges[i + 1][0], t)]
            elif i > 0 and s < a + blend:
                t = 0.5 * (1 - smoothstep(a - blend, a + blend, s)); w = [(name, 1 - t), (ranges[i - 1][0], t)]
            return w
    return [(ranges[-1][0], 1.0)]


def sculpt_trunk(q, centre, zone):
    """Muscle masses swelling the trunk (mirrored left/right), and colour patches painted over them."""
    sgn = 1.0 if q[0] >= 0 else -1.0
    for m in TR["sculpt"]["masses"]:
        c = np.array([sgn * m["centre"][0], m["centre"][1], m["centre"][2]])
        w = math.exp(-float(np.sum(((q - c) / np.array(m["radii"])) ** 2)))
        out = q - centre; out = out / (np.linalg.norm(out) + 1e-9)
        q = q + out * m["amount"] * w
    for pt in TR["sculpt"]["patches"]:
        if abs(q[0]) < pt["x_min"]:
            continue
        (cz, cy), (rz, ry) = pt["centre_zy"], pt["radii"]
        e = math.hypot((q[2] - cz) / rz, (q[1] - cy) / ry)
        zone = zone + (pt["zone"] - zone) * (1 - smoothstep(0.95, 1.05, e))
    return q, zone


def trunk_part(ranges, around=72):
    s_all, P, DU, DV, N, Bv = trunk_frames()
    verts, faces, A, Bf, Z, W = [], [], [], [], [], []
    for i, s in enumerate(s_all):
        sc = max(s, 0.0)
        nsq = table(TR["squareness"], sc)
        wf = table(TR["width"]["factor"], sc) * (DU[i] + DV[i]) / 2
        taper = 1.0 if i < len(s_all) - 1 else 0.0  # close the tail tip
        for k in range(around):
            th = 2 * math.pi * k / around  # 0 dorsal, pi ventral, pi/2 Clay's left
            c, sn = math.cos(th), math.sin(th)
            v = (DU[i] if c > 0 else DV[i]) * math.copysign(abs(c) ** (2 / nsq), c)
            w = wf * math.copysign(abs(sn) ** (2 / nsq), sn)
            q = P[i] + (N[i] * v + Bv[i] * w) * taper
            q, zv = sculpt_trunk(q, P[i], zone_value(sc, (1 - c) / 2, q[2], q[1]))
            verts.append(tuple(q))
            A.append(sc); Bf.append((1 - c) / 2); Z.append(zv); W.append(trunk_weights(sc, ranges))
    for i in range(len(s_all) - 1):
        for k in range(around):
            a = i * around + k; b = i * around + (k + 1) % around
            faces.append([a, a + around, b + around, b])
    return H.add_part("Trunk", verts, faces, {"_PART": [20] * len(verts), "_A": A, "_B": Bf, "_ZONE": Z}, W)


# ---------------------------------------------------------------- limbs
def limb_frames(path, radii, step=0.004):
    """Points along a limb spline, with N lateral (toward Clay's outside) and Bk pointing to the limb's back."""
    C, R, sl, _, _ = H.spline_frames(path, radii, step)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    side = math.copysign(1.0, C[0][0])
    N, Bk = [], []
    for t in T:
        n = H.norm(np.array([side, 0, 0]) - t * (t[0] * side))
        b = np.cross(t, n)
        if b[2] > 0:  # make it point backward (-z)
            b = -b
        N.append(n); Bk.append(b)
    return C, R, sl / sl[-1], np.array(N), np.array(Bk), sl[-1]


def nearest_t(C, tl, p):
    return float(tl[int(np.argmin(np.linalg.norm(C - np.asarray(p), axis=1)))])


def limb_weights(t, marks, blend=0.06):
    """marks: [(bone, t_start)] in order; blend the two bones at each joint."""
    for k in range(len(marks)):
        name, t0 = marks[k]
        t1 = marks[k + 1][1] if k + 1 < len(marks) else 1.01
        if t0 <= t < t1 or (k == 0 and t < t0):
            if k + 1 < len(marks) and t > t1 - blend:
                u = 0.5 * smoothstep(t1 - blend, t1 + blend, t); return [(name, 1 - u), (marks[k + 1][0], u)]
            if k > 0 and t < t0 + blend:
                u = 0.5 * (1 - smoothstep(t0 - blend, t0 + blend, t)); return [(name, 1 - u), (marks[k - 1][0], u)]
            return [(name, 1.0)]
    return [(marks[-1][0], 1.0)]


def mirror(p, sgn):
    return np.array([sgn * p[0], p[1], p[2]])


def claw_tube(base, direction, length, radius, hook_deg, down=np.array([0, -1.0, 0])):
    """A hooked claw: a tapering tube that curls down by hook_deg over its length."""
    d0 = H.norm(direction)
    axis = H.norm(np.cross(d0, down)) if abs(d0 @ down) < 0.99 else np.array([1.0, 0, 0])
    pts = [np.asarray(base, float)]
    p, d = np.asarray(base, float), d0
    for k in range(6):
        p = p + d * length / 6
        d = H.rot(d, axis, -math.radians(hook_deg) / 6)
        pts.append(p)
    v, f, A, Bq = H.tube(pts, [radius, radius * 0.8, radius * 0.6, radius * 0.45, radius * 0.3, radius * 0.15, 0.002], around=10, step=0.004)
    return v, f


def limb_loft(name, path, radii, aspect, cream, marks, root, sgn, around=40):
    """A limb segment as a loft along its spline. marks: [(bone, point)] where each bone starts; the
    first vertices blend into `root`. cream: {from, to, width} cream along the limb's back."""
    C, R, tl, N, Bk, length = limb_frames(path, radii)
    mk = [(bn, 0.0 if k == 0 else nearest_t(C, tl, pt)) for k, (bn, pt) in enumerate(marks)]
    asp = np.interp(tl, np.linspace(0, 1, len(aspect)), aspect)
    verts, faces, A, Bf, Z, W = [], [], [], [], [], []
    for i in range(len(C)):
        for k in range(around):
            th = 2 * math.pi * k / around  # 0 outside, pi/2 back, pi inside, 3pi/2 front
            verts.append(tuple(C[i] + (N[i] * math.cos(th) * asp[i] + Bk[i] * math.sin(th)) * R[i]))
            cr = 0.0
            if cream:
                cr = smoothstep(cream["from"] - 0.05, cream["from"] + 0.05, tl[i]) * (1 - smoothstep(cream["to"] - 0.05, cream["to"] + 0.05, tl[i])) \
                    * smoothstep(1 - cream["width"], 1 - cream["width"] + 0.15, max(0.0, math.sin(th)))
            A.append(tl[i] * length); Bf.append((th if th < math.pi else th - 2 * math.pi) * R[i]); Z.append(cr)  # along/around the limb in model units; the wrap falls on the hidden inside
            if root and tl[i] < 0.08:  # the root blends into the body
                W.append([(mk[0][0], 0.5 + 0.5 * tl[i] / 0.08), (root, 0.5 - 0.5 * tl[i] / 0.08)])
            else:
                W.append(limb_weights(tl[i], mk))
    for i in range(len(C) - 1):
        for k in range(around):
            a = i * around + k; b = i * around + (k + 1) % around
            faces.append([a, b, b + around, a + around] if sgn > 0 else [a, a + around, b + around, b])
    c0, c1 = len(verts), len(verts) + 1
    verts += [tuple(C[0]), tuple(C[-1])]; A += [0, 1]; Bf += [0, 0]; Z += [0, 0]; W += [[(mk[0][0], 1.0)], [(mk[-1][0], 1.0)]]
    for k in range(around):
        a = k; b = (k + 1) % around
        faces.append([b, a, c0]); faces.append([(len(C) - 1) * around + a, (len(C) - 1) * around + b, c1])
    return H.add_part(name, verts, faces, {"_PART": [21] * len(verts), "_A": A, "_B": Bf, "_ZONE": Z}, W)


def toes(kn, back, T, sgn, parent, prefix, sd):
    """Toes with hooked claws, fanned forward from the knuckle line. back: the point behind (wrist or heel)."""
    fwd = H.norm(kn - back); fwd[1] = 0; fwd = H.norm(fwd)
    parts, bones = [], []
    for k in range(T["count"]):
        d = H.rot(fwd, np.array([0, 1.0, 0]), math.radians(T["spread_deg"][k]) * sgn)
        side = H.norm(np.cross(d, [0, 1.0, 0]))
        base = kn + np.array([sgn * T["base_offset_x"][k], 0, 0]) - fwd * 0.02
        pts, p, segs = [base], base, T["segments"]
        for j, sl in enumerate(segs):
            dd = H.rot(d, side, -math.radians(T["drop_deg"][j]))
            p = p + dd * sl; pts.append(p)
        bn = f"{prefix}{k + 1}.{sd}"
        rads = list(T["radius"]) + [T["radius"][-1] * 0.9]
        v, f, _, _ = H.tube(pts, rads[:len(pts)], around=12, step=0.004)
        parts.append(H.add_part(f"{prefix}{k}{sd}", v, f, {"_PART": [21] * len(v), "_A": [0.97] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(bn, 1.0)]] * len(v)))
        cl = T["claw"]
        v, f = claw_tube(p - dd * 0.01, dd, cl["length"], cl["radius"], cl["hook_deg"])
        parts.append(H.add_part(f"{prefix}Claw{k}{sd}", v, f, {"_PART": [23] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(bn, 1.0)]] * len(v)))
        bones.append((bn, tuple(base), tuple(p), parent))
    return parts, bones


def front_leg(sgn):
    """One front leg (sgn +1 left, -1 right): parts and bones."""
    L = B["front_leg"]; sd = "L" if sgn > 0 else "R"
    J = {k: mirror(v, sgn) for k, v in L["joints"].items()}
    marks = [(f"upperarm.{sd}", J["shoulder"]), (f"forearm.{sd}", J["elbow"]), (f"hand.{sd}", J["wrist"])]
    parts = [limb_loft(f"FrontLeg{sd}", [mirror(p, sgn) for p in L["path"]], L["radius"], L["aspect"], L["cream_back"], marks, "chest", sgn)]
    bones = [(f"upperarm.{sd}", tuple(J["shoulder"]), tuple(J["elbow"]), "chest"),
             (f"forearm.{sd}", tuple(J["elbow"]), tuple(J["wrist"]), f"upperarm.{sd}"),
             (f"hand.{sd}", tuple(J["wrist"]), tuple(J["knuckles"]), f"forearm.{sd}")]
    tp, tb = toes(J["knuckles"], J["wrist"], L["toes"], sgn, f"hand.{sd}", "ftoe", sd)
    parts += tp; bones += tb
    dc = L["dewclaw"]
    v, f = claw_tube(mirror(dc["at"], sgn), mirror(dc["direction"], sgn), dc["length"], dc["radius"], 60)
    parts.append(H.add_part(f"Dewclaw{sd}", v, f, {"_PART": [23] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(f"forearm.{sd}", 1.0)]] * len(v)))
    return parts, bones


def hind_leg(sgn):
    """One hind leg: thigh, shin and the long digitigrade foot (its own loft, since the leg folds back on
    itself at the heel), four splayed toes, a heel spur, and studs along the top of the foot."""
    L = B["hind_leg"]; sd = "L" if sgn > 0 else "R"
    J = {k: mirror(v, sgn) for k, v in L["joints"].items()}
    parts = [limb_loft(f"HindLeg{sd}", [mirror(p, sgn) for p in L["leg_path"]], L["leg_radius"], L["leg_aspect"], L["cream_back"],
                       [(f"thigh.{sd}", J["hip"]), (f"shin.{sd}", J["knee"])], "hips", sgn),
             limb_loft(f"HindFoot{sd}", [mirror(p, sgn) for p in L["foot_path"]], L["foot_radius"], L["foot_aspect"], None,
                       [(f"foot.{sd}", J["heel"])], None, sgn)]
    bones = [(f"thigh.{sd}", tuple(J["hip"]), tuple(J["knee"]), "hips"),
             (f"shin.{sd}", tuple(J["knee"]), tuple(J["heel"]), f"thigh.{sd}"),
             (f"foot.{sd}", tuple(J["heel"]), tuple(J["ball"]), f"shin.{sd}")]
    tp, tb = toes(J["ball"], J["heel"], L["toes"], sgn, f"foot.{sd}", "htoe", sd)
    parts += tp; bones += tb
    sp = L["spur"]
    v, f = claw_tube(mirror(sp["at"], sgn), mirror(sp["direction"], sgn), sp["length"], sp["radius"], 40)
    parts.append(H.add_part(f"Spur{sd}", v, f, {"_PART": [23] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(f"foot.{sd}", 1.0)]] * len(v)))
    # studs: dark square plates along the top of the foot
    st = L["studs"]; heel, ball = J["heel"], J["ball"]
    for k in range(st["count"]):
        t = (k + 0.5) / st["count"]
        c = heel + (ball - heel) * t + np.array([0, st["lift"], 0])
        v, f, uv = H.sphere(c, 1.0, lat=6, lon=8)
        v = [tuple(c + (np.array(q) - c) * np.array(st["size"])) for q in v]
        parts.append(H.add_part(f"Stud{k}{sd}", v, f, {"_PART": [22] * len(v), "_A": [0.5] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(f"foot.{sd}", 1.0)]] * len(v)))
    return parts, bones


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tb, ranges = trunk_bones()
    objs, head_bones = H.head_parts()
    objs.append(trunk_part(ranges))
    neck_end = TR["bones"]["chain_forward"][-1][0]
    bones = tb + [(n, h, t, p or neck_end) for n, h, t, p in head_bones]
    for sgn in (1, -1):
        for leg in (front_leg, hind_leg):
            parts, lb = leg(sgn)
            objs += parts; bones += lb
    H.assemble(objs, bones, OUT, "ClayRig")


if __name__ == "__main__":
    main()
