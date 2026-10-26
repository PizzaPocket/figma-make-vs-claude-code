"""Clay, head and body, built in Blender from measured data, exported as one rigged .glb.

The head comes from ../head/build_head.py. The body is built here, element by element (see
body_design.json and body_sheets.md):
- skin (skin.py): one surface over the trunk (neck, torso and tail, measured cross-sections along a
  curved spine), the limb bones and the muscles that work them, so the shoulders and haunches grow
  out of the body; skinned to the spine and limb bones;
- the dark shell: the skin's dark region (the back, shoulder and hip caps, the top of the tail)
  raised as one smooth layer with a rolled rim running round its whole edge;
- front legs: toes, hooked claws and a dewclaw on the hand;
- hind legs: four toes (part of the skin) with claws, and a heel spur.
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


def smoothstep_v(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
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
            # ending in a small rounded tip (tip_radius) rather than a point thinner than the mesh can hold
            tr = tl["tip_radius"]; u = (sc - (st[-1, 0] - tr)) / tr
            r = max(r, tr * math.sqrt(max(0.0, 1 - min(max(u, 0.0), 1.0) ** 2)))
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


def zone_value(s, f, z=None, y=None, x=None):
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
    if x is not None:  # over the chest the cream is a central band of plates; orange wraps the shoulders round it
        hw = table(Zd["cream_halfwidth"], s)
        cream *= 1 - smoothstep(hw - 0.02, hw + 0.02, abs(x))
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
    """Weights of the spine bones at s: the bone whose range holds s, blended with its neighbour near the joint.
    Joints touching the neck blend over half a neck bone (neck_blend), so the neck bends in one smooth curve as the
    head turns instead of kinking at each joint."""
    ranges = sorted(ranges, key=lambda r: r[1])
    bl = lambda n0, n1: TR["bones"]["neck_blend"] if "neck" in n0 + n1 else blend
    for i, (name, a, b) in enumerate(ranges):
        if a <= s <= b or (i == 0 and s < a) or (i == len(ranges) - 1 and s > b):
            w = [(name, 1.0)]
            if i + 1 < len(ranges) and s > b - bl(name, ranges[i + 1][0]):
                # half and half at the joint itself, whichever side it is read from
                k = bl(name, ranges[i + 1][0]); t = smoothstep(b - k, b + k, s); w = [(name, 1 - t), (ranges[i + 1][0], t)]
            elif i > 0 and s < a + bl(name, ranges[i - 1][0]):
                k = bl(name, ranges[i - 1][0]); t = 1 - smoothstep(a - k, a + k, s); w = [(name, 1 - t), (ranges[i - 1][0], t)]
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


def head_weld():
    """The face and jaw behind the mouth corner as pieces of the skin's field (anatomy.head_weld), from their
    own cross-sections (build_head's contours, closed across the mouth)."""
    HW = B["anatomy"]["head_weld"]
    CL = np.array(HW["cheek_line"]["zy"]); b0, b1 = HW["cheek_line"]["blend"]

    def cheek_dz(X):
        """How far in front of the cheek line (model z) each point lies, in side view."""
        return X[:, 2] - np.interp(X[:, 1], CL[:, 1], CL[:, 0])

    def inset_at(X):
        """Set in under the face and jaw in front of the cheek line, their surface behind it."""
        t = np.clip((cheek_dz(X) - b0) / (b1 - b0), 0.0, 1.0)
        return HW["inset"] * t * t * (3 - 2 * t)

    _SKIN["cheek_dz"] = cheek_dz

    def clip(X, d, D, parts):
        """The skin keeps to the face and jaw (set in by inset) in front of the cheek line, and is let out from them
        gradually behind it (by rise * distance squared), so the neck's fillet swells out of the head's surface
        smoothly instead of through it; a smooth maximum, so the cut leaves no kink for the mesh to step on."""
        k = [i for i, p in enumerate(parts) if p.kind == "section"]
        if not k:  # a surface without the head (the wing arm)
            return d
        dh = D[k[0]]
        for i in k[1:]:
            dh = SK.smin(dh, D[i], parts[i].k)  # the face and jaw joined as the union joins them, filling between them
        behind = np.maximum(-cheek_dz(X), 0.0)
        lim = dh - HW["rise"] * behind ** 2
        return np.where(dh < parts[k[0]].margin, -SK.smin(-d, -lim, HW["clip_k"]), d)

    SK.CLIP = clip
    out = []
    for sp in HW["parts"]:
        rows, contour = (H.UPPER, H.upper_contour) if sp["mesh"] == "Face" else (H.JAW, H.jaw_contour)
        zs = np.linspace(rows[-1, 0], HW["zcut"] + 0.03, 40)
        secs = [(z, contour(z)[0]) for z in zs]
        out.append(SK.SectionPiece(sp["mesh"], secs, sp["rig"], sp["zone"], HW["k"], HW["inset"], HW["zcut"], inset_at=inset_at))
    return out


def trim_head(objs):
    """Remove the face and jaw behind the cheek line: there the body's skin is the head's surface (head_weld)."""
    import bmesh
    for ob in objs:
        if ob.name not in [p["mesh"] for p in B["anatomy"]["head_weld"]["parts"]]:
            continue
        bm = bmesh.new(); bm.from_mesh(ob.data)
        co = np.array([v.co[:] for v in bm.verts]); M = np.stack([co[:, 0], co[:, 2], -co[:, 1]], 1)
        behind = _SKIN["cheek_dz"](M) < 0
        bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if any(behind[v.index] for v in f.verts)], context="FACES")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bm.to_mesh(ob.data); bm.free(); ob.data.update()


