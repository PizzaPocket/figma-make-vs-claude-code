"""Clay's head as fitted architectural pieces, built in Blender from measured data.

Pieces (see head_design.json and head_sheets.md):
- face: the orange mass of muzzle, cheeks and skull, a clean quad loft of measured stations
  shaped from the inside out by anatomy layers: bone landmarks, muscle masses, skin creases;
- roof: the dark banded shell fitted over the face, standing proud so its eave overhangs
  the orange; its back corners continue as the horns;
- nose crest: a raised pad on the front of the roof with the nostrils under its flares;
- lower jaw on a hinge, mouth interior, teeth, and a tongue on its own bone chain;
- eyes, and lids that are shells hinged on the canthal axis; ear frills under the horns.
Model space: x = Clay's left, y = up, z = forward; 1 unit = 343 px of the reference.
"""
import json
import math
import os
import sys

import bpy  # bmesh is only importable once bpy is loaded
import numpy as np

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
OUT = ARGS.get("--out", "head.glb")

# ---------------------------------------------------------------- measurements (head_design.json)
D = json.load(open(ARGS.get("--design", os.path.join(os.path.dirname(os.path.abspath(__file__)), "head_design.json"))))
UPPER = np.array(D["upper_head"]["rows"])
SQ = D["upper_head"].get("squareness", 3.6)  # higher = crisper edge between top and side planes
JAW = np.array(D["lower_jaw"]["rows"])
HINGE = tuple(D["lower_jaw"]["hinge"])
EYE = D["eye"]
PLATE_EDGE = np.array(D["dark_plate_edge"]["zy"])
ROOF = D["roof"]
PLATES = D["roof_plates"]
CREST = D["nose_crest"]
HORN = D["horn"]
FRILL = D["ear_frill"]
N_AROUND = 96  # points around the face contour (fine enough to carry the lid creases)


def interp(table, z, col):
    return float(np.interp(-z, -table[:, 0], table[:, col]))


def norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


BRUSHES = [b for layer in ("bone", "muscle", "skin") for b in D["anatomy"][layer] if b["kind"] != "note"]


def seg_dist(z, y, pts):
    """Side-view (z, y) distance from a point to a polyline; whether the point is above it (judged on
    the nearest segment's interior, so the sign never jumps at a joint); and the distance from the
    polyline's nearer end, measured along it (for tapering)."""
    best, above, along, total = 1e9, True, 0.0, 0.0
    for (az, ay), (bz, by) in zip(pts[:-1], pts[1:]):
        dz, dy = bz - az, by - ay
        L2 = dz * dz + dy * dy
        t = ((z - az) * dz + (y - ay) * dy) / L2
        tc = max(0.0, min(1.0, t))
        d = math.hypot(z - az - tc * dz, y - ay - tc * dy)
        if d < best:
            best, along = d, total + tc * math.sqrt(L2)
            above = (dz * (y - ay) - dy * (z - az)) * (1 if dz < 0 else -1) >= 0
        total += math.sqrt(L2)
    return best, above, min(along, total - along)


def rim_radius(pts, ref, z, y):
    """Distance from `ref` to the polyline's nearest point to (z, y): which side of a rim we are on."""
    best, rr = 1e9, 0.0
    for (az, ay), (bz, by) in zip(pts[:-1], pts[1:]):
        dz, dy = bz - az, by - ay
        t = max(0.0, min(1.0, ((z - az) * dz + (y - ay) * dy) / (dz * dz + dy * dy)))
        cz, cy = az + t * dz, ay + t * dy
        d = math.hypot(z - cz, y - cy)
        if d < best:
            best, rr = d, math.hypot(cz - ref[0], cy - ref[1])
    return rr


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def brush_offset(z, y):
    """Outward (+) / inward (-) offset of the side surface from the anatomy layers (bone, muscle, skin).
    Nothing raises the skin where the eye sits: the lids and eye fill that opening, and the bone and
    muscle forms only frame it."""
    off, dents = 0.0, 0.0
    ec = EYE["centre_zy"]; clear = EYE["clear_radius"]
    frame = smoothstep(clear[0], clear[1], math.hypot(z - ec[0], y - ec[1]))
    for b in BRUSHES:
        k = b["kind"]
        if k == "dent":
            d = math.hypot(z - b["zy"][0], y - b["zy"][1])
            dents -= b["depth"] * math.exp(-(d / b["radius"]) ** 2)
        elif k == "bulge":  # a muscle belly: elliptical, full in the middle
            (cz, cy), (rz, ry) = b["centre"], b["radii"]
            off += b["amount"] * math.exp(-((z - cz) / rz) ** 2 - ((y - cy) / ry) ** 2)
        elif k == "pad":  # a raised plateau in a tilted ellipse (the lid ring)
            (cz, cy), (ra, rb) = b["centre"], b["radii"]
            t = math.radians(b["tilt_deg"])
            along = -(z - cz) * math.cos(t) + (y - cy) * math.sin(t)
            across = (z - cz) * math.sin(t) + (y - cy) * math.cos(t)
            e = math.hypot(along / ra, across / rb)
            off += b["height"] * (1 - smoothstep(1 - b["softness"], 1 + b["softness"], e))
        elif k == "rim":  # a bony rim round an opening: gentle on the side toward `around`, crisp on the outside
            d, _, end = seg_dist(z, y, b["zy"])
            ref = b["around"]
            outside = math.hypot(z - ref[0], y - ref[1]) > rim_radius(b["zy"], ref, z, y)
            w = b["width_out"] if outside else b["width_in"]
            off += b["height"] * math.exp(-(d / w) ** 2) * smoothstep(-0.01, 0.04, end)
        else:
            d, _, end = seg_dist(z, y, b["zy"])
            amt = b["height"] if k == "ridge" else -b["depth"]
            off += amt * math.exp(-(d / b["width"]) ** 2) * smoothstep(-0.01, 0.02, end)
    return off * frame + dents


# ---------------------------------------------------------------- face
def snout_ridge(z):
    """Height of the ridge along the middle of the roof's top: the roof is a gable, two mirrored slopes meeting
    at a crisp ridge down its whole length."""
    R = np.array(D["upper_head"]["ridge"])
    return float(np.interp(-z, -R[:, 0], R[:, 1]))


def front_setback(x, y):
    """How far the front muzzle's face sits forward (+) of the front station at (x, y): rounded across (convex
    from above, the middle forward of the sides) and dipping in just under the nose (concave in profile). Both
    vanish at the face's outline, where it joins the sides."""
    F = D["upper_head"]["front"]
    z0 = UPPER[0, 0]
    lo, top = interp(UPPER, z0, 2), interp(UPPER, z0, 1)
    q = min(1.0, max(0.0, (y - lo) / (top - lo)))
    xo = abs(face_pt(z0, side_th(z0, min(max(y, lo + 1e-4), top - 1e-4)))[0]) or 1e-6
    across = max(0.0, 1 - (x / xo) ** 2) * (1 - smoothstep(0.8, 1.0, q))  # zero all round the outline, its peak included
    # convex forward both ways: rounded across from above, and bulging in side profile between the nose and the lip
    return across * (F["convex"] + F.get("convex_side", 0.0) * math.sin(math.pi * q) - F["concave"] * math.sin(math.pi * q ** 0.8))


def corner_lift(z, x, wb):
    """How far the upper jaw's lower edge is pulled up at x, at station z: at the front muzzle its front lip edge
    arcs down in the middle and its bottom corners pull up before the lip turns back along the side."""
    F = D["upper_head"]["front"]
    return F["corner_lift"] * smoothstep(F["block_back_z"], UPPER[0, 0], z) * min(1.0, abs(x) / wb) ** F.get("lip_arc_power", 2)


def face_pt(z, th):
    """Point on the face at station z, angle th (0 = left lip edge, pi/2 = top, pi = right lip edge).
    Boxy cross-section (flat top, steep sides, cheeks wider than the top), then the brushes."""
    top, low, wt, wb = (interp(UPPER, z, c) for c in (1, 2, 3, 4))
    b = top - low
    c, s = math.cos(th), math.sin(th)
    yy = b * abs(s) ** (2 / SQ)
    a = wb + (wt - wb) * (yy / b) ** 1.6
    x = a * math.copysign(abs(c) ** (2 / SQ), c)
    # gable: straight slopes down from a crisp ridge; the ridge stays on the measured profile, the shoulders drop
    y = low + yy - snout_ridge(z) * min(1.0, abs(x) / (wt * 0.98)) * (yy / b) ** 4
    y += corner_lift(z, x, wb) * (1 - yy / b) ** 2  # the front's bottom corners pull up
    side = min(1.0, max(0.0, (abs(x) / wb - 0.35) / 0.4))  # brushes act on the sides, fading out on the top
    return x + math.copysign(brush_offset(z, y) * side, x), y


