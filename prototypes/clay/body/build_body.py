"""Clay, head and body, built in Blender from measured data, exported as one rigged .glb.

The head comes from ../head/build_head.py. The body is built here, element by element (see
body_design.json and body_sheets.md):
- skin (skin.py): one surface over the trunk (neck, torso and tail, measured cross-sections along a
  curved spine), the limb bones and the muscles that work them, so the shoulders and haunches grow
  out of the body; skinned to the spine and limb bones;
- the dark back: a carapace of plates over the trunk, lifted onto the skin where muscles swell it;
- front legs: toes, hooked claws and a dewclaw on the hand;
- hind legs: four splayed toes, a heel spur and studs along the top of the foot.
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
import skin as SK  # noqa: E402
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


def section_vw(s, du, dv, th):
    """The trunk's cross-section at s, at angle th round the spine (0 dorsal, +pi/2 Clay's left): the
    offset (v toward the back, w to the left). A superellipse with the measured depths, narrowing below
    the spine into the keel of the chest and belly (trunk.keel)."""
    nsq = table(TR["squareness"], s)
    wf = table(TR["width"]["factor"], s) * (du + dv) / 2
    c, sn = math.cos(th), math.sin(th)
    v = (du if c > 0 else dv) * math.copysign(abs(c) ** (2 / nsq), c)
    eta = v / (du if v > 0 else dv)
    w = wf * math.copysign(abs(sn) ** (2 / nsq), sn) * (1 - table(TR["keel"]["rows"], s) * smoothstep(-0.1, 1.0, -eta))
    return v, w


_TF = {}
_SKIN = {}


def trunk_surface(s, th):
    """A point on the trunk (with its muscle masses) at spine position s and angle th (0 dorsal,
    +pi/2 Clay's left), and the outward direction there."""
    if not _TF:
        _TF["f"] = trunk_frames()
    s_all, P, DU, DV, N, Bv = _TF["f"]
    i = int(np.clip(np.searchsorted(s_all, s), 1, len(s_all) - 1))
    t = (s - s_all[i - 1]) / (s_all[i] - s_all[i - 1])
    lerp = lambda X: X[i - 1] * (1 - t) + X[i] * t
    p, du, dv, n, b = lerp(P), lerp(DU), lerp(DV), H.norm(lerp(N)), H.norm(lerp(Bv))
    v, w = section_vw(max(s, 0.0), du, dv, th)
    q = p + n * v + b * w
    out = H.norm(q - p)
    return q, out


def carapace_edge(s):
    """Angle from the dorsal line at which the dark back ends at s (the rim of the carapace)."""
    for th in np.linspace(0.05, math.pi - 0.05, 120):
        q, _ = trunk_surface(s, th)
        if zone_value(s, (1 - math.cos(th)) / 2, q[2], q[1]) > 0.25:
            return th
    return math.pi - 0.05


def carapace_plate(s0, s1, th0, th1, nv, ranges, thick, lift, flare=0.0, seed=0, wrap=False):
    """A shell plate over the trunk between s0..s1 and angles th0..th1 (functions of s), raised by lift,
    bevelled, thicker toward its back edge and overlapping the next one back. With flare, its outer edge
    rolls outward like a turtle shell's margin."""
    C = B["carapace"]; bev, ov, gap = C["bevel"], C["overlap"], C["gap"]
    s0g, s1g = s0 + gap / 2, s1 - gap / 2 + ov
    nu = max(4, int((s1g - s0g) / 0.01))
    rnd = lambda x: math.sqrt(max(0.0, 1 - (1 - min(1.0, max(0.0, x))) ** 2))
    verts, A, Bq, W = [], [], [], []
    tint = (math.sin(seed * 12.9898) * 43758.5453) % 1.0
    for i in range(nu + 1):
        u = i / nu; sc = s0g + (s1g - s0g) * u
        a0, a1 = th0(sc), th1(sc)
        if not wrap:
            a0, a1 = a0 + gap * 2, a1 - gap * 2
        row = [trunk_surface(sc, a0 + (a1 - a0) * j / nv) for j in range(nv + 1)]
        if _SKIN:  # where muscles swell the skin (the shoulder, the haunch), the plates ride over them
            Q = SK.lift_onto([q for q, _ in row], np.array([o for _, o in row]), _SKIN["trunk"], _SKIN["parts"])
            row = [(Q[j], o) for j, (_, o) in enumerate(row)]
        acc = np.concatenate([[0], np.cumsum([np.linalg.norm(row[k + 1][0] - row[k][0]) for k in range(nv)])])
        Lv, Ls = acc[-1] + 1e-6, s1g - s0g
        for j, (q, out) in enumerate(row):
            dist = min(u * Ls, (1 - u) * Ls * 2.5, acc[j], Lv - acc[j])
            e = rnd(dist / bev)
            rim = flare * smoothstep(0.5, 1.0, j / nv) if not wrap else 0.0
            h = lift + (thick * (0.7 + 0.3 * u) + rim) * e
            verts.append(tuple(q + out * h)); A.append(dist); Bq.append(tint); W.append(trunk_weights(sc, ranges))
    faces = []
    for i in range(nu):
        for j in range(nv):
            q = i * (nv + 1) + j
            faces.append([q, q + 1, q + nv + 2, q + nv + 1])
    return verts, faces, A, Bq, W


def carapace_parts(ranges):
    """The dark back as a turtle-shell carapace over the trunk: transverse bands wrapping over the top
    down to the rim, and a rim of square marginal scutes along the measured dark edge (mirrored)."""
    C = B["carapace"]
    edge = {}
    def th_edge(s):
        k = round(s / 0.02) * 0.02
        if k not in edge:
            edge[k] = carapace_edge(k)
        return edge[k]
    parts = []
    band_to = lambda s: th_edge(s) - C["rim"]["height"] / max(0.05, trunk_radius(s))
    s, k = C["from_s"], 0
    while s < C["to_s"]:
        s1 = min(C["to_s"], s + C["band_every"] * (1 if s < TR["bones"]["tail_from"] else C["tail_scale"]))
        v, f, A, Bq, W = carapace_plate(s, s1, lambda x: -band_to(x), band_to, 16, ranges, C["thickness"], C["lift"], seed=k, wrap=True)
        parts.append(H.add_part(f"Back{k}", v, f, {"_PART": [13] * len(v), "_A": A, "_B": Bq, "_ZONE": [0] * len(v)}, W))
        s, k = s1, k + 1
    R = C["rim"]
    for side in (1, -1):
        s, j = C["from_s"] + R["offset"], 0
        while s < C["to_s"]:
            s1 = min(C["to_s"], s + R["every"] * (1 if s < TR["bones"]["tail_from"] else C["tail_scale"]))
            lo = (lambda x: band_to(x)) if side > 0 else (lambda x: -th_edge(x))
            hi = (lambda x: th_edge(x)) if side > 0 else (lambda x: -band_to(x))
            v, f, A, Bq, W = carapace_plate(s, s1, lo, hi, 4, ranges, R["thickness"], C["lift"], flare=R["flare"] if side > 0 else 0.0, seed=100 + j)
            parts.append(H.add_part(f"Rim{j}{side}", v, f, {"_PART": [13] * len(v), "_A": A, "_B": Bq, "_ZONE": [0] * len(v)}, W))
            s, j = s1, j + 1
    return parts


def trunk_radius(s):
    st = np.array(TR["stations"])
    return (table(st, s, 3) + table(st, s, 4)) / 2


def skin_setup():
    """The trunk as a field (its measured sections along the spine) and the bones and muscles."""
    s_all, P, DU, DV, N, Bv = trunk_frames()
    trunk = SK.Trunk(s_all, P, N, Bv, lambda i, th: section_vw(max(s_all[i], 0.0), DU[i], DV[i], th))
    _SKIN["trunk"], _SKIN["parts"] = trunk, SK.pieces(B["anatomy"])


def skin_part(ranges):
    """One skin over the trunk, bones and muscles (skin.py), skinned to the spine and limb bones."""
    trunk, parts = _SKIN["trunk"], _SKIN["parts"]
    V, F = SK.mesh(trunk, parts, B["anatomy"]["resolution"])
    W, Z, A, Bf = SK.vertex_data(V, trunk, parts, lambda s: trunk_weights(s, ranges), zone_value)
    return H.add_part("Skin", V.tolist(), F.tolist(), {"_PART": [20] * len(V), "_A": A, "_B": Bf, "_ZONE": Z}, W)


# ---------------------------------------------------------------- limbs
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
    parts = []  # the leg itself is part of the skin (bones and muscles)
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
    """One hind leg's bones and attachments: four splayed toes, a heel spur, and studs along the top of
    the foot (the leg itself is part of the skin)."""
    L = B["hind_leg"]; sd = "L" if sgn > 0 else "R"
    J = {k: mirror(v, sgn) for k, v in L["joints"].items()}
    parts = []
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
    skin_setup()
    objs.append(skin_part(ranges))
    objs += carapace_parts(ranges)
    neck_end = TR["bones"]["chain_forward"][-1][0]
    bones = tb + [(n, h, t, p or neck_end) for n, h, t, p in head_bones]
    for sgn in (1, -1):
        for leg in (front_leg, hind_leg):
            parts, lb = leg(sgn)
            objs += parts; bones += lb
    H.assemble(objs, bones, OUT, "ClayRig")


if __name__ == "__main__":
    main()