def head_weld_weights(V, W, parts):
    """At the cheek line and in front of it the skin is the head's own surface, so it moves exactly with the head
    and jaw (whichever is nearer), handing over to the neck's weights over head_weld.handover behind the line.
    Otherwise the trimmed face's edge and the skin under it part as the head turns or the mouth opens."""
    sec = {p.name: p for p in parts if p.kind == "section"}
    if not sec:
        return W
    h0, h1 = B["anatomy"]["head_weld"]["handover"]
    df, dj = sec["Face"].sdf(V), sec["Jaw"].sdf(V)
    wj = 1 / (1 + np.exp(np.clip((dj - df) / 0.008, -50, 50)))  # the jaw's share: where the jaw is the nearer
    t = np.clip((_SKIN["cheek_dz"](V) - h0) / (h1 - h0), 0, 1); t = t * t * (3 - 2 * t)
    t *= np.minimum(df, dj) < 0.03
    out = []
    for n, wl in enumerate(W):
        if t[n] <= 0:
            out.append(wl); continue
        acc = {bn: w * (1 - t[n]) for bn, w in wl}
        acc["head"] = acc.get("head", 0) + t[n] * (1 - wj[n]); acc["jaw"] = acc.get("jaw", 0) + t[n] * wj[n]
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(w for _, w in top)
        out.append([(bn, w / tot) for bn, w in top if w > 0])
    return out


def skin_setup(weld=True):
    """The trunk as a field (its measured sections along the spine), the bones and muscles, and the back of the head."""
    s_all, P, DU, DV, N, Bv = trunk_frames()
    trunk = SK.Trunk(s_all, P, N, Bv, lambda i, th: section_vw(max(s_all[i], 0.0), DU[i], DV[i], th))
    toes = []
    for L, prefix in ((B["front_leg"], "ftoe"), (B["hind_leg"], "htoe")):
        sb, sm = toe_pieces(L, prefix)
        toes += [SK.Piece(s, sgn, "bone") for sgn in (1, -1) for s in sb] + [SK.Piece(s, sgn, "muscle") for sgn in (1, -1) for s in sm]
    _SKIN["trunk"], _SKIN["parts"] = trunk, SK.pieces(B["anatomy"]) + toes + (head_weld() if weld else [])


def band(x):
    """The shell's band coordinate at spine position x: one per plate band (shell.band_every)."""
    K = np.array(B["shell"]["band_every"], float)
    sg = np.linspace(0, 6, 601)
    bcum = np.concatenate([[0], np.cumsum(np.diff(sg) / np.interp(sg[:-1], K[:, 0], K[:, 1]))])
    return np.interp(x, sg, bcum)