def face_normal(z, th):
    th = min(max(th, 2e-3), math.pi - 2e-3)  # the contour folds back on itself past the lip edges
    x0, y0 = face_pt(z, th - 1e-3)
    x1, y1 = face_pt(z, th + 1e-3)
    tx, ty = x1 - x0, y1 - y0
    L = math.hypot(tx, ty)
    return ty / L, -tx / L


def upper_contour(z):
    low, wb = interp(UPPER, z, 2), interp(UPPER, z, 4)
    return [face_pt(z, math.pi * i / N_AROUND) for i in range(N_AROUND + 1)], (lambda x: low + corner_lift(z, x, wb))


def jaw_contour(z):
    top, bot, w = (interp(JAW, z, c) for c in (1, 2, 3))
    b = top - bot
    pts = []
    for i in range(N_AROUND + 1):
        th = math.pi * i / N_AROUND  # 0 = one edge, pi/2 = chin bottom, pi = other edge
        c, s = math.cos(th), math.sin(th)
        n = D["lower_jaw"].get("squareness", 2.6)
        x = w * math.copysign(abs(c) ** (2 / n), c)
        pts.append((x, top - b * abs(s) ** (2 / n)))
    return pts, top


# ---------------------------------------------------------------- roof and nose crest
def roof_t(z):
    """Shell thickness: overlapping bands, each thickest at its back edge."""
    f = ((ROOF["front_z_band_origin"] - z) / ROOF["band"]) % 1.0
    return ROOF["thickness"][0] + (ROOF["thickness"][1] - ROOF["thickness"][0]) * f, f


def eave_th(z):
    """Face angle at which the roof's eave sits (0 = the roof reaches the lip)."""
    top, low = interp(UPPER, z, 1), interp(UPPER, z, 2)
    ye = float(np.interp(-z, -PLATE_EDGE[:, 0], PLATE_EDGE[:, 1]))
    if ye <= low + 1e-4:
        return 0.0
    q = min(1.0, (ye - low) / (top - low))
    return min(math.asin(q ** (SQ / 2)), math.pi / 2 - 0.08)


def roof_ring(z, K=27):  # odd, so one sample sits on the ridge
    the = eave_th(z)
    t, f = roof_t(z)
    outer, inner = [], []
    for i in range(K):
        th = the + (math.pi - 2 * the) * i / (K - 1)
        x, y = face_pt(z, th)
        nx, ny = face_normal(z, th)
        outer.append((x + nx * t, y + ny * t, z))
        inner.append((x - nx * ROOF["inset"], y - ny * ROOF["inset"], z))
    return outer, inner, f


def crest_height(z, th):
    """A pad sculpted into the nose plate along the top front of the muzzle (none at present: the nose is its
    own piece, nose_part). Returns (height above the plate, nostril weight)."""
    st = np.array(CREST.get("stations", []))
    if not len(st) or not (st[-1, 0] <= z <= st[0, 0]):
        return 0.0, 0.0
    half, h = (float(np.interp(-z, -st[:, 0], st[:, c])) for c in (1, 2))
    u = (th - math.pi / 2) / max(half, 1e-6)
    return (h * (1 - u * u) ** 0.8 if abs(u) < 1 else 0.0), 0.0


