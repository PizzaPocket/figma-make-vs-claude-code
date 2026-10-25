"""Clay, head and body, built in Blender from measured data, exported as one rigged .glb.

The head comes from ../head/build_head.py. The body is built here, element by element (see
body_design.json and body_sheets.md):
- skin (skin.py): one surface over the trunk (neck, torso and tail, measured cross-sections along a
  curved spine), the limb bones and the muscles that work them, so the shoulders and haunches grow
  out of the body; skinned to the spine and limb bones;
- the dark shell: the skin's dark region (the back, shoulder and hip caps, the top of the tail)
  raised as one smooth layer with a rolled rim running round its whole edge;
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
def tail_vertebrae():
    """The s at each joint between caudal vertebrae: each a fixed fraction shorter than the one before,
    from first_length, filling the tail from from_s to its tip."""
    tl = TR["tail"]; n, a = tl["vertebrae"], tl["first_length"]
    L = TR["stations"][-1][0] - tl["from_s"]
    lo, hi = 0.5, 1.0
    for _ in range(60):  # the ratio that makes n vertebrae sum to the tail's length
        r = (lo + hi) / 2
        lo, hi = (r, hi) if a * (1 - r ** n) / (1 - r) < L else (lo, r)
    lengths = [a * r ** k for k in range(n)]
    return list(tl["from_s"] + np.concatenate([[0], np.cumsum(lengths)]) * L / sum(lengths))


def tail_heading(s):
    """The tail's direction at s: pitch (+ up) and yaw (0 straight back, + toward Clay's left)."""
    K = np.array(TR["tail"]["heading_keys"], float)
    p, ya = math.radians(np.interp(s, K[:, 0], K[:, 1])), math.radians(np.interp(s, K[:, 0], K[:, 2]))
    return np.array([math.sin(ya) * math.cos(p), math.sin(p), -math.cos(ya) * math.cos(p)])


def trunk_frames(step=0.01):
    """Spine points (bind pose), depths, and a parallel-transported frame (dorsal normal N, side B).
    The neck and torso follow the side sheet's traced spine; the tail is the vertebral chain, laid
    along its heading from the hips and resting on the ground where it lies flat."""
    st = np.array(TR["stations"], float)
    tl = TR["tail"]; t0 = tl["from_s"]
    s_all = np.arange(-TR["front_overlap"], st[-1, 0] + 1e-9, step)
    # smooth curves through the measured stations (straight segments between them kinked the surface at each one):
    # a cubic spline for the spine, shape-preserving curves for the depths
    from scipy.interpolate import CubicSpline, PchipInterpolator
    curves = [CubicSpline(st[:, 0], st[:, 1]), CubicSpline(st[:, 0], st[:, 2]),
              PchipInterpolator(st[:, 0], st[:, 3]), PchipInterpolator(st[:, 0], st[:, 4])]
    P, DU, DV = [], [], []
    for s in s_all:
        sc = min(max(s, 0.0), st[-1, 0])
        z, y, du, dv = (float(c(sc)) for c in curves)
        if s < 0:  # run on into the head along the first tangent, so the join is hidden inside it
            z1, y1 = table(st, 0.02, 1), table(st, 0.02, 2)
            z, y = z + (z - z1) / 0.02 * (-s), y + (y - y1) / 0.02 * (-s)
        w = smoothstep(t0, t0 + 0.3, sc)  # the tail's section is symmetric about its spine
        du, dv = du * (1 - w) + (du + dv) / 2 * w, dv * (1 - w) + (du + dv) / 2 * w
        if sc > t0:  # a gecko's tail: fat at the root, tapering steadily all the way to a point
            r0 = (table(st, t0, 3) + table(st, t0, 4)) / 2
            r = r0 * max(0.0, (st[-1, 0] - sc) / (st[-1, 0] - t0)) ** tl["taper_power"] + 1e-3
            k = smoothstep(t0, t0 + 0.4, sc)
            du, dv = du * (1 - k) + r * k, dv * (1 - k) + r * k
        P.append([0.0, y, z]); DU.append(du); DV.append(dv)
    P = np.array(P)
    i0 = int(np.searchsorted(s_all, t0))
    for i in range(i0 + 1, len(s_all)):
        P[i] = P[i - 1] + tail_heading(s_all[i - 1]) * (s_all[i] - s_all[i - 1])
        rest = smoothstep(tl["rest_from_s"], tl["rest_to_s"], s_all[i])  # lying on the ground
        P[i, 1] += (tl["ground_y"] + DV[i] - P[i, 1]) * rest
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
    lim = B["shell"]["dark_below_f"]  # the dark region is on the body's upper side only
    dark = (1 - smoothstep(-w, w, poly_sdist(z, y, _ZONES["dark"]))) * (1 - smoothstep(lim - 0.04, lim + 0.04, f))
    cream = 1 - smoothstep(-w, w, poly_sdist(z, y, _ZONES["cream"]))
    # the cream underside: the sheet's cream region, or the underside of the body by its place round it
    # (zones.rows), so the throat band wraps under the neck wherever the side view can't show it
    cream = max(cream, smoothstep(fc - 0.015, fc + 0.015, f))
    by_lines = 0.5 * (1 - dark) + 0.5 * cream * (1 - dark)
    t = smoothstep(Zd["lines_until_s"] - 0.15, Zd["lines_until_s"] + 0.15, s)
    return by_lines * (1 - t) + by_fraction * t


def dark_value(s, f, z, y):
    """1 inside the dark shell, 0 outside: on the neck and torso the sheet's dark region (a side-view
    line, so only on the body's upper side, f < dark_below_f, and not across its underside); on the
    tail the dark top by fraction."""
    Zd = TR["zones"]
    if not _ZONES:
        _ZONES["dark"] = px_to_model(Zd["dark_region_px"]); _ZONES["cream"] = px_to_model(Zd["cream_region_px"])
    fd = table(Zd["rows"], s, 1)
    by_fraction = 1 - smoothstep(fd - 0.015, fd + 0.015, f)
    lim = B["shell"]["dark_below_f"]
    by_lines = (1 - smoothstep(-0.012, 0.012, poly_sdist(z, y, _ZONES["dark"]))) * (1 - smoothstep(lim - 0.04, lim + 0.04, f))
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
    edges = tail_vertebrae()[::3]  # one bone for every three caudal vertebrae
    n = len(edges) - 1
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


_SKIN = {}


def skin_setup():
    """The trunk as a field (its measured sections along the spine) and the bones and muscles."""
    s_all, P, DU, DV, N, Bv = trunk_frames()
    trunk = SK.Trunk(s_all, P, N, Bv, lambda i, th: section_vw(max(s_all[i], 0.0), DU[i], DV[i], th))
    _SKIN["trunk"], _SKIN["parts"] = trunk, SK.pieces(B["anatomy"])


def band(x):
    """The shell's band coordinate at spine position x: one per plate band (shell.band_every)."""
    K = np.array(B["shell"]["band_every"], float)
    sg = np.linspace(0, 6, 601)
    bcum = np.concatenate([[0], np.cumsum(np.diff(sg) / np.interp(sg[:-1], K[:, 0], K[:, 1]))])
    return np.interp(x, sg, bcum)