def skin_parts(ranges, ear_pts=None):
    """One skin over the trunk, bones and muscles (skin.py), skinned to the spine and limb bones, and
    the dark shell raised from it with a continuous rim round its edge. ear_pts: the ears' vertices (model
    coordinates), which the shell keeps clear of by design (anatomy.ear_clearance)."""
    trunk, parts = _SKIN["trunk"], _SKIN["parts"]
    V, F = SK.mesh(trunk, parts, B["anatomy"]["resolution"])
    # the spine position for the spine bones' weights, smoothed over the skin: on the inside of the neck's bend the
    # nearest spine station flips between stations far apart from one vertex to the next, which made the weights
    # jump and the neck crease in bands as it bent
    i0, _, _, t_al = trunk.local(V)[:4]
    S_rig = SK.smooth_on_mesh(V, F, trunk.s[i0] + t_al, iters=B["anatomy"]["rig_smooth_iters"])
    W, Z, A, Bf, Tr = SK.vertex_data(V, trunk, parts, lambda s: trunk_weights(s, ranges), zone_value, dark_value,
                                 TR["zones"]["lines_until_s"] + 0.15, N=SK.normals(V, F), S_rig=S_rig)
    W = head_weld_weights(V, W, parts)
    Z = list(SK.smooth_on_mesh(V, F, Z))  # no pinholes in the shell, smooth edges to its colour regions
    Tr = list(SK.smooth_on_mesh(V, F, Tr))
    # the distance round the trunk from the top of the spine (angle times the section's mean radius), for laying the
    # scales out in rows; carried in _PART's fraction (20 + around / 4, under 20.4, still part 20), as the other
    # attributes are full
    idx, v, w = trunk.local(V)[:3]
    around = np.arctan2(np.abs(w), v) * trunk.R[idx].mean(axis=1)
    skin = H.add_part("Skin", V.tolist(), F.tolist(), {"_PART": list(20 + np.clip(around, 0, 1.56) / 4), "_A": A, "_B": Tr, "_ZONE": Z}, W)
    sh = B["shell"]
    S, SF, src, ink, tint = SK.shell(V, F, Z, sh, SK.smooth_normals(V, F), trunk.s[idx], np.array(Bf), band)
    if "cheek_dz" in _SKIN:  # the shell and its rim run out into the cheek line, where the head's surface takes over
        t = 1 - smoothstep_v(-B["anatomy"]["head_weld"]["shell_taper"], 0.0, _SKIN["cheek_dz"](S))
        S = V[src] + (S - V[src]) * t[:, None]
    if ear_pts is not None and len(ear_pts):
        # clear of the ears by design: within the margin of an ear's mesh the shell lies flush on the skin, so its
        # rim never reaches into the ear's path (it reached to within 0.002 of the ear's rolled rim)
        from scipy.spatial import cKDTree
        EC = B["anatomy"]["ear_clearance"]
        d, _ = cKDTree(ear_pts).query(S)
        t = smoothstep_v(EC["flush_within"], EC["full_from"], d)
        S = V[src] + (S - V[src]) * t[:, None]
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
        d = H.rot(d, axis, math.radians(hook_deg) / 6)  # curling toward `down`
        pts.append(p)
    v, f, A, Bq = H.tube(pts, [radius, radius * 0.92, radius * 0.78, radius * 0.6, radius * 0.42, radius * 0.22, 0.002], around=10, step=0.004)
    return v, f


def toe_layout(kn, back, T):
    """The toes on the left side: per toe its points (base, middle joint, tip) and the distal segment's
    direction. kn: the knuckle line's centre, back: the point behind it (wrist or heel)."""
    fwd = H.norm(kn - back); fwd[1] = 0; fwd = H.norm(fwd)
    out = []
    for k in range(T["count"]):
        d = H.rot(fwd, np.array([0, 1.0, 0]), math.radians(T["spread_deg"][k]))
        side = H.norm(np.cross(d, [0, 1.0, 0]))
        p = kn + np.array([T["base_offset_x"][k], 0, 0]) - fwd * 0.03
        pts, dd = [p], d
        for j, sl in enumerate(T["segments"]):
            dd = H.rot(d, side, -math.radians(T["drop_deg"][j]))
            p = p + dd * sl; pts.append(p)
        out.append((pts, dd))
    return out


def thumb_layout(J, Th):
    """The front hand's opposable thumb (left side): base on the inner side of the hand, then its two
    segments, the second bent further down. Returns its points and the last segment's direction."""
    base = J["wrist"] + (J["knuckles"] - J["wrist"]) * Th["at_frac"] + np.array([Th["inset_x"], 0, 0])
    d = H.norm(np.array(Th["direction"], float))
    side = H.norm(np.cross(d, [0, 1.0, 0]))
    d2 = H.rot(d, side, -math.radians(20))
    p1 = base + d * Th["segments"][0]
    return [base, p1, p1 + d2 * Th["segments"][1]], d2


def digit_specs(pts, dd, radii, bn, blend):
    """One toe, finger or thumb as skin pieces: a bone per segment and a pad under its tip."""
    sb = [{"name": f"{bn} phalanx {j + 1}", "from": pts[j].tolist(), "to": pts[j + 1].tolist(), "r": [radii[j], radii[j] * 0.9],
           "k": blend if j == 0 else 0.012, "rig": {bn: 1.0}, "zone": 0.5} for j in range(len(pts) - 1)]
    r = radii[-1]
    a, b = pts[-2] + np.array([0, -r * 0.4, 0]), pts[-1] + dd * r * 0.2 + np.array([0, -r * 0.35, 0])
    sm = [{"name": f"{bn} pad", "from": a.tolist(), "to": b.tolist(), "radii": [r * 0.75, r * 1.05], "hint": [0, -1.0, 0],
           "k": 0.012, "rig": {bn: 1.0}, "zone": 0.8}]
    return sb, sm