def shield(W, H, drop, r, n=16, bulge=0.0):
    """The nose's section, like the border of the Superman shield: a flat top with square corners, short
    sides falling straight down, then two lower edges converging to a point at the bottom. Corners rounded
    with radius r; each straight edge swells outward by bulge (a fraction of its length), so the faces are softly
    convex. Returns (x, v) points counter-clockwise from the bottom point, and each point's side:
    0 top, 1 upright side, 2 lower edge (the undersides, where the nostrils open)."""
    P = [(0.0, -H), (W / 2, -drop), (W / 2, 0.0), (-W / 2, 0.0), (-W / 2, -drop)]
    out, tag = [], []
    for i, c in enumerate(P):
        p, q = np.array(P[i - 1]), np.array(P[(i + 1) % len(P)])
        c = np.array(c); a1, a2 = norm(p - c), norm(q - c)
        half = math.acos(max(-1.0, min(1.0, a1 @ a2))) / 2
        # never round further than 45% along either edge (a short side would otherwise fold into a spike)
        dcut = min(r / math.tan(half), 0.45 * min(np.linalg.norm(p - c), np.linalg.norm(q - c)))
        r_c = dcut * math.tan(half)
        s0, s1 = c + a1 * dcut, c + a2 * dcut
        ctr = c + norm(a1 + a2) * r_c / math.sin(half)
        u0, u1 = math.atan2(*(s0 - ctr)[::-1]), math.atan2(*(s1 - ctr)[::-1])
        du = (u1 - u0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n + 1):
            u = u0 + du * k / n
            out.append(tuple(ctr + r_c * np.array([math.cos(u), math.sin(u)])))
            tag.append({0: 2, 1: 2, 2: 1, 3: 0, 4: 1}[i] if k < n // 2 else {0: 2, 1: 1, 2: 0, 3: 1, 4: 2}[i])
        # the straight edge to the next corner, divided so the faces can be sculpted (the nostrils)
        out.append(None); tag.append({0: 2, 1: 1, 2: 0, 3: 1, 4: 2}[i])
    pts = []
    for j, p in enumerate(out):
        if p is not None:
            pts.append((p, tag[j])); continue
        a, b = np.array(out[j - 1]), np.array(out[(j + 1) % len(out)])
        m = max(2, int(np.linalg.norm(b - a) / 0.004))
        nrm = np.array([b[1] - a[1], -(b[0] - a[0])]) / (np.linalg.norm(b - a) + 1e-9)  # outward (the outline runs counter-clockwise)
        pts += [(tuple(a + (b - a) * q / m + nrm * bulge * np.linalg.norm(b - a) * math.sin(math.pi * q / m)), tag[j]) for q in range(1, m)]
    return [p for p, _ in pts], [g for _, g in pts]


def nose_part():
    """The nose: one extruded mass emerging out of the roof, pitched upward, its section like the border of the
    Superman shield (flat top, short upright sides, lower edges converging to a point). It juts forward out of
    the snout's front above the front lip, with a flat upright front face; its back sinks into the roof. The nostrils
    are slits cut into its two lower faces, near the front. _ZONE: nostril."""
    NS = D["nose"]
    sec, tag = shield(NS["width"], NS["height"], NS["side_drop"], NS["corner_radius"], bulge=NS.get("bulge", 0.0))
    p = math.radians(NS["pitch_deg"])
    ax = np.array([0.0, math.sin(p), math.cos(p)])      # forward and up
    up = np.array([0.0, math.cos(p), -math.sin(p)])     # the section's v direction
    front = np.array([0.0, NS["front_top_zy"][1], NS["front_top_zy"][0]])  # middle of the front face's top edge
    N = NS["nostril"]
    # the front face is upright (a plane of constant z through the top edge), so the whole shield shows from the
    # front, its point below jutting as far forward as its top; each section point runs back from there
    t_end = lambda v: -(up[2] * v) / ax[2]
    back = np.concatenate([np.linspace(NS["length"], 0.07, 12), np.linspace(0.068, 0.0, 40)])  # distance back from the front face
    rings, A, NW = [], [], []
    for db in back:
        ring, a_r, n_r = [], [], []
        for (x, v), tg in zip(sec, tag):
            t = -db
            sink = NS.get("sink", 0.0) * smoothstep(NS.get("emerge", 0.0), NS["length"], db)  # the back dips under the roof's surface
            pt = front + ax * (t_end(v) + t) + up * (v - sink) + np.array([x, 0, 0])
            nw = 0.0
            if tg == 2:  # a nostril on each lower face: a slit along the axis, wide at the front end
                s = (t - N["t_front"]) / (N["t_back"] - N["t_front"])
                across = (abs(x) / (NS["width"] / 2)) - N["across"]
                if -0.2 < s < 1.2:
                    w = N["half_width"][0] + (N["half_width"][1] - N["half_width"][0]) * min(1.0, max(0.0, s))
                    ends = smoothstep(-0.15, 0.05, s) * (1 - smoothstep(0.9, 1.1, s))
                    g = smoothstep(0.0, 1.0, max(0.0, 1 - abs(across) / w)) * ends
                    if g > 0:  # cut in toward the middle of the nose's section
                        core = front + ax * (t_end(v) + t) - up * (NS["height"] * 0.45 + sink)
                        pt = pt + norm(core - pt) * N["depth"] * g
                        nw = smoothstep(0.35, 0.8, g)
            ring.append(tuple(pt)); a_r.append(0.02); n_r.append(nw)
        rings.append(ring); A.append(a_r); NW.append(n_r)
    # the front face: its rim rounds over (a quarter round of radius front_round), then it is flat
    last = np.array(rings[-1])
    fwd = np.array([0.0, 0.0, 1.0])
    S = np.array(sec); M2 = len(S)
    n2 = np.array([norm(np.array([S[(i + 1) % M2][1] - S[i - 1][1], -(S[(i + 1) % M2][0] - S[i - 1][0])])) for i in range(M2)])  # outward, in the section
    rf = NS.get("front_round", 0.004)
    for a in np.radians([20, 40, 60, 75, 90]):
        ring = [tuple(q - (np.array([n2[i][0], 0, 0]) + up * n2[i][1]) * rf * (1 - math.cos(a)) + fwd * rf * math.sin(a)) for i, q in enumerate(last)]
        rings.append(ring); A.append([0.0] * len(last)); NW.append([0.0] * len(last))
    verts, faces, AA, NN = [], [], [], []
    M = len(rings[0])
    for r, a_r, n_r in zip(rings, A, NW):
        verts += r; AA += a_r; NN += n_r
    for i in range(len(rings) - 1):
        for j in range(M):
            k = (j + 1) % M
            p0 = i * M + j; q0 = p0 + M
            faces.append([p0, i * M + k, (i + 1) * M + k, q0])
    for i in (0, len(rings) - 1):
        cidx = len(verts); verts.append(tuple(np.mean(rings[i], 0))); AA.append(0.0); NN.append(0.0)
        for j in range(M):
            k = (j + 1) % M
            faces.append([i * M + k, i * M + j, cidx] if i == 0 else [i * M + j, i * M + k, cidx])
    return verts, faces, [0.02] * len(verts), [0.45] * len(verts), NN


def shell_loft(rings, attrs_per_ring):
    """rings: list of (outer, inner) point lists; builds a closed shell (outer, rim, inner) with caps."""
    verts, faces, A, B, Z = [], [], [], [], []
    idx = []
    for (outer, inner), (a, bvals) in zip(rings, attrs_per_ring):
        K = len(outer)
        ring = []
        for i, p in enumerate(outer):
            ring.append(len(verts)); verts.append(p); A.append(a); B.append(bvals[i]); Z.append(i / (K - 1))
        for i, p in enumerate(reversed(inner)):
            ring.append(len(verts)); verts.append(p); A.append(a); B.append(0.0); Z.append(-1.0)
        idx.append(ring)
    M = len(idx[0])
    for k in range(len(idx) - 1):
        r0, r1 = idx[k], idx[k + 1]
        for i in range(M):
            j = (i + 1) % M
            faces.append([r0[i], r0[j], r1[j], r1[i]])
    K = len(rings[0][0])  # the front end: no face across it, just the thin rim joining the outer and inner layers
    r = idx[0]
    for i in range(K - 1):
        faces.append([r[i + 1], r[i], r[2 * K - 1 - i], r[2 * K - 2 - i]])
    for k in (len(idx) - 1,):  # capped at the back
        r = idx[k]
        n = len(r)
        c = len(verts)
        verts.append(tuple(np.mean([verts[i] for i in r], 0))); A.append(A[r[0]]); B.append(0.0); Z.append(0.5)
        for i in range(n):
            j = (i + 1) % n
            faces.append([r[j], r[i], c] if k == 0 else [r[i], r[j], c])
    return verts, faces, A, B, Z


_HORN_AXES = {}


def horn_axis(sgn):
    """Centreline and radii of one horn, sampled along its spline."""
    if sgn not in _HORN_AXES:
        path = [[sgn * p[0], p[1], p[2]] for p in HORN["path"]]
        C, R, _, _, _ = spline_frames(path, HORN["radius"], 0.004)
        _HORN_AXES[sgn] = (C, R)
    return _HORN_AXES[sgn]


def horn_fillet(q, n, edge):
    """Sculpt the horn's root into the roof: move a roof point out along its normal n onto the smooth
    union of the roof and the horn (exponential smooth-min, radius HORN['fillet']), so the plates
    swell up into the horn and wrap its base instead of the horn being stuck on."""
    k = HORN["fillet"]
    for sgn in (1, -1):
        if q[0] * sgn < 0.05:
            continue
        C, R = horn_axis(sgn)
        if np.min(np.linalg.norm(C - q, axis=1) - R) > 4 * k:
            continue
        def f(t):
            p = q + n * t
            a, b = t, float(np.min(np.linalg.norm(C - p, axis=1) - R))
            return -k * math.log(math.exp(-a / k) + math.exp(-b / k))
        lo, hi = 0.0, 0.0
        while f(hi) < 0 and hi < 0.2:
            hi += 0.01
        for _ in range(22):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
        return q + n * hi * edge
    return q


# ---------------------------------------------------------------- roof plate layout
# The plates are laid out in side-view coordinates that follow the head's top profile, as the art draws
# them: s runs along the profile from the nose tip back, d is the depth below it, perpendicular to it.
# Joints between plates are lines of constant s (perpendicular to the profile, so nearly level in the side
# view on the steep muzzle); the strips along the side are lines of constant d.
_PROFILE = {}


def profile():
    if not _PROFILE:
        zs = np.linspace(UPPER[0, 0], ROOF["back_z"] - 0.02, 400)  # from the flat front edge, where the roof meets the front face
        ys = np.array([interp(UPPER, z, 1) + roof_t(z)[0] for z in zs])
        P = np.stack([zs, ys], 1)
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
        # smooth the direction along the profile (over ~0.06): the joints follow the profile's overall flow, and
        # neighbouring joint lines never cross where the profile bends sharply (they would fold the plates)
        k = np.exp(-0.5 * (np.arange(-75, 76) / 25.0) ** 2)
        Tp = np.pad(T, ((75, 75), (0, 0)), mode="edge")
        T = np.stack([np.convolve(Tp[:, c], k / k.sum(), mode="valid") for c in (0, 1)], 1)
        T /= np.linalg.norm(T, axis=1)[:, None]
        Nin = np.stack([T[:, 1], -T[:, 0]], 1)  # perpendicular, pointing down into the head
        Nin[Nin[:, 1] > 0] *= -1
        _PROFILE.update(P=P, s=s, N=Nin)
    return _PROFILE


def sv_point(s, d):
    """Side-view point at profile position s and depth d."""
    pr = profile()
    p = np.array([np.interp(s, pr["s"], pr["P"][:, k]) for k in (0, 1)])
    n = np.array([np.interp(s, pr["s"], pr["N"][:, k]) for k in (0, 1)])
    return p + norm(n) * d


def side_th(z, y):
    """Face angle on the +x side at which the face reaches height y at station z."""
    lo, hi = 0.0, math.pi / 2
    if y >= face_pt(z, hi)[1]:
        return hi
    if y <= face_pt(z, lo)[1]:
        return lo
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if face_pt(z, mid)[1] < y else (lo, mid)
    return (lo + hi) / 2


def eave_depth(s):
    """Depth of the roof's eave below the profile at s (found to within 1e-5, so neighbouring plate rows
    end smoothly instead of in 0.002 steps, which ridge a finely divided plate)."""
    def below(d):
        z, y = sv_point(s, d)
        return y <= float(np.interp(-z, -PLATE_EDGE[:, 0], PLATE_EDGE[:, 1])) or y <= interp(UPPER, z, 2) + 0.012  # short of the lip's edge
    d = 0.0
    while d < 0.4 and not below(d):
        d += 0.002
    lo, hi = max(0.0, d - 0.002), d
    for _ in range(8):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if below(mid) else (mid, hi)
    return hi


def chamfer(dist):
    """A tile's edge profile: a short wall, then a narrow 45-degree chamfer up to its full thickness."""
    c = PLATES["chamfer"]
    return 0.0 if dist < 1e-9 else min(1.0, 0.5 + 0.5 * dist / c)


def edge_samples(n, frac):
    """0..1 in n steps, plus a sample just inside each end (frac), so a tile's edge is a crisp wall."""
    return sorted(set([0.0, frac, 1 - frac, 1.0] + [k / n for k in range(1, n)]))


def plate(s0, s1, d0, d1, nv, seed, wrap=False, thick=None, flare=0.0, step=0.004, open_front=False):
    """One roof plate: a solid tile of even thickness with crisp chamfered edges, laid on the underlay over
    profile positions s0..s1 and depths d0..d1 (d1 may be a function of s). With wrap=+1 or -1 it is one
    side of the gable, from the ridge down to depth d1 (the roof's plates meet at the ridge in mirrored
    pairs). _A: distance to its nearest edge, _B: tint, _ZONE: 0."""
    T, gap = thick or PLATES["thickness"], PLATES["gap"]
    s0g, s1g = s0 + gap / 2, s1 - gap / 2
    Ls = s1g - s0g
    us = edge_samples(max(4, int(Ls / step)), PLATES["chamfer"] * 0.3 / Ls)
    tint = (math.sin(seed * 12.9898) * 43758.5453) % 1.0
    D1 = d1 if callable(d1) else (lambda s, v=d1: v)
    rows = []
    for u in us:
        sc = s0g + Ls * u
        dh = D1(sc) - gap / 2
        row = []
        if wrap:
            za, ya = sv_point(sc, dh); tha = side_th(za, ya)
            zt = sv_point(sc, 0.0)[0]
            for w in edge_samples(nv, 0.012):
                v = wrap * w ** 1.3 if wrap is not True else -1 + 2 * w
                z = zt + (za - zt) * abs(v)  # the joint runs straight from the ridge to the plate's lower end
                th = math.pi / 2 - v * (math.pi / 2 - tha)
                if open_front and u == 0.0:
                    # an open front edge follows the front face's convex curve, where the front ridge carries on from it
                    xf, yf = face_pt(zt, th)
                    z = zt + front_setback(xf, yf)
                row.append((z, th, w))
        else:
            dl = d0 + gap / 2
            for w in edge_samples(nv, 0.03):
                z, y = sv_point(sc, dl + (dh - dl) * w)
                row.append((z, side_th(z, y), w))
        rows.append(row)
    under = roof_t(sv_point(s0, 0)[0])[0]
    verts, A, B, NW = [], [], [], []
    for u, row in zip(us, rows):
        pts = [np.array(face_pt(z, th)) for z, th, _ in row]
        acc = np.concatenate([[0], np.cumsum([np.linalg.norm(pts[k + 1] - pts[k]) for k in range(len(pts) - 1)])])
        Lv = acc[-1] + 1e-6
        for j, (z, th, w) in enumerate(row):
            x, y = pts[j]; nx, ny = face_normal(z, th)
            dist = min(1.0 if open_front else u * Ls, (1 - u) * Ls, acc[j], Lv - acc[j])  # open_front: no edge at the front (it carries on)
            edge = chamfer(dist)
            rim = flare * smoothstep(0.55, 1.0, w) if not wrap else 0.0  # a rim scute's lower edge rolls outward, like a turtle shell's margin
            h = (T + rim) * edge
            for sgn in ((1, -1) if not wrap else (1,)):
                xs = x if wrap else sgn * x
                ns = nx if wrap else sgn * nx
                q = np.array([xs + ns * (under + h), y + ny * (under + h), z])
                q = horn_fillet(q, np.array([ns, ny, 0.0]), edge)
                verts.append(tuple(q)); A.append(dist); B.append(tint); NW.append(0.0)
    n_side = 1 if wrap else 2
    nvv = len(rows[0]) - 1
    skirt = front_skirt(verts[:nvv + 1], under, T) if open_front else []
    faces = []
    W = (nvv + 1) * n_side
    for i in range(len(rows) - 1):
        for j in range(nvv):
            for k in range(n_side):
                q0 = i * W + j * n_side + k
                q1 = q0 + n_side
                f = [q0, q1, q1 + W, q0 + W]
                faces.append(f if (k == 0) else f[::-1])
    if skirt:  # the same plate carries on down over the front face: more rows, stitched to its front row
        prev = list(range(nvv + 1))
        for srow in skirt:
            cur = []
            for p in srow:
                cur.append(len(verts)); verts.append(tuple(p)); A.append(0.02); B.append(tint); NW.append(0.0)
            for j in range(nvv):
                faces.append([cur[j], cur[j + 1], prev[j + 1], prev[j]])
            prev = cur
    return verts, faces, A, B, NW


def front_skirt(front_row, under, T):
    """The roof's front band carried on down over the front of the snout, as more rows of the same plate: from
    its open front edge (front_row) down to the orange front muzzle at the eave, lying on the convex front face
    at the plate's thickness, and at the bottom rolling in to the face in a small rounded step. This is the
    front ridge: one piece with the band, so there is no seam."""
    R = D["upper_head"]["front"]["ridge"]
    z0 = UPPER[0, 0]
    ye, step = R["eave_y"], R["edge_step"]
    K = 14
    rows = []
    for k in range(1, K + 1):
        f = k / K
        row = []
        for p in front_row:
            x0, y0, zp = p
            # the bottom line rises at the corners with the front muzzle's lifted lower edge, staying above it
            yex = max(ye, interp(UPPER, z0, 2) + corner_lift(z0, x0, interp(UPPER, z0, 4)) + R["above_lip"])
            y = y0 + (yex - y0) * f
            xo = abs(face_pt(z0, side_th(z0, min(max(y, interp(UPPER, z0, 2) + 1e-4), face_pt(z0, math.pi / 2)[1] - 1e-4)))[0]) + under + T
            x = max(-xo, min(xo, x0))
            thick = step + (T - step) * (1 - smoothstep(0.6, 1.0, f))  # thins toward the bottom edge
            zt = z0 + front_setback(x, y) + under + thick
            # where the band's front edge is already down at the eave (its lower ends) there is nothing to cover:
            # the rows collapse onto the edge instead of folding
            reach = smoothstep(0.0, 0.025, y0 - yex)
            if reach < 1e-3:
                row.append((x0, y0, zp)); continue
            row.append((x0 + (x - x0) * reach, y, zp + (zt - zp) * smoothstep(0.0, 0.35, f) * reach))
        rows.append(row)
    rows.append([(x, y - 0.002, z - step) for x, y, z in rows[-1]])  # the bottom edge rolls in to the face
    return rows


def roof_plates():
    """The roof, in few pieces of one kind: bands of tiles from the roof's front edge back, each a mirrored
    pair meeting at the ridge and running down each side to the rim; the rim of square marginal scutes
    down to the eave. There is no plate on the front face."""
    L = PLATES["layout"]
    pr = profile(); smax = pr["s"][-1]
    out, seed = [], 0  # no plate on the front face: the references draw none there
    for row in L["rows"]:
        sc = 0.0  # the bands start at the roof's front edge
        while sc < smax - 0.01:
            s1 = min(smax, sc + row["joint_every"])
            dlo = row["d"][0]
            dhi = (lambda s, cap=row["d"][1]: min(cap, eave_depth(s) - 0.002)) if row["d"][1] is not None else (lambda s: eave_depth(s) - 0.002)
            if row.get("wrap") and sc == 0.0:
                # the front band is one piece, not a mirrored pair: it wraps over the ridge down to the eave and carries
                # on, with no edge, into the front ridge over the front face (front_ridge)
                out.append(plate(sc, s1, 0.0, lambda s: eave_depth(s) - 0.002, 20, 10 + seed, wrap=True, open_front=True))
            elif row.get("wrap"):
                # where the rim below would be too thin to be a plate (at the front, the eave comes up close), the
                # band runs on down to the eave instead
                cap = row["d"][1]
                if min(eave_depth(sc), eave_depth(s1)) - 0.002 - cap < L.get("min_rim", 0.025):
                    dh2 = lambda s: eave_depth(s) - 0.002
                else:
                    dh2 = dhi
                for side in (1, -1):
                    out.append(plate(sc, s1, 0.0, dh2, 10, 10 + seed, wrap=side))
            elif sc > 0.0 and min(eave_depth(sc), eave_depth(s1)) - 0.002 - dlo >= L.get("min_rim", 0.025):
                out.append(plate(sc, s1, dlo, dhi, 6, 10 + seed, thick=row.get("thickness"), flare=row.get("rim_flare", 0.0)))
            sc = s1; seed += 1
    return out


def eye_seat(sgn):
    """Eye centre and the face normal there: the eyeball is seated along the face's true normal
    at the eye centre (the side of the head slopes forward)."""
    ez, ey, er = EYE["centre_zy"][0], EYE["centre_zy"][1], EYE["radius"]
    th = min(np.linspace(0.01, 1.55, 3000), key=lambda q: abs(face_pt(ez, q)[1] - ey))
    p0 = np.array([*face_pt(ez, th), ez])
    dth = np.array([*face_pt(ez, th + 1e-3), ez]) - np.array([*face_pt(ez, th - 1e-3), ez])
    dz = np.array([*face_pt(ez + 1e-3, th), ez + 1e-3]) - np.array([*face_pt(ez - 1e-3, th), ez - 1e-3])
    nf = norm(np.cross(dz, dth)); nf = nf if nf[0] > 0 else -nf
    c = p0 - nf * er * EYE["sink"]
    return c * np.array([sgn, 1, 1]), nf * np.array([sgn, 1, 1])


def carve_socket(V):
    """Carve the eye sockets into the face: inside the lids' footprint the skin runs in under the lid
    dome and, inside the lid shell, back behind the eyeball; a rounded rim turns it back out to the face."""
    S = EYE["socket"]; er = EYE["radius"]
    Ro = er * (EYE["lid_scale"] + EYE["lid_thickness"])
    rho_r = Ro * S["rim_frac"]
    Re = er * 1.04  # never carve into the eyeball itself
    hd = lambda r: max(math.sqrt(max(0.0, Ro * Ro - r * r)) - S["under"], math.sqrt(max(0.0, Re * Re - r * r)))
    V = V.copy()
    for sgn in (1, -1):
        c, nf = eye_seat(sgn)
        for i, p in enumerate(V):
            if p[0] * sgn <= 0:
                continue
            q = p - c; h = q @ nf; rho = np.linalg.norm(q - h * nf)
            if rho > rho_r + S["rim_width"]:
                continue
            s = smoothstep(rho_r, rho_r + S["rim_width"], rho)
            target = hd(min(rho, rho_r)) * (1 - s) + h * s
            k = 0.003  # smooth minimum: the skin rolls into the socket instead of stepping
            hn = -k * math.log(math.exp(-h / k) + math.exp(-target / k))
            if hn < h:
                V[i] = p + nf * (hn - h)
            # inside the lids the skin goes in behind the eyeball, never over it: the lids and the eye fill the
            # opening, so no skin can show between the eyeball and the lid margin
            q = V[i] - c; dist = np.linalg.norm(q)
            w = 1 - smoothstep(Ro * 0.92, Ro * 1.02, dist)
            if w > 0 and dist > 0.85 * er:
                V[i] = c + q / dist * (dist + (0.85 * er - dist) * w)
    return V


def caruncle(c, a, g, u, er):
    """The inner corner's fleshy teardrop, lying on the eyeball between the two lid margins: its point
    in the corner, its round end toward the iris."""
    K = EYE["lids"]["caruncle"]
    tc = math.cos(math.radians(EYE["lids"]["inner_canthus_deg"]))
    nt, nv = 10, 8
    verts, faces = [], []
    for i in range(nt + 1):
        sfr = i / nt
        t = -tc * (1 - K["reach"] * sfr)
        psi = math.acos(t)
        pu, pl = lid_margin(t, True), -lid_margin(t, False)
        mid, half = (pu + pl) / 2, (pu - pl) / 2 * math.sqrt(max(0.0, 1 - sfr ** 2)) * 0.85
        for j in range(nv + 1):
            v = j / nv
            phi = mid - half + 2 * half * v
            r = er * (1.01 + K["bulge"] * math.sin(math.pi * v) * math.sqrt(max(0.0, 1 - sfr ** 2)) * min(1.0, 3 * sfr))
            ab, ub = bent_frame(a, g, u, t)
            d = ab * math.cos(psi) + math.sin(psi) * (g * math.cos(phi) + ub * math.sin(phi))
            verts.append(tuple(np.asarray(c) + d * r))
    for i in range(nt):
        for j in range(nv):
            q = i * (nv + 1) + j
            faces.append([q, q + 1, q + nv + 2, q + nv + 1])
    return verts, faces


def band_zs(z_front, z_back, base_n):
    """Stations for the roof: even spacing plus a tight pair at every band step so the steps stay crisp."""
    zs = list(np.linspace(z_front, z_back, base_n))
    zb = ROOF["front_z_band_origin"]
    while zb > z_back:
        for e in (0.0012, -0.0012):
            if z_back < zb + e < z_front:
                zs.append(zb + e)
        zb -= ROOF["band"]
    return sorted(set(round(z, 5) for z in zs), reverse=True)


# ---------------------------------------------------------------- general pieces
def loft(contour_fn, zs, cap_front=True, cap_back=True, front_dent=None):
    """Rings of the contour along z, closed across the open side (palate / mouth floor)
    and capped at both ends. Returns verts, quads, and per-vertex (along, around) coords."""
    verts, faces, uv = [], [], []
    rings = []
    for k, z in enumerate(zs):
        pts, edge_y = contour_fn(z)
        ring = []
        for i, (x, y) in enumerate(pts):
            ring.append(len(verts)); verts.append((x, y, z)); uv.append((z, i / N_AROUND))
        # inner (mouth-side) surface between the two lip edges
        inner = []
        for j in range(1, 6):
            t = j / 6
            x = pts[-1][0] + (pts[0][0] - pts[-1][0]) * t
            inner.append(len(verts)); verts.append((x, edge_y(x) if callable(edge_y) else edge_y, z)); uv.append((z, -1.0))
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
        if k == 0 and front_dent:
            # the front face, filled with rings shrinking toward its middle, each moved forward by front_dent(x, y),
            # so the face can be shaped (it must vanish at the outline)
            cx = sum(verts[i][0] for i in r) / M; cy = sum(verts[i][1] for i in r) / M
            for f in (0.85, 0.7, 0.55, 0.4, 0.25, 0.1):
                nr = []
                for i in r:
                    x, y, _ = verts[i]
                    x, y = cx + (x - cx) * f, cy + (y - cy) * f
                    nr.append(len(verts)); verts.append((x, y, zs[0] + front_dent(x, y))); uv.append((zs[0], 0.5))
                for i in range(M):
                    j = (i + 1) % M
                    faces.append([r[j], r[i], nr[i], nr[j]])
                r = nr
        c = len(verts)
        cx = sum(verts[i][0] for i in r) / M; cy = sum(verts[i][1] for i in r) / M
        verts.append((cx, cy, zs[k] + (front_dent(cx, cy) if (k == 0 and front_dent) else 0.0) + (0.0 if k == 0 else -0.006))); uv.append((zs[k], 0.5))
        for i in range(M):
            j = (i + 1) % M
            faces.append([r[j], r[i], c] if k == 0 else [r[i], r[j], c])
    return verts, faces, uv


def catmull(P, n):
    """Points along a Catmull-Rom spline through P, n per span, with the matching control-point parameter."""
    P = [np.asarray(p, float) for p in P]
    Q = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    pts, par = [], []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for k in range(n):
            t = k / n
            pts.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
            par.append(i - 1 + t)
    pts.append(P[-1]); par.append(len(P) - 1)
    return np.array(pts), np.array(par)


def spline_frames(path, radii, step):
    """Resample a Catmull-Rom spline through `path` at even arc-length steps. Returns centres, radii
    (interpolated per control point), arc length, and a parallel-transported frame (n, b)."""
    C, par = catmull(path, 200)
    s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(C, axis=0), axis=1))])
    su = np.arange(0, s[-1], step); su = np.append(su, s[-1])
    C = np.stack([np.interp(su, s, C[:, k]) for k in range(3)], 1)
    R = np.interp(np.interp(su, s, par), np.arange(len(radii)), radii)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    N, B = [], []
    n = norm(np.cross(T[0], [0, 1.0, 0]))
    for i in range(len(C)):
        if i:
            n = norm(n - T[i] * (n @ T[i]))
        N.append(n); B.append(np.cross(T[i], n))
    return C, R, su, np.array(N), np.array(B)