def skin_parts(ranges):
    """One skin over the trunk, bones and muscles (skin.py), skinned to the spine and limb bones, and
    the dark shell raised from it with a continuous rim round its edge."""
    trunk, parts = _SKIN["trunk"], _SKIN["parts"]
    V, F = SK.mesh(trunk, parts, B["anatomy"]["resolution"])
    W, Z, A, Bf = SK.vertex_data(V, trunk, parts, lambda s: trunk_weights(s, ranges), zone_value, dark_value,
                                 TR["zones"]["lines_until_s"] + 0.15)
    Z = list(SK.smooth_on_mesh(V, F, Z))  # no pinholes in the shell, smooth edges to its colour regions
    skin = H.add_part("Skin", V.tolist(), F.tolist(), {"_PART": [20] * len(V), "_A": A, "_B": Bf, "_ZONE": Z}, W)
    idx = trunk.local(V)[0]
    sh = B["shell"]
    S, SF, src, ink, tint = SK.shell(V, F, Z, sh, SK.smooth_normals(V, F), trunk.s[idx], np.array(Bf), band)
    shell = H.add_part("Shell", S.tolist(), SF.tolist(), {"_PART": [13] * len(S), "_A": list(ink), "_B": list(tint), "_ZONE": [0] * len(S)},
                       [W[i] for i in src])
    return [skin, shell]