def toe_pieces(L, prefix):
    """The toes as part of the skin (skin.py), so the foot is one form: each toe a bone per segment,
    fused into the hand or foot mass at its base and parted from its neighbours by grooves toward the
    tips, with a pad under its tip (How to Draw, the side sheet: short thick toes ending in rounded
    knuckles). Left-side specs; Piece mirrors them."""
    J = {k: np.array(v) for k, v in L["joints"].items()}
    kn, back = (J["knuckles"], J["wrist"]) if "knuckles" in J else (J["ball"], J["heel"])
    T = L["toes"]; specs_b, specs_m = [], []
    for k, (pts, dd) in enumerate(toe_layout(kn, back, T)):
        sb, sm = digit_specs(pts, dd, T["radius"], f"{prefix}{k + 1}", T["blend"])
        specs_b += sb; specs_m += sm
    if "thumb" in L:
        pts, dd = thumb_layout(J, L["thumb"])
        sb, sm = digit_specs(pts, dd, L["thumb"]["radius"], "fthumb", T["blend"])
        specs_b += sb; specs_m += sm
    return specs_b, specs_m


def toes(kn, back, T, sgn, parent, prefix, sd):
    """The toes' bones and their claws (the toes themselves are part of the skin, toe_pieces). Each
    claw springs from the top of its toe's tip, runs forward and hooks down to the ground."""
    parts, bones = [], []
    up = np.array([0, 1.0, 0])
    for k, (pts, dd) in enumerate(toe_layout(kn, back, dict(T, spread_deg=[sgn * a for a in T["spread_deg"]],
                                                            base_offset_x=[sgn * a for a in T["base_offset_x"]]))):
        bn = f"{prefix}{k + 1}.{sd}"
        cl = T["claw"]; r = T["radius"][-1]
        fwd = H.norm(np.array([dd[0], 0, dd[2]]))
        base = pts[-1] + fwd * r * 0.3 + up * r * 0.3
        d0 = H.norm(fwd * math.cos(math.radians(cl["pitch_deg"])) - up * math.sin(math.radians(cl["pitch_deg"])))
        v, f = claw_tube(base, d0, cl["length"], cl["radius"], cl["hook_deg"])
        parts.append(H.add_part(f"{prefix}Claw{k}{sd}", v, f, {"_PART": [23] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(bn, 1.0)]] * len(v)))
        bones.append((bn, tuple(pts[0]), tuple(pts[-1]), parent))
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
    Th = L["thumb"]; bn = f"fthumb.{sd}"
    pts, dd = thumb_layout({k: np.array(v, float) for k, v in L["joints"].items()}, Th)
    pts = [mirror(p, sgn) for p in pts]; dd = mirror(dd, sgn)
    cl, r = Th["claw"], Th["radius"][-1]
    # along the thumb's tip, hooking forward toward the fingers it opposes
    v, f = claw_tube(pts[-1] + dd * r * 0.3, dd, cl["length"], cl["radius"], cl["hook_deg"], down=np.array([0, 0, 1.0]))
    parts.append(H.add_part(f"ThumbClaw{sd}", v, f, {"_PART": [23] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(bn, 1.0)]] * len(v)))
    bones.append((bn, tuple(pts[0]), tuple(pts[-1]), f"hand.{sd}"))
    return parts, bones


def hind_leg(sgn):
    """One hind leg's bones and attachments: the toes' bones and claws and a heel spur (the leg and toes
    themselves are part of the skin)."""
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
    return parts, bones


def spar(name, pts, radii, bn, around=12):
    """A finger: a tube of plain orange skin (the plates are the arm's alone). _A: length along it, _B: 0
    (no plates). bn: one bone name, or a function of the fraction along it giving the bone."""
    v, f, A, _ = H.tube(pts, radii, around=around, step=0.004)
    total = sum(float(np.linalg.norm(np.subtract(pts[k + 1], pts[k]))) for k in range(len(pts) - 1))
    Bq = [0.0] * len(v)
    w = [[(bn(a) if callable(bn) else bn, 1.0)] for a in A]
    return H.add_part(name, v, f, {"_PART": [24] * len(v), "_A": [a * total for a in A], "_B": Bq, "_ZONE": [0] * len(v)}, w)