def ring_faces(nrings, around, closed_ends=None):
    faces = []
    for i in range(nrings - 1):
        for k in range(around):
            a = i * around + k; b2 = i * around + (k + 1) % around
            faces.append([a, b2, b2 + around, a + around])
    return faces


def tube(path, radii, around=16, step=0.002, grooves=None):
    """A smooth horn: a tube along a spline, radius per control point, with fine incised grooves
    (thin lines cut into a smooth surface, not raised bumps). _A runs 0..1 along it; _B is the groove."""
    C, R, s, N, Bv = spline_frames(path, radii, step)
    total = s[-1]
    verts, A, B = [], [], []
    for i in range(len(C)):
        g = 0.0
        if grooves and grooves["start_s"] <= s[i] <= grooves["end_frac"] * total:
            m = (s[i] - grooves["start_s"]) % grooves["every"]
            g = math.exp(-(min(m, grooves["every"] - m) / grooves["width"]) ** 2)
        r = R[i] - (grooves["depth"] * g if grooves else 0.0)
        for k in range(around):
            a = 2 * math.pi * k / around
            verts.append(tuple(C[i] + (N[i] * math.cos(a) + Bv[i] * math.sin(a)) * r))
            A.append(s[i] / total); B.append(g)
    faces = ring_faces(len(C), around)
    for i, end in ((0, False), (len(C) - 1, True)):
        c = len(verts); verts.append(tuple(C[i])); A.append(s[i] / total); B.append(0.0)
        for k in range(around):
            a = i * around + k; b2 = i * around + (k + 1) % around
            faces.append([a, b2, c] if end else [b2, a, c])
    return verts, faces, A, B