# ---------------------------------------------------------------- limbs
def spike_parts(ranges, band):
    """The mane and the tail spikes (B["spikes"]): thin leaf-shaped blades on the shell's midline,
    raked back, each moving with the spine bone under it."""
    s_all, P, DU, DV, N, Bv = trunk_frames()
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    parts = []
    for row in B["spikes"]["rows"]:
        if row["every"] == "band":  # one per plate band, at its middle
            k0, k1 = int(math.ceil(band(row["from_s"]))), int(math.floor(band(row["to_s"])))
            sg = np.linspace(0, 6, 6001); bg = band(sg)
            ss = [float(np.interp(k + 0.5, bg, sg)) for k in range(k0, k1)]
        else:
            ss = list(np.arange(row["from_s"], row["to_s"], row["every"]))
        rake = math.radians(row["rake_deg"])
        for n, s in enumerate(ss):
            i = int(np.argmin(abs(s_all - s)))
            hgt = table(row["height"], s)
            L = hgt / math.sin(rake)
            d = H.norm(T[i] * math.cos(rake) + N[i] * math.sin(rake))
            e = H.norm(N[i] - (N[i] @ d) * d)  # across the blade, in its plane
            base = P[i] + N[i] * (DU[i] + B["shell"]["thickness"] * 0.5) - d * 0.02  # rooted in the shell
            W, th = row["width"] * min(1.0, hgt / 0.06) ** 0.3, row["thickness"]
            thorn = row.get("shape") == "thorn"
            if thorn:  # lying along the top: base on the surface, convex outer edge, point at the back
                L, W = hgt * row["length_per_height"], hgt
                base = P[i] + N[i] * (DU[i] + B["shell"]["thickness"] * 0.5) - d * L * 0.5
            verts, faces, around, nt = [], [], 8, 10
            for a in range(nt + 1):
                tt = a / nt
                w = W * ((tt / 0.3) ** 0.6 if tt < 0.3 else ((1 - tt) / 0.7) ** 1.1)  # a leaf, widest a third of the way out
                c = base + d * (L + 0.02) * tt
                if thorn:  # one-sided: the leaf's lower half sinks into the shell
                    c = base + d * L * tt + e * (w / 2 - 0.008); w = w / 2 + 0.008
                for j in range(around):
                    ang = 2 * math.pi * j / around
                    verts.append(tuple(c + e * w * math.cos(ang) + Bv[i] * (th * (1 - tt) + 0.002) * math.sin(ang)))
            for a in range(nt):
                for j in range(around):
                    p0 = a * around + j; p1 = a * around + (j + 1) % around
                    faces.append([p0, p1, p1 + around, p0 + around])
            parts.append(H.add_part(f"Spike{row['name']}{n}", verts, faces, {"_PART": [13] * len(verts), "_A": [0.02] * len(verts), "_B": [0.25] * len(verts),
                                    "_ZONE": [0] * len(verts)}, [trunk_weights(s, ranges)] * len(verts)))
    return parts


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
    objs += skin_parts(ranges)
    objs += spike_parts(ranges, band)
    neck_end = TR["bones"]["chain_forward"][-1][0]
    bones = tb + [(n, h, t, p or neck_end) for n, h, t, p in head_bones]
    for sgn in (1, -1):
        for leg in (front_leg, hind_leg):
            parts, lb = leg(sgn)
            objs += parts; bones += lb
    H.assemble(objs, bones, OUT, "ClayRig")


if __name__ == "__main__":
    main()