def align(a, b):
    """The smallest rotation (a matrix) turning direction a onto direction b."""
    a, b = H.norm(a), H.norm(b); v = np.cross(a, b); c = float(a @ b)
    if np.linalg.norm(v) < 1e-9:
        return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def wing_pose(sgn):
    """The wing at rest is spread (the flying covers); folded (the side sheet, where the anatomy is
    measured) is a pose of its bones. Returns the rest joints (with the elbow finger's tip) and finger tips,
    how to carry a point from the measured folded wing to rest (points on the humerus turn about the
    shoulder, on the forearm about the elbow; the bones keep their lengths), the forearm's turn, and the
    fold: per bone, its turn from rest to folded and its head when folded (both in the model's frame)."""
    Wg = B["wing"]; S = Wg["spread"]
    J = {k: np.array(v, float) for k, v in Wg["joints"].items()}
    tips = [np.array(t, float) for t in Wg["fingers"]]
    J["elbow_tip"] = np.array(Wg["elbow_finger"]["tip"], float)
    Rh = align(J["elbow"] - J["shoulder"], S["humerus_dir"])
    Rf = align(J["wrist"] - J["elbow"], S["forearm_dir"])
    R = dict(J)
    R["elbow"] = J["shoulder"] + Rh @ (J["elbow"] - J["shoulder"])
    R["wrist"] = R["elbow"] + Rf @ (J["wrist"] - J["elbow"])
    R["elbow_tip"] = R["elbow"] + H.norm(np.array(S["elbow_finger_dir"], float)) * np.linalg.norm(J["elbow_tip"] - J["elbow"])
    rtips = [R["wrist"] + H.norm(np.array(d, float)) * np.linalg.norm(t - J["wrist"]) for t, d in zip(tips, S["finger_dirs"])]
    def carry(p, bone):
        p = np.asarray(p, float)
        if bone == "wing_humerus":
            return R["shoulder"] + Rh @ (p - J["shoulder"])
        if bone == "wing_forearm":
            return R["elbow"] + Rf @ (p - J["elbow"])
        return p
    def rolled(R0, d):  # also turn about the folded bone so the armored top (up when spread) faces outward
        d = H.norm(d); u = R0 @ np.array([0, 1.0, 0]); u = H.norm(u - d * (u @ d))
        o = np.array([1.0, 0, 0]); o = H.norm(o - d * (o @ d))
        ang = math.atan2(np.cross(u, o) @ d, u @ o)
        return np.array([H.rot(c, d, ang) for c in R0.T]).T
    Rhf, Rff = rolled(Rh.T, J["elbow"] - J["shoulder"]), rolled(Rf.T, J["wrist"] - J["elbow"])
    fold = {"wing_humerus": (Rhf, J["shoulder"]), "wing_forearm": (Rff, J["elbow"]), "wing_thumb": (Rff, J["wrist"]),
            "wing_elbowfinger": (rolled(align(R["elbow_tip"] - R["elbow"], J["elbow_tip"] - J["elbow"]), J["elbow_tip"] - J["elbow"]), J["elbow"])}
    for k, (t, rt) in enumerate(zip(tips, rtips)):  # rolled too, so the membrane billows outward when folded, not into the leg
        fold[f"wing_finger{k + 1}"] = (rolled(align(rt - R["wrist"], t - J["wrist"]), t - J["wrist"]), J["wrist"])
        for seg in ("b", "c"):  # the two phalanges turn with it; their heads ride the bone before
            fold[f"wing_finger{k + 1}{seg}"] = (fold[f"wing_finger{k + 1}"][0], None)
    Mx = np.diag([sgn, 1.0, 1.0]); m = lambda p: mirror(p, sgn)
    fold = {n: (Mx @ Rm @ Mx, None if hd is None else m(hd)) for n, (Rm, hd) in fold.items()}
    return {k: m(v) for k, v in R.items()}, [m(t) for t in rtips], carry, Rf, fold