def sphere(c, r, lat=12, lon=18, theta_max=math.pi, up=(0, 1, 0)):
    up = norm(up)
    a = np.cross(up, [0, 0, 1.0]) if abs(up[2]) < 0.9 else np.cross(up, [1.0, 0, 0]); a = norm(a); b = np.cross(up, a)
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


def eye_frame(sgn):
    """Gaze g, canthal axis a (front corner -> back corner) and lid 'up' u for one eye."""
    g = norm([sgn * EYE["gaze"][0], EYE["gaze"][1], EYE["gaze"][2]])
    tl = math.radians(EYE["canthal_tilt_deg"])
    a0 = np.array([0.0, math.sin(tl), -math.cos(tl)])
    a = norm(a0 - (a0 @ g) * g)
    u = np.cross(a, g)
    if u[1] < 0:
        u = -u
    return g, a, u


def lid_margin(t, upper):
    """Angle of a lid margin above (+) or below (-) the gaze, at position t = cos(psi) along the canthal
    axis (+1 toward the outer/lateral end, -1 toward the inner/medial end). The corners of the eye (the
    canthi) are not the ends of that axis, which lie buried under the face: they sit on the eyeball where
    it meets the face, outer_canthus_deg / inner_canthus_deg from the gaze. Between them the two lids are
    not mirror images: the upper margin peaks a little toward the inner corner, the lower dips lowest
    toward the outer corner; the outer corner closes to a sharp point, the inner one is rounded round the
    caruncle. Beyond the corners the margins meet and the lids are closed."""
    Ls = EYE["lids"]; L = Ls["upper" if upper else "lower"]
    tc = math.cos(math.radians(Ls["outer_canthus_deg"])) if t > 0 else math.cos(math.radians(Ls["inner_canthus_deg"]))
    tau = min(1.0, abs(t) / tc) * (1 if t > 0 else -1)
    p = L["corner_exp_lateral"] if t > 0 else L["corner_exp_medial"]
    h = math.sin(math.radians(L["open_deg"])) * max(0.0, 1 - tau * tau) ** p * (1 + L["skew"] * tau)
    return math.asin(min(0.98, h / max(1e-4, math.sqrt(max(0.0, 1 - t * t)))))


def rot(v, k, ang):
    """Rotate v about unit axis k by ang (Rodrigues)."""
    return v * math.cos(ang) + np.cross(k, v) * math.sin(ang) + k * (k @ v) * (1 - math.cos(ang))


def bent_frame(a, g, u, t):
    """The eye's frame at position t along the canthal axis, bent so each corner sits at its own measured
    angle: the axis through the centre has the mean tilt, and each half turns its corner further down
    (toward the corner) by corner_bend_deg, growing from mid-eye to the corner."""
    if abs(t) < 1e-9:
        return a, u
    tau = lid_tau(t)
    bend = math.radians(EYE["corner_bend_deg"]["outer" if t > 0 else "inner"]) * smoothstep(0.0, 1.0, abs(tau))
    end = a if t > 0 else -a
    ang = bend if rot(end, g, 0.01)[1] < end[1] else -bend  # turn that corner downward
    return rot(a, g, ang), rot(u, g, ang)


def lid_tau(t):
    """Position between the corners: 0 mid-eye, +-1 at the outer / inner corner (and beyond)."""
    Ls = EYE["lids"]
    tc = math.cos(math.radians(Ls["outer_canthus_deg"] if t > 0 else Ls["inner_canthus_deg"]))
    return max(-1.0, min(1.0, t / tc))


def lid(c, R, a, g, u, upper, thick, psi_lat, psi_med, closed=0.0, nps=40, nph=10):
    """A lid: a thick shell around the eye. psi runs along the canthal axis from the outer corner (0)
    to the inner corner (pi), so the lid pinches toward the corners; phi runs round the axis from the
    margin back into the socket. The outer and inner layers meet in a rounded rim at the margin.
    Returns verts, faces, _A (0 at the margin) and t (position along the axis) per vertex."""
    sgn = 1 if upper else -1
    phi1 = sgn * math.radians(170)
    verts, faces, A, Ts = [], [], [], []
    n = None
    for i in range(nps + 1):
        psi = psi_lat + (math.pi - psi_lat - psi_med) * i / nps
        t = math.cos(psi)
        phi0 = sgn * lid_margin(t, upper)
        if closed:  # blink: the margin slides over the eyeball to where the lids meet, a little below mid-eye
            meet = -EYE["lids"]["blink_meet"] * lid_margin(t, False)
            phi0 = phi0 + (meet - phi0) * closed * EYE["lids"]["blink_share_" + ("upper" if upper else "lower")]
        rim = [(R + thick * 0.5 * (1 - math.cos(math.pi * k / 4)), phi0 - sgn * math.radians(4) * math.sin(math.pi * k / 4)) for k in range(5)]
        layers = [(R + thick, phi0 + (phi1 - phi0) * j / nph) for j in range(nph, 0, -1)] + \
                 [(R + thick - (r - R), ph) for r, ph in rim] + \
                 [(R, phi0 + (phi1 - phi0) * j / nph) for j in range(1, nph + 1)]
        n = len(layers)
        ab, ub = bent_frame(a, g, u, t)
        for j, (rr, phi) in enumerate(layers):
            d = ab * math.cos(psi) + math.sin(psi) * (g * math.cos(phi) + ub * math.sin(phi))
            verts.append(tuple(np.asarray(c) + d * rr)); A.append(abs(j - (n - 1) / 2) / ((n - 1) / 2)); Ts.append(t)
    for i in range(nps):
        for j in range(n - 1):
            p = i * n + j; q = p + n
            faces.append([p, q, q + 1, p + 1])
    return verts, faces, A, Ts