def wing_arm(sgn, sd):
    """The wing's arm as flesh over bone, like the legs (skin.py): bone capsules and muscle bellies joined
    smoothly, meshed on their own. Orange skin with dark plates over its top: _A: length along the arm,
    _B: how much it faces up when spread."""
    an = B["wing"]["anatomy"]
    J, _, carry, _, _ = wing_pose(sgn)
    def posed(spec):  # each piece rides the bone that carries most of it
        bone = max(spec["rig"].items(), key=lambda kv: kv[1])[0]
        return dict(spec, **{"from": carry(spec["from"], bone).tolist(), "to": carry(spec["to"], bone).tolist()})
    parts = [SK.Piece(posed(b), sgn, "bone") for b in an["bones"]] + [SK.Piece(posed(m), sgn, "muscle") for m in an["muscles"]]
    V, F = SK.mesh(None, parts, an["resolution"])
    W = SK.piece_weights(V, parts)
    path = np.array([J["shoulder"], J["elbow"], J["wrist"]])
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    A = []
    for p in V:  # length along the shoulder-elbow-wrist line, for the plate rows
        best = None
        for k in range(2):
            d = path[k + 1] - path[k]; h = float(np.clip((p - path[k]) @ d / (d @ d), 0, 1))
            dist = np.linalg.norm(p - (path[k] + d * h))
            if best is None or dist < best[0]:
                best = (dist, seg[:k].sum() + h * seg[k])
        A.append(best[1])
    Bq = list((SK.normals(V, F)[:, 1] + 1) / 2)  # facing up, spread: the armored side, alike on both wings
    arm = H.add_part(f"WingArm{sd}", V.tolist(), F.tolist(), {"_PART": [24] * len(V), "_A": A, "_B": [0.0] * len(V), "_ZONE": [0] * len(V)}, W)
    # its armor: a distinct shell over the top, like the back's (skin.shell): banded plates with a rolled rim
    ar = B["wing"]["armor"]
    Z = SK.smooth_on_mesh(V, F, [0.0 if b > ar["top_from"] else 1.0 for b in Bq], iters=4)
    S, SF, src, ink, tint = SK.shell(V, F, Z, ar, SK.smooth_normals(V, F), np.array(A), np.zeros(len(V)), lambda x: np.asarray(x) / ar["band"])
    shell = H.add_part(f"WingArmor{sd}", S.tolist(), SF.tolist(), {"_PART": [13] * len(S), "_A": list(ink), "_B": list(tint), "_ZONE": [0] * len(S)},
                       [W[i] for i in src])
    return [arm, shell]


def membrane_body_line(sgn):
    """Where the wing's membrane meets the body: just under the carapace's lower edge (zones.dark_edge_px),
    following its arch from the wing's root behind the shoulder armor to the front of the hip armor, on the
    body's surface (found along x from the midline)."""
    Wg = B["wing"]; L = Wg["membrane_line"]
    E = np.array(TR["zones"]["dark_edge_px"], float)
    trunk, parts = _SKIN["trunk"], _SKIN["parts"]
    pts = []
    for px in np.arange(L["from_px"], L["to_px"] + 1e-6, L["every_px"]):
        z = (700 - px) / 343; y = (830 - np.interp(px, E[:, 0], E[:, 1])) / 343 - L["below"]
        lo, hi = 0.0, 1.2  # the body's surface along x at (z, y): inside at the midline, outside far out
        for _ in range(30):
            mid = (lo + hi) / 2
            if SK.field(np.array([[mid, y, z]]), trunk, parts)[0] < 0:
                lo = mid
            else:
                hi = mid
        pts.append(mirror([hi + L["out"], y, z], sgn))
    return pts