def expression_offsets(V, terms):
    """Offsets of the face's vertices for one muscle action: `push` moves a region (out, up, forward),
    `crease` folds the skin in along a line. Both act on the sides of the face like the anatomy brushes."""
    Dl = np.zeros_like(V)
    for i, (x, y, z) in enumerate(V):
        wb = interp(UPPER, z, 4)
        side = min(1.0, max(0.0, (abs(x) / wb - 0.35) / 0.4))
        if side == 0.0:
            continue
        sx = math.copysign(1.0, x)
        for tm in terms:
            if tm["kind"] == "push":
                (cz, cy), (rz, ry) = tm["centre"], tm["radii"]
                w = math.exp(-((z - cz) / rz) ** 2 - ((y - cy) / ry) ** 2) * side
                mo, mu, mf = tm["move"]
                Dl[i] += (sx * mo * w, mu * w, mf * w)
            else:
                d, _, end = seg_dist(z, y, tm["zy"])
                Dl[i, 0] -= sx * tm["depth"] * math.exp(-(d / tm["width"]) ** 2) * side * smoothstep(-0.01, 0.02, end)
    return Dl


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
    # _A, _B and _ZONE travel packed in one vector attribute (_ABZ): with morph targets on top, WebGL's
    # 16 vertex attributes run out otherwise
    a = me.attributes.new("_PART", "FLOAT", "POINT"); a.data.foreach_set("value", np.asarray(attrs["_PART"], np.float32))
    abz = np.stack([np.asarray(attrs[k], np.float32) for k in ("_A", "_B", "_ZONE")], 1)
    a = me.attributes.new("_ABZ", "FLOAT_VECTOR", "POINT"); a.data.foreach_set("vector", abz.ravel())
    for vi, wl in enumerate(bone_weights):
        for bone, w in wl:
            (ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)).add([vi], w, "ADD")
    return ob


def head_parts():
    """Build every head part as a Blender object. Returns the objects and the head's bones as
    (name, head, tail, parent) with the head bone's parent left as None, for the caller to attach."""
    objs = []
    rigid = lambda n: [[("head", 1.0)]] * n

    # face: the orange mass, dense rings near the nose where the shape changes fastest
    z0, z1 = UPPER[0, 0], UPPER[-1, 0]
    zs = np.concatenate([np.linspace(z0, 1.86, 20), np.linspace(1.85, z1, 120)])
    v, f, uv = loft(upper_contour, zs, front_dent=front_setback)
    hf = []
    for (x, y, z), (_, w) in zip(v, uv):
        low, top = interp(UPPER, z, 2), interp(UPPER, z, 1)
        hf.append((y - low) / max(top - low, 1e-6))
    # the closed underside in front of the jaw is the overhanging upper lip (skin), not the palate
    part = [1.0 if uv[i][1] >= 0 or v[i][2] > JAW[0, 0] - 0.01 else 3.0 for i in range(len(v))]
    under = [1.0 if uv[i][1] < 0 else 0.0 for i in range(len(v))]  # _ZONE: the overhang's underside, smooth skin
    V = carve_socket(np.array(v))
    face = add_part("Face", V.tolist(), f, {"_PART": part, "_A": [u[0] for u in uv], "_B": hf, "_ZONE": under}, rigid(len(v)))
    objs.append(face)
    # expression shapes: one per facial muscle action, exported as morph targets (blend shapes)
    face.shape_key_add(name="Basis", from_mix=False)
    for name, act in D["expressions"]["muscle_actions"].items():
        key = face.shape_key_add(name=name, from_mix=False)
        key.data.foreach_set("co", to_blender(V + expression_offsets(V, act["terms"])).astype(np.float32).ravel())

    # roof: banded shell over the face; its eave stands proud of the orange
    rz = band_zs(z0 + roof_t(z0)[0], ROOF["back_z"], 60)  # its front cap covers the face's flat front, dark in the gaps round the front tile
    rings, at = [], []
    for z in rz:
        outer, inner, fb = roof_ring(z)
        rings.append((outer, inner)); at.append((fb, [fb] * len(outer)))
    v, f, A, B, Z = shell_loft(rings, at)
    objs.append(add_part("Roof", v, f, {"_PART": [10] * len(v), "_A": A, "_B": B, "_ZONE": Z}, rigid(len(v))))
    v, f, A, B, NW = nose_part()
    objs.append(add_part("Nose", v, f, {"_PART": [13] * len(v), "_A": A, "_B": B, "_ZONE": NW}, rigid(len(v))))
    for k, (v, f, A, B, NW) in enumerate(roof_plates()):
        objs.append(add_part(f"RoofPlate{k}", v, f, {"_PART": [13] * len(v), "_A": A, "_B": B, "_ZONE": NW}, rigid(len(v))))

    # lower jaw skin
    zj = np.concatenate([np.linspace(JAW[0, 0], 1.80, 10), np.linspace(1.79, JAW[-1, 0], 24)])
    v, f, uv = loft(jaw_contour, zj)
    part = [2.0 if u[1] >= 0 else 3.0 for u in uv]
    objs.append(add_part("Jaw", v, f, {"_PART": part, "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                         [[("jaw", 1.0)]] * len(v)))

    # teeth: small flat triangular blades, evenly spaced along each lip edge, each pointing perpendicular to the
    # lip line with its tip raked a little back toward the throat (flight render, limited edition)
    TT = D["teeth"]
    for jaw_side, bone in ((False, "head"), (True, "jaw")):
        TS = TT["lower" if jaw_side else "upper"]
        vs, fs, ws = [], [], []
        if jaw_side:
            edge_y = lambda z: interp(JAW, z, 1)
            half_w = lambda z: interp(JAW, z, 3) - TS["inset"]
        else:
            edge_y = lambda z: interp(UPPER, z, 2)
            half_w = lambda z: interp(UPPER, z, 4) - TS["inset"]
        zs = np.linspace(TS["z"][0], TS["z"][1], TS["count"])
        # the front teeth: a row across the front of the mouth at the bite point, where the upper and lower fronts
        # meet (in front of it is the front muzzle's underside: skin, no teeth)
        FT = TT["front_lower" if jaw_side else "front"]
        if FT:
            z0 = FT["z"]
            for x in np.linspace(-FT["half_span"], FT["half_span"], FT["count"]):
                base = np.array([x, edge_y(z0), z0])
                sy = 1.0 if jaw_side else -1.0
                d = norm(np.array([0.0, sy * math.cos(math.radians(TT["rake_deg"])), -math.sin(math.radians(TT["rake_deg"]))]))
                tang = np.array([1.0, 0.0, 0.0]); length = FT["length"]; bl = length * TT["base_frac"]
                b0 = len(vs)
                for p in (tang * bl, np.array([0, 0, TT["thickness"]]), -tang * bl, np.array([0, 0, -TT["thickness"]])):
                    vs.append(tuple(base + p - d * 0.004))
                vs.append(tuple(base + d * length))
                for j in range(4):
                    fs.append([b0 + (j + 1) % 4, b0 + j, b0 + 4] if not jaw_side else [b0 + j, b0 + (j + 1) % 4, b0 + 4])
                ws += [[(bone, 1.0)]] * 5
        for sgn in (1, -1):
            for k, z in enumerate(zs):
                f = k / (len(zs) - 1)
                length = TS["length"][0] + (TS["length"][1] - TS["length"][0]) * math.sin(math.pi * min(1.0, f * 1.3))
                dz = 0.004
                slope = (edge_y(z + dz) - edge_y(z - dz)) / (2 * dz)
                tang = norm(np.array([0.0, slope, 1.0]))          # along the lip, forward
                into = np.array([0.0, 1.0 if jaw_side else -1.0, 0.0])
                into = norm(into - (into @ tang) * tang)            # perpendicular to the lip line, into the mouth gap
                rake = math.radians(TT["rake_deg"])
                d = norm(into * math.cos(rake) - tang * math.sin(rake))  # tip raked back toward the throat
                base = np.array([sgn * half_w(z), edge_y(z), z])
                bl, bt = length * TT["base_frac"], TT["thickness"]
                b0 = len(vs)
                # a flat blade: base a thin diamond along the lip, apex at the tip
                for p in (tang * bl, np.array([sgn * bt, 0, 0]), -tang * bl, np.array([-sgn * bt, 0, 0])):
                    vs.append(tuple(base + p - d * 0.004))
                vs.append(tuple(base + d * length))
                for j in range(4):
                    fs.append([b0 + j, b0 + (j + 1) % 4, b0 + 4] if sgn > 0 else [b0 + (j + 1) % 4, b0 + j, b0 + 4])
                ws += [[(bone, 1.0)]] * 5
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

    lid_bones = []
    for sgn in (1, -1):
        sd = "L" if sgn > 0 else "R"
        ez, ey, er = EYE["centre_zy"][0], EYE["centre_zy"][1], EYE["radius"]
        c, _ = eye_seat(sgn)
        g, a, u = eye_frame(sgn)
        v, f, uv = sphere(c, er, up=g)
        objs.append(add_part("Eye" + sd, v, f, {"_PART": [6] * len(v), "_A": [q[0] for q in uv], "_B": [0] * len(v), "_ZONE": [0] * len(v)}, rigid(len(v))))
        # lids: thick shells hinged on the canthal axis. The upper lid is on two bones (inner and outer half)
        # so its margin can tilt for expression; the lower lid on one. A positive turn about a bone closes its lid.
        hinge = a if np.allclose(np.cross(a, u), g, atol=1e-6) else -a
        R = er * EYE["lid_scale"]; thick = er * EYE["lid_thickness"]
        psi_lat, psi_med = (math.radians(EYE["lids"][k]) for k in ("outer_corner_inset_deg", "inner_corner_inset_deg"))
        for upper in (True, False):
            v, f, A, Ts = lid(c, R, a, g, u, upper, thick, psi_lat, psi_med)
            # the lid moves most mid-eye and not at all at the corners, where it is fixed to the face (the
            # canthal tendons): the rest of each vertex's weight stays on the head
            ws = []
            for t in Ts:
                tau = lid_tau(t)
                m = 1 - smoothstep(0.55, 1.0, abs(tau))
                if upper:
                    wo = smoothstep(-0.6, 0.6, tau)
                    ws.append([(f"lidUpperOut.{sd}", m * wo), (f"lidUpperIn.{sd}", m * (1 - wo)), ("head", 1 - m + 1e-4)])
                else:
                    ws.append([(f"lidLower.{sd}", m), ("head", 1 - m + 1e-4)])
            # _B: how far past the eye's corner (0 inside the opening, 1 beyond): there the lids are closed and their
            # margins meet in a plain seam, not a dark rim, so the eye ends at its corners with no line trailing on
            beyond = [smoothstep(1.0, 1.12, abs(t) / math.cos(math.radians(EYE["lids"]["outer_canthus_deg" if t > 0 else "inner_canthus_deg"]))) for t in Ts]
            ob = add_part(f"Lid{'Upper' if upper else 'Lower'}{sd}", v, f, {"_PART": [7] * len(v), "_A": A, "_B": beyond, "_ZONE": [0] * len(v)}, ws)
            # blink: each lid turns about the canthal axis (its margin travels across the eye at right angles to the
            # line between the corners, and the lids meet along that line). Stored as in-between shapes along that
            # arc (blink1..blinkN, each the lid at k/N closed): a single straight-line blend would cut through the
            # eyeball mid-blink. A bone turn this large would tear the corners, which are fixed to the face.
            ob.shape_key_add(name="Basis", from_mix=False)
            NB = EYE["lids"]["blink_steps"]
            for kb in range(1, NB + 1):
                vb, _, _, _ = lid(c, R, a, g, u, upper, thick, psi_lat, psi_med, closed=kb / NB)
                ob.shape_key_add(name=f"blink{kb}", from_mix=False).data.foreach_set("co", to_blender(np.array(vb)).astype(np.float32).ravel())
            objs.append(ob)
        for bn, axis in (("lidUpperIn", hinge), ("lidUpperOut", hinge), ("lidLower", -hinge)):
            lid_bones.append((f"{bn}.{sd}", c, c + axis * 0.04))
        # caruncle: the fleshy teardrop in the inner corner
        v, f = caruncle(c, a, g, u, er)
        objs.append(add_part("Caruncle" + sd, v, f, {"_PART": [12] * len(v), "_A": [0] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, rigid(len(v))))
        # horn: a smooth tube with incised ring lines, starting buried in the roof; the roof plates are
        # sculpted up into its root (horn_fillet), so it grows out of the head rather than sitting on it
        path = [[sgn * p[0], p[1], p[2]] for p in HORN["path"]]
        v, f, A, B = tube(path, HORN["radius"], around=24, step=0.001, grooves=HORN["grooves"])
        objs.append(add_part("Horn" + sd, v, f, {"_PART": [8] * len(v), "_A": A, "_B": B, "_ZONE": [0] * len(v)}, rigid(len(v))))
        # ear frill: an almond leaf lying close along the side of the head under the horn, pointing back and
        # up; cupped (pale hollow inside) with an orange rolled rim along its top edge, like a horse's ear laid back
        base = np.array([sgn * FRILL["base"][0], FRILL["base"][1], FRILL["base"][2]])
        tipp = np.array([sgn * FRILL["tip"][0], FRILL["tip"][1], FRILL["tip"][2]])
        L = tipp - base; length = np.linalg.norm(L); L /= length
        nrm = norm([sgn * 1.0, FRILL["face_up"], FRILL["face_forward"]]); nrm = norm(nrm - L * (nrm @ L))
        W = np.cross(nrm, L); W = W if W[1] > 0 else -W  # across the leaf, toward its top edge
        G, H = 16, 12
        vs, fs, us, bs = [], [], [], []
        for layer, off in ((0, 0.0), (1, -FRILL["thickness"])):
            b0 = len(vs)
            for i in range(G + 1):          # base -> tip
                for j in range(H + 1):      # bottom edge -> top edge
                    a = i / G; c = -1 + 2 * j / H
                    half = FRILL["width"] / 2 * math.sin(math.pi * (0.12 + 0.88 * a)) ** 0.75 * (1 - 0.35 * a)
                    p = base + L * a * length + W * c * half
                    cup = -FRILL["cup"] * (1 - c * c) * math.sin(math.pi * min(1.0, a * 1.05))  # hollow facing out
                    roll = FRILL["rolled_front_edge"] * smoothstep(0.55, 1.0, c) ** 2 * math.sin(math.pi * min(1.0, a * 1.1))
                    p = p + nrm * (cup + roll + off) - W * roll * 0.6  # the top edge curls out and over
                    vs.append(tuple(p)); us.append(a); bs.append((c + 1) / 2)
            for i in range(G):
                for j in range(H):
                    q = b0 + i * (H + 1) + j
                    fs.append([q, q + H + 1, q + H + 2, q + 1] if layer == 0 else [q, q + 1, q + H + 2, q + H + 1])
        objs.append(add_part("Frill" + ("L" if sgn > 0 else "R"), vs, fs, {"_PART": [9] * len(vs), "_A": us, "_B": bs, "_ZONE": [0] * len(vs)},
                             rigid(len(vs))))

    bones = [("head", (0, 1.57, 1.36), (0, 1.44, 2.017), None),
             ("jaw", HINGE, (0, 1.24, 1.86), "head"),
             ("tongue1", (0, 1.42, 1.56), (0, 1.38, 1.66), "jaw"),
             ("tongue2", (0, 1.38, 1.66), (0, 1.34, 1.75), "tongue1"),
             ("tongue3", (0, 1.34, 1.75), (0, 1.31, 1.84), "tongue2")]
    bones += [(bn, h0, h1, "head") for bn, h0, h1 in lid_bones]
    return objs, bones


def assemble(objs, bones, out, name="ClayRig"):
    """Make the armature from (name, head, tail, parent) specs, join the parts into one skinned mesh
    on it, and export a .glb."""
    arm_data = bpy.data.armatures.new(name); arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, h0, h1, parent in bones:
        b = arm_data.edit_bones.new(bn); b.head = to_blender(h0).tolist(); b.tail = to_blender(h1).tolist()
        if parent:
            b.parent = arm_data.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    mesh = objs[0]
    mod = mesh.modifiers.new("Armature", "ARMATURE"); mod.object = arm
    mesh.parent = arm
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True); arm.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_skins=True, export_attributes=True,
                              export_yup=True, export_animations=False, export_materials="NONE")
    print(f"exported {out}: {len(mesh.data.vertices)} verts, {len(mesh.data.polygons)} faces")


def main():
    """The head on its own, on a stub neck bone."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs, bones = head_parts()
    bones = [("neck3", (0, 1.30, 1.10), (0, 1.57, 1.36), None)] + [(n, h, t, p or "neck3") for n, h, t, p in bones]
    assemble(objs, bones, OUT, "HeadRig")


if __name__ == "__main__":
    main()