def wing(sgn):
    """One wing (B["wing"]), built like a bat's arm: the muscled arm, a thumb claw at the wrist, four jointed
    fingers and a short finger from the elbow, all with claws, and the membrane: from the elbow finger across
    to the fingers and between them, scalloped between the tips, and from the elbow finger back along the
    flank to the hip. Built spread (its rest pose, the flying covers) and rigged, so it moves through any
    pose; folded as on the side sheet is a pose of its bones (returned as `fold`), with the flank membrane
    gathered in loose folds along his side (the `wingfold` shape, set with the fold)."""
    Wg = B["wing"]; sd = "L" if sgn > 0 else "R"
    J, tips, _, Rf, fold = wing_pose(sgn)
    out = np.array([0, 1.0, 0])  # spread, the membrane billows up with the air under it
    parts = wing_arm(sgn, sd)
    bones = [(f"wing_humerus.{sd}", tuple(J["shoulder"]), tuple(J["elbow"]), "chest"),
             (f"wing_forearm.{sd}", tuple(J["elbow"]), tuple(J["wrist"]), f"wing_humerus.{sd}")]
    claw_part = lambda name, v, f, bn: H.add_part(name, v, f, {"_PART": [23] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)},
                                                  [[(bn, 1.0)]] * len(v))
    # the thumb: a short digit on the wrist's leading side, ending in a hooked claw
    th = Wg["thumb"]; td = mirror(Rf @ H.norm(np.array(th["direction"], float)), sgn); tb = f"wing_thumb.{sd}"
    t1 = J["wrist"] + td * th["length"]
    parts.append(spar(f"WingThumb{sd}", [J["wrist"], t1], [th["radius"], th["radius"] * 0.8], tb))
    c = th["claw"]; v, f = claw_tube(t1 - td * 0.01, td, c["length"], c["radius"], c["hook_deg"], down=np.array([0, -1.0, 0]))
    parts.append(claw_part(f"WingThumbClaw{sd}", v, f, tb))
    bones.append((tb, tuple(J["wrist"]), tuple(t1), f"wing_forearm.{sd}"))
    # the fingers: a metacarpal to a knuckle, then two phalanges, each bent a little back, to the tip
    # the elbow finger: two segments, a knuckle bulge between them, and a hooked claw
    eb = f"wing_elbowfinger.{sd}"; E = Wg["elbow_finger"]
    ek = J["elbow"] + (J["elbow_tip"] - J["elbow"]) * 0.55
    epts = [J["elbow"], (J["elbow"] + ek) / 2, ek, (ek + J["elbow_tip"]) / 2, J["elbow_tip"]]
    parts.append(spar(f"WingElbowFinger{sd}", epts, E["radius"], eb))
    de = H.norm(J["elbow_tip"] - J["elbow"]); ec = E["claw"]
    v, f = claw_tube(J["elbow_tip"] - de * 0.01, de, ec["length"], ec["radius"], ec["hook_deg"], down=np.array([0, 0, 1.0]))
    parts.append(claw_part(f"WingElbowClaw{sd}", v, f, eb))
    bones.append((eb, tuple(J["elbow"]), tuple(J["elbow_tip"]), f"wing_forearm.{sd}"))
    # the first spar: from the wrist up the forearm to the elbow and out along the elbow finger
    fe = np.linalg.norm(J["elbow"] - J["wrist"]) / (np.linalg.norm(J["elbow"] - J["wrist"]) + np.linalg.norm(J["elbow_tip"] - J["elbow"]))
    spars = [(np.array([J["wrist"], J["elbow"], J["elbow_tip"]]), lambda u, fe=fe: f"wing_forearm.{sd}" if u < fe else eb)]
    fan = H.norm(np.cross(tips[0] - J["wrist"], tips[-1] - J["wrist"]))  # the fan's plane
    Fg, cl = Wg["finger"], Wg["claw"]
    for k, tip in enumerate(tips):
        mb, pb, qb = f"wing_finger{k + 1}.{sd}", f"wing_finger{k + 1}b.{sd}", f"wing_finger{k + 1}c.{sd}"  # metacarpal, two phalanges
        d = H.norm(tip - J["wrist"]); L = np.linalg.norm(tip - J["wrist"])
        back = H.norm(np.cross(fan, d))  # in the fan's plane, toward the trailing edge
        if back[2] > 0:
            back = -back
        bend = lambda a: J["wrist"] + d * L * a + back * L * math.sin(math.pi * a) * math.sin(math.radians(Fg["bend_deg"]))
        kn, kn2 = bend(Fg["knuckle_at"]), bend(Fg["knuckle2_at"])
        pts = [J["wrist"], (J["wrist"] + kn) / 2, kn, (kn + kn2) / 2, kn2, (kn2 + tip) / 2, tip]
        ka, ka2 = Fg["knuckle_at"], Fg["knuckle2_at"]
        seg_bone = lambda a, mb=mb, pb=pb, qb=qb, ka=ka, ka2=ka2: mb if a < ka else (pb if a < ka2 else qb)
        parts.append(spar(f"WingFinger{k}{sd}", pts, Fg["radius"], seg_bone))
        dt = H.norm(tip - kn2)
        v, f = claw_tube(tip - dt * 0.01, dt, cl["length"], cl["radius"], cl["hook_deg"], down=np.array([0, 0, 1.0]))
        parts.append(claw_part(f"WingClaw{k}{sd}", v, f, qb))
        bones += [(mb, tuple(J["wrist"]), tuple(kn), f"wing_forearm.{sd}"), (pb, tuple(kn), tuple(kn2), mb), (qb, tuple(kn2), tuple(tip), pb)]
        spars.append((np.array(pts), seg_bone))
    M = dict(Wg["membrane"], billow=Wg["spread"]["billow"])
    pairs = [(spars[k], spars[k + 1], 0.0) for k in range(len(spars) - 1)]
    # the flank panel: from the wing's root, between the arm (up the humerus to the elbow and out along the
    # elbow finger) and the body (back along the flank just under the carapace's edge to the front of the hip
    # armor), so it meets the whole upper arm and the body with no gap; its trailing edge runs from the
    # elbow finger's claw to the hip. Folded, the humerus lies along
    # the flank and the panel lies flat between them, gathered in loose folds (the wingfold shape)
    arm_line = np.array([J["shoulder"], J["elbow"], J["elbow_tip"]])
    fa = np.linalg.norm(J["elbow"] - J["shoulder"]) / (np.linalg.norm(J["elbow"] - J["shoulder"]) + np.linalg.norm(J["elbow_tip"] - J["elbow"]))
    body = np.array([J["shoulder"]] + membrane_body_line(sgn))
    pairs.append(((arm_line, lambda u, fa=fa: f"wing_humerus.{sd}" if u < fa else eb),
                  (body, lambda u: "chest" if u < 0.5 else "hips"), M["pleats"]["depth"]))
    # membrane panels: between two spars, u from the wrist (0) out to the tips (1), v across; the
    # trailing edge sags back toward the wrist between the tips (the scallop), and the panel billows
    def at(P, u):
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cs = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
        return np.array([np.interp(u, cs, P[:, c]) for c in range(3)])
    nu, nv = 28, 18
    for k, ((PA, ba), (PB, bb), pleat) in enumerate(pairs):
        verts, faces, A, Bq, wts, folds = [], [], [], [], [], []
        if pleat:  # the panel's edges when folded: the folded arm line, and the body line (it doesn't move)
            Rh_, hh = fold["wing_humerus"]; Re_, he = fold["wing_elbowfinger"]
            PAf = np.array([J["shoulder"], he, he + Re_ @ (J["elbow_tip"] - J["elbow"])])
        for i in range(nu + 1):
            for j in range(nv + 1):
                u, vv = i / nu, j / nv
                ue = u * (1 - M["sag"] * math.sin(math.pi * vv))
                # the flank panel (the one with folds) is held taut against the body: only a slight billow, or
                # its body-weighted middle, which doesn't turn with the fold, would stand up above the back
                bil = M["billow"] * (0.2 if pleat else 1.0)
                p = at(PA, ue) * (1 - vv) + at(PB, ue) * vv + out * bil * math.sin(math.pi * vv) * math.sin(math.pi * ue)
                verts.append(tuple(p)); A.append(ue); Bq.append(u)
                if pleat:
                    # folded, the flank membrane spans straight from the folded arm to the body, gathered in soft
                    # folds bulging outward; the wingfold shape puts each point where the fold's bones carry it there
                    target = at(PAf, ue) * (1 - vv) + at(PB, ue) * vv + np.array([sgn * 1.0, 0, 0]) * pleat * abs(
                        math.sin(2 * math.pi * M["pleats"]["count"] * vv)) * math.sin(math.pi * u) * (1 - u) ** 0.5
                    wv = vv ** 4 if 0 < vv < 1 else float(vv == 1)
                    Ra, ha = (Rh_, hh) if ba(ue) == f"wing_humerus.{sd}" else (Re_, he)
                    ra = J["shoulder"] if ba(ue) == f"wing_humerus.{sd}" else J["elbow"]
                    Am = (1 - wv) * Ra + wv * np.eye(3); c = (1 - wv) * (ha - Ra @ ra)
                    folds.append(tuple(np.linalg.solve(Am, target - c)))
                # the flank panel's body edge holds only a strip next to the body; the rest rides the arm, so it
                # folds in with it rather than staying out where the spread wing was
                wv = vv ** 4 if pleat else vv
                wts.append([(ba(ue), 1 - wv), (bb(ue), wv)] if 0 < vv < 1 else [((ba if vv == 0 else bb)(ue), 1.0)])
        for i in range(nu):
            for j in range(nv):
                a = i * (nv + 1) + j
                faces.append([a, a + 1, a + nv + 2, a + nv + 1])
        ob = H.add_part(f"WingMembrane{k}{sd}", verts, faces, {"_PART": [25] * len(verts), "_A": A, "_B": Bq, "_ZONE": [0] * len(verts)}, wts)
        if pleat:
            ob.shape_key_add(name="Basis", from_mix=False)
            ob.shape_key_add(name="wingfold", from_mix=False).data.foreach_set("co", H.to_blender(np.array(folds)).astype(np.float32).ravel())
        parts.append(ob)
    return parts, bones, {f"{n}.{sd}": v for n, v in fold.items()}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tb, ranges = trunk_bones()
    objs, head_bones = H.head_parts()
    skin_setup()
    trim_head(objs)
    ear = [o for o in objs if o.name.startswith("Frill")]
    ear_pts = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in ear]) if ear else None
    if ear_pts is not None:
        ear_pts = np.stack([ear_pts[:, 0], ear_pts[:, 2], -ear_pts[:, 1]], 1)  # Blender's frame back to the model's
    objs += skin_parts(ranges, ear_pts)
    objs += spike_parts(ranges, band)
    neck_end = TR["bones"]["chain_forward"][-1][0]
    bones = tb + [(n, h, t, p or neck_end) for n, h, t, p in head_bones]
    fold = {}
    for sgn in (1, -1):
        for leg in (front_leg, hind_leg):
            parts, lb = leg(sgn)
            objs += parts; bones += lb
        parts, lb, fd = wing(sgn)
        objs += parts; bones += lb; fold.update(fd)
    # the wings rest spread; "wings_fold" (spread at 0, folded at 1) takes them to the side sheet's folded pose
    H.assemble(objs, bones, OUT, "ClayRig", clips={"wings_fold": fold})


if __name__ == "__main__":
    main()
