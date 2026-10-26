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


def horn_path():
    """The horn's centreline: a simple S. It rises steeply out of the back of the head, flattens as it
    sweeps back (a downward arc), then curls up toward the tip (an upward arc): its heading eases
    between three angles above straight back (s_curve.heading_deg), over its length, splaying outward
    from x root to x tip. Returns points and the radius at each."""
    S = HORN["s_curve"]
    a0, a1, a2 = S["heading_deg"]
    n = 24
    p = np.array(S["root_zy"], float); pts = [p.copy()]
    for i in range(n):
        t = (i + 0.5) / n
        s1 = smoothstep(0.0, 0.5, t); s2 = smoothstep(0.55, 1.0, t)
        th = math.radians(a0 + (a1 - a0) * s1 + (a2 - a1) * s2)
        p = p + np.array([-math.cos(th), math.sin(th)]) * S["length"] / n
        pts.append(p.copy())
    xs = np.linspace(S["x"][0], S["x"][1], n + 1)
    R = np.interp(np.linspace(0, 1, n + 1), np.linspace(0, 1, len(HORN["radius"])), HORN["radius"])
    return [[x, y, z] for x, (z, y) in zip(xs, pts)], list(R)
FRILL = D["ear_frill"]
N_AROUND = 192  # points around the face contour (fine enough to carry the lid creases, and for the trimmed edge at the cheek line to follow it closely)


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


def muzzle_taper(z):
    """Width factor for the front muzzle in top view (upper_head.muzzle_taper): one long convex curve from the eye to
    the tip, narrowing slowly at first and faster toward the front (the premaxilla's rounded U), then a small radius
    rounding the front corners. Convex all the way, so the roof and its plates, built on the face, round with it."""
    MT = D["upper_head"]["muzzle_taper"]
    z0 = UPPER[0, 0]
    t = min(1.0, max(0.0, (z - MT["from_z"]) / (z0 - MT["from_z"])))
    f = 1 - (1 - MT["tip_width"]) * t ** MT["power"]
    tc = (z - (z0 - MT["corner_radius"])) / MT["corner_radius"]
    if tc > 0:
        f *= MT["corner_min"] + (1 - MT["corner_min"]) * math.sqrt(max(0.0, 1 - min(tc, 1.0) ** 2))
    return f


def face_pt(z, th):
    """Point on the face at station z, angle th (0 = left lip edge, pi/2 = top, pi = right lip edge).
    Boxy cross-section (flat top, steep sides, cheeks wider than the top), then the brushes."""
    top, low, wt, wb = (interp(UPPER, z, c) for c in (1, 2, 3, 4))
    b = top - low
    c, s = math.cos(th), math.sin(th)
    yy = b * abs(s) ** (2 / SQ)
    a = (wb + (wt - wb) * (yy / b) ** 1.6) * muzzle_taper(z)
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
        hp, hr = horn_path()
        path = [[sgn * p[0], p[1], p[2]] for p in hp]
        C, R, _, _, _ = spline_frames(path, hr, 0.004)
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
            # open_front: no edge at the front (it carries on down the front face); and near the front its lower ends
            # keep their full thickness, so the front piece's rounded bottom edge wraps round the corner into them
            low = Lv - acc[j] + (0.03 * (1 - smoothstep(0.0, 0.5, u)) if open_front else 0.0)
            dist = min(1.0 if open_front else u * Ls, (1 - u) * Ls, acc[j], low)
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
    """The roof's front: the front band carried on down over the snout's front face as one smooth piece, lying
    on the slightly convex front at the plate's thickness, down to a level bottom edge at the overhang's lowest
    height (eave_y) right across to the front corners, where it rolls in to the orange muzzle in a rounded edge,
    as the roof's edge does all round. Where the band's front edge is already down at that height (its lower
    ends, at the corners) the rows stay on it."""
    ye = D["upper_head"]["front"]["ridge"]["eave_y"]
    step = D["upper_head"]["front"]["ridge"]["edge_step"]
    z0 = UPPER[0, 0]
    K = 10
    rows = []
    for k in range(1, K + 1):
        f = k / K
        row = []
        for x0, y0, zp in front_row:
            reach = smoothstep(0.0, 0.02, y0 - ye)  # eases out toward the corners, where the edge is already low
            y = y0 + (ye - y0) * f if y0 > ye else y0
            xo = abs(face_pt(z0, side_th(z0, min(max(y, interp(UPPER, z0, 2) + 1e-4), face_pt(z0, math.pi / 2)[1] - 1e-4)))[0]) + under + T
            x = x0 + (math.copysign(min(abs(x0), xo), x0) - x0) * reach
            zt = z0 + front_setback(x, y) + under + T
            row.append((x, y, zp + (zt - zp) * smoothstep(0.0, 0.3, f)))  # all of it comes onto the front face, closing the corners
        rows.append(row)
    rows.append([(x, y - 0.002, z - step) for x, y, z in rows[-1]])  # the bottom edge rolls in to the face
    return rows


def front_shell(V, F):
    """The roof's front, raised from the face itself, like the body's shell: the front of the snout down to
    the roof's lower edge, and the front band's strip of the top and sides back to its joint, lifted by
    the plate's thickness over the underlay, with a rounded edge along the joint and along the bottom
    (the lower edge runs level at the front, so it meets the orange muzzle in one smooth line right round
    the corners). Being one surface, it has no seams or corners to fold. Returns verts, faces, _A (distance
    to its edge) and tint."""
    L = PLATES["layout"]["rows"][0]
    s1 = L["joint_every"] - PLATES["gap"] / 2
    a = np.array(sv_point(s1, 0.0)); b = np.array(sv_point(s1, eave_depth(s1)))
    tdir = norm(b - a); nfw = np.array([-tdir[1], tdir[0]])
    if nfw[0] < 0:
        nfw = -nfw  # pointing forward
    V = np.asarray(V, float); F = np.asarray(F)
    # only the face's triangles near the front, split three times (each into four) so the piece's edges are smooth
    near = (V[:, 2] > a[0] - 0.05).astype(bool)
    F = F[near[F].any(axis=1)]
    for _ in range(3):
        mid, newV, newF = {}, list(V), []
        def m(i, j):
            k = (min(i, j), max(i, j))
            if k not in mid:
                mid[k] = len(newV); newV.append((V[i] + V[j]) / 2)
            return mid[k]
        for i, j, k in F:
            ij, jk, ki = m(i, j), m(j, k), m(k, i)
            newF += [[i, ij, ki], [ij, j, jk], [ki, jk, k], [ij, jk, ki]]
        V, F = np.array(newV), np.array(newF)
    zy = V[:, [2, 1]]
    dj = (zy - a) @ nfw  # in front of the band's back joint
    eave = np.interp(-V[:, 2], -PLATE_EDGE[:, 0], PLATE_EDGE[:, 1])
    de = V[:, 1] - eave - 0.004  # above the roof's lower edge, clear of where the face curls under the lip
    d = np.minimum(dj, de)
    inside = d > 0
    keep = inside[F].any(axis=1)
    used = np.unique(F[keep]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    # snap each outside vertex onto the edge line (d = 0) along its edges to inside neighbours, so the edge is smooth, not a sawtooth
    Ek = np.vstack([F[keep][:, [0, 1]], F[keep][:, [1, 2]], F[keep][:, [2, 0]]]); Ek = np.vstack([Ek, Ek[:, ::-1]])
    Ek = Ek[~inside[Ek[:, 0]] & inside[Ek[:, 1]]]
    o, i = Ek[:, 0], Ek[:, 1]
    t = (-d[o] / (d[i] - d[o]))[:, None]
    P = V[o] + (V[i] - V[o]) * t
    acc = np.zeros_like(V); cnt = np.zeros(len(V))
    np.add.at(acc, o, P); np.add.at(cnt, o, 1)
    V = V.copy(); V[cnt > 0] = acc[cnt > 0] / cnt[cnt > 0][:, None]; d = np.where(cnt > 0, 0.0, d)
    N = np.zeros_like(V)  # smooth outward normals
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); E = np.vstack([E, E[:, ::-1]])
    for _ in range(3):
        acc = np.zeros_like(N)
        for k in range(3):
            acc[:, k] = np.bincount(E[:, 0], weights=N[E[:, 1], k], minlength=len(V))
        N = 0.5 * N + 0.5 * acc / np.maximum(np.linalg.norm(acc, axis=1), 1e-12)[:, None] * np.linalg.norm(N, axis=1)[:, None]
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    if np.mean(N[used] @ np.array([0.0, 1.0, 0.0])) < 0:
        N = -N
    du = np.clip(d[used], 0.0, None)
    # it rounds down onto the underlay (not the face), so the underlay's edge never shows through it
    h = roof_t(UPPER[0, 0])[0] + 0.0005 + PLATES["thickness"] * np.sqrt(np.clip(du / PLATES["layout"].get("front_edge_round", 0.008), 0.0, 1.0))
    S = V[used] + N[used] * h[:, None]
    tint = (math.sin(10 * 12.9898) * 43758.5453) % 1.0
    return S.tolist(), remap[F[keep]].tolist(), list(du), [tint] * len(used)


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
                pass  # the front band and the snout's front are one piece raised from the face (front_shell)
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


def opening_frame(c, er):
    """The eye's opening in side view: one teardrop outline, the round eye with its inner corner drawn down
    and forward into a point, filled by the pink caruncle (side sheet). Returns the tip (z, y), the axis
    e_p from the tip through the eyeball's centre, e_q across it toward the upper lid, the axis length,
    and h(p): the opening's half-width at p along the axis (the circle, or the wedge from the tip)."""
    O = EYE["opening"]
    ang = math.radians(O["tip_angle_deg"])
    c2 = np.array([c[2], c[1]])
    d, r0 = O["tip_reach"] * er, O["radius"] * er
    tip = c2 + np.array([math.cos(ang), -math.sin(ang)]) * d  # +z forward, -y down
    ep = norm(c2 - tip)
    eq = np.array([-ep[1], ep[0]])
    if eq[1] < 0:
        eq = -eq
    ta = math.tan(math.radians(O["tip_half_angle_deg"]))
    h = lambda p: max(math.sqrt(max(0.0, r0 * r0 - (p - d) ** 2)), p * ta if 0 <= p <= d else 0.0)
    return tip, ep, eq, d + r0, h


def eye_skin(c, er, sgn):
    """|x| of what lies under the lids at (z, y): the outermost of the carved face and the eyeball. The face
    is sampled once on a grid round the eye and interpolated."""
    from scipy.interpolate import RegularGridInterpolator
    Z = np.linspace(c[2] - 2.2 * er, c[2] + 2.2 * er, 33)
    Y = np.linspace(c[1] - 2.2 * er, c[1] + 2.2 * er, 33)
    P = np.array([[sgn * abs(face_pt(z, side_th(z, y))[0]), y, z] for z in Z for y in Y])
    X = np.abs(carve_socket(P)[:, 0]).reshape(len(Z), len(Y))
    face = RegularGridInterpolator((Z, Y), X, bounds_error=False, fill_value=None)
    return lambda z, y: max(float(face((z, y))), abs(c[0]) + math.sqrt(max(0.0, er * er - (z - c[2]) ** 2 - (y - c[1]) ** 2)))


def press_under_lids(V):
    """Press the face's skin in under the lids' footprint (the teardrop opening and the lid band round it),
    fading out at the band's edge, so the face never shows through the lids: they are fitted to a sampled
    copy of the skin, which smooths over the crisp forms round the eye."""
    O = EYE["opening"]; er = EYE["radius"]
    V = V.copy()
    for sgn in (1, -1):
        c, _ = eye_seat(sgn)
        tip, ep, eq, L, h = opening_frame(c, er)
        ps = np.linspace(0.0, L, 200)
        ring = np.array([tip + ep * p + eq * h(p) for p in ps] + [tip + ep * p - eq * h(p) for p in ps[::-1]])
        band = O["band"] * er
        for i, (x, y, z) in enumerate(V):
            if x * sgn <= 0 or abs(z - c[2]) > L + band or abs(y - c[1]) > L + band:
                continue
            q = np.array([z, y]) - tip
            p, w = q @ ep, q @ eq
            inside = 0 <= p <= L and abs(w) <= h(p)
            dist = 0.0 if inside else float(np.min(np.linalg.norm(ring - np.array([z, y]), axis=1)))
            k = 1 - smoothstep(0.8 * band, 1.05 * band, dist)
            if k > 0:
                V[i, 0] -= sgn * O["press"] * er * k
    return V


def eye_lid(c, er, sgn, skin, upper, closed=0.0, nps=36, nf=14, nr=5):
    """A lid as a sheet over the opening, seen from the side: from its margin on the outline out past the
    dark ring, where it sinks into the skin. The two lids meet at the tip and at the back of the round, so
    the dark ring runs unbroken round the whole teardrop. Blink: the upper margin slides across the
    opening to the lower one, covering the eyeball and the caruncle. Returns verts, faces, _A (0 at the
    margin, the dark ring, 1 past it) and tau (-1 at the tip, +1 at the back) per vertex."""
    O = EYE["opening"]
    tip, ep, eq, L, h = opening_frame(c, er)
    s = 1 if upper else -1
    thick, clear = er * EYE["lid_thickness"], er * O["clear"] + (0.0003 if upper else 0.0)
    out = lambda p: tip + ep * p + eq * s * h(p)
    verts, A, T = [], [], []
    for i in range(nps + 1):
        p = L * (1 - math.cos(math.pi * i / nps)) / 2
        # the band runs straight out from the eye's centre: the teardrop is star-shaped about it, so the rows
        # never cross (an outline normal folds the band at the inside corners where the point meets the
        # round), and at the tip and the back both lids run out along the axis and meet
        n = norm(out(p) - (tip + ep * (L - O["radius"] * er)))
        m = out(p) if not upper else tip + ep * p + eq * (h(p) * (1 - 2 * closed) - closed * 0.03 * er)
        edge = out(p) + n * O["band"] * er
        # rows: the dark ring is its own rows at the margin, a fixed width (narrowing as the lid closes, so
        # the closed eye is a line, not a dark band); the rest of the lid stretches out to its buried edge
        span = np.linalg.norm(edge - m); dirn = (edge - m) / max(span, 1e-9)
        ring = min(O["ring_upper" if upper else "ring_lower"] * er * (1 - 0.6 * closed), 0.6 * span)
        for j in range(nf + 1):
            dm = ring * (j / nr) ** 1.3 if j <= nr else ring + (span - ring) * ((j - nr) / (nf - nr)) ** 1.3
            f = dm / max(span, 1e-9)
            z, y = m + dirn * dm
            sink = smoothstep(0.75, 1.0, f)
            lift = (clear + thick * math.sin(math.pi / 2 * min(1.0, dm / (0.08 * er)))) * (1 - sink) - 0.0005 * sink
            verts.append((sgn * (skin(z, y) + lift), y, z))
            A.append(0.2 * j / nr if j <= nr else 1.0)
            T.append(2 * p / L - 1)
    faces = []
    for i in range(nps):
        for j in range(nf):
            q = i * (nf + 1) + j
            fc = [q, q + 1, q + nf + 2, q + nf + 1]
            faces.append(fc if (sgn > 0) != upper else fc[::-1])
    return verts, faces, A, T


def caruncle(c, er, sgn, skin):
    """The pink caruncle: a low fleshy pad filling the teardrop's point, from the tip to where the point
    opens into the round of the eye, tucked a little under the lid margins."""
    O = EYE["opening"]
    tip, ep, eq, L, h = opening_frame(c, er)
    ta = math.tan(math.radians(O["tip_half_angle_deg"]))
    d, r0 = O["tip_reach"] * er, O["radius"] * er
    pj = min(np.linspace(0.0, d, 400), key=lambda p: abs(p * ta - math.sqrt(max(0.0, r0 * r0 - (p - d) ** 2))) if p > d - r0 else 1.0)
    nt, nv = 14, 8
    verts = []
    for i in range(nt + 1):
        p = pj * i / nt
        hw = 1.1 * p * ta * math.sqrt(max(0.0, 1 - (p / pj) ** 4))
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            z, y = tip + ep * p + eq * hw * v
            verts.append((sgn * (skin(z, y) + O["caruncle_bump"] * er * math.sqrt(max(0.0, 1 - v * v))), y, z))
    faces = []
    for i in range(nt):
        for j in range(nv):
            q = i * (nv + 1) + j
            fc = [q, q + 1, q + nv + 2, q + nv + 1]
            faces.append(fc if sgn < 0 else fc[::-1])
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
def loft(contour_fn, zs, cap_front=True, cap_back=True, front_dent=None, inner_dip=None, n_inner=6):
    """Rings of the contour along z, closed across the open side (palate / mouth floor)
    and capped at both ends. Returns verts, quads, and per-vertex (along, around) coords. inner_dip(z), if given,
    bows the closing surface: up into an arched palate (positive) or down into a trough for the tongue (negative)."""
    verts, faces, uv = [], [], []
    rings = []
    for k, z in enumerate(zs):
        pts, edge_y = contour_fn(z)
        ring = []
        for i, (x, y) in enumerate(pts):
            ring.append(len(verts)); verts.append((x, y, z)); uv.append((z, i / N_AROUND))
        # inner (mouth-side) surface between the two lip edges
        inner = []
        for j in range(1, n_inner):
            t = j / n_inner
            x = pts[-1][0] + (pts[0][0] - pts[-1][0]) * t
            y = (edge_y(x) if callable(edge_y) else edge_y) + (inner_dip(z) * math.sin(math.pi * t) if inner_dip else 0.0)
            inner.append(len(verts)); verts.append((x, y, z)); uv.append((z, -1.0))
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


def rot(v, k, ang):
    """Rotate v about unit axis k by ang (Rodrigues)."""
    return v * math.cos(ang) + np.cross(k, v) * math.sin(ang) + k * (k @ v) * (1 - math.cos(ang))


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


def snout_z(z):
    """The side sheet's head is turned a few degrees toward the viewer, so the front of its snout shows
    the muzzle's front face and front corner; measured as if it were a true side view, that added
    length and a forward slant to the snout (the user's reading). The snout is compressed toward the
    eye from snout_turn.from_z by snout_turn.scale, which takes the turn back out."""
    T = D["snout_turn"]
    return np.where(z > T["from_z"], T["from_z"] + (z - T["from_z"]) * T["scale"], z)


def warp_snout(objs, bones):
    """Apply snout_z to every head part (its vertices and every shape key) and to the bones."""
    for ob in objs:
        keys = ob.data.shape_keys.key_blocks if ob.data.shape_keys else []
        for data in [ob.data.vertices] + [k.data for k in keys]:
            co = np.zeros(len(data) * 3, np.float32); data.foreach_get("co", co); co = co.reshape(-1, 3)
            co[:, 1] = -snout_z(-co[:, 1])  # Blender's y is -z
            data.foreach_set("co", co.ravel())
    w = lambda p: (p[0], p[1], float(snout_z(np.array(p[2]))))
    return [(n, w(h0), w(h1), par) for n, h0, h1, par in bones]


def head_parts():
    """Build every head part as a Blender object. Returns the objects and the head's bones as
    (name, head, tail, parent) with the head bone's parent left as None, for the caller to attach."""
    objs = []
    rigid = lambda n: [[("head", 1.0)]] * n

    # face: the orange mass, dense rings near the nose where the shape changes fastest
    z0, z1 = UPPER[0, 0], UPPER[-1, 0]
    zs = np.concatenate([np.linspace(z0, 1.86, 20), np.linspace(1.85, z1, 120)])
    MO = D["mouth"]
    # 1 inside the mouth (behind inside_from), 0 in front of it, where the closing surface is the overhanging lip's underside
    inside = lambda z: smoothstep(MO["inside_from"][0], MO["inside_from"][1], z) * smoothstep(MO["hinge_z"], MO["hinge_z"] + 0.06, z)
    # the closing surface finely sampled across: in front of the mouth it is the lip's visible underside
    v, f, uv = loft(upper_contour, zs, front_dent=front_setback, inner_dip=lambda z: MO["palate_arch"] * inside(z), n_inner=24)
    hf = []
    for (x, y, z), (_, w) in zip(v, uv):
        low, top = interp(UPPER, z, 2), interp(UPPER, z, 1)
        hf.append((y - low) / max(top - low, 1e-6))
    # the closed underside in front of the jaw is the overhanging upper lip (skin), not the palate
    part = [1.0 if uv[i][1] >= 0 or v[i][2] > JAW[0, 0] - 0.01 else 3.0 for i in range(len(v))]
    under = [1.0 if uv[i][1] < 0 else 0.0 for i in range(len(v))]  # _ZONE: the overhang's underside, smooth skin
    V = press_under_lids(carve_socket(np.array(v)))
    face = add_part("Face", V.tolist(), f, {"_PART": part, "_A": [u[0] for u in uv], "_B": hf, "_ZONE": under}, rigid(len(v)))
    objs.append(face)
    tris = np.array([[p[0], p[k], p[k + 1]] for p in f for k in range(1, len(p) - 1)])  # quads and fans as triangles
    sv, sf, sa, sb = front_shell(V, tris)
    objs.append(add_part("RoofFront", sv, sf, {"_PART": [13] * len(sv), "_A": sa, "_B": sb, "_ZONE": [0] * len(sv)}, rigid(len(sv))))
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
    v, f, uv = loft(jaw_contour, zj, inner_dip=lambda z: -MO["floor_trough"] * inside(z))
    part = [2.0 if u[1] >= 0 else 3.0 for u in uv]
    objs.append(add_part("Jaw", v, f, {"_PART": part, "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                         [[("jaw", 1.0)]] * len(v)))

    # cheek skin at each corner of the mouth: a web from the upper lip's edge to the lower jaw's edge, from near the
    # hinge forward to the mouth corner, its front edge bowed forward into a rounded corner. Its upper edge rides the
    # head and its lower edge the jaw, so it lies folded inside the cheek when the mouth is shut and stretches into the
    # back of the gape as the jaw drops, instead of the gape opening as a slot all the way back to the hinge. Two
    # layers: cheek skin outside (orange above, cream below like the jaw), the mouth's lining inside
    NU, NV = 22, 12
    for sgn in (1, -1):
        vs, fs, ws, ps, As, Bs, bulge = [], [], [], [], [], [], []
        for layer in (0, 1):
            b0 = len(vs)
            for i in range(NU + 1):
                for j in range(NV + 1):
                    u, w = i / NU, j / NV
                    z = MO["web_back_z"] + (MO["corner_z"] + MO["corner_round"] * math.sin(math.pi * w) - MO["web_back_z"]) * u
                    up = upper_contour(z)[0]; lo = jaw_contour(z)[0]
                    U = np.array([*(up[0] if sgn > 0 else up[-1]), z]); Lp = np.array([*(lo[0] if sgn > 0 else lo[-1]), z])
                    P = U + (Lp - U) * w
                    P[0] -= sgn * (0.0 if layer == 0 else MO["web_thickness"])  # the lining a little inside the skin
                    vs.append(tuple(P)); ws.append([("head", 1 - w), ("jaw", w)])
                    # outside: orange along the upper lip, cream jowl below it (the cover); inside: the mouth's lining
                    ps.append((1.0 if w < MO["web_orange_to"] else 2.0) if layer == 0 else 3.0); As.append(u); Bs.append(w)
                    # the jaw's opening fills the cheek out: a corrective shape (jawOpen, driven by the jaw's angle) bowing
                    # the stretched skin outward, most in the middle of the span and toward the corner
                    bulge.append((sgn * MO["cheek_bulge"] * math.sin(math.pi * w) ** 2 * smoothstep(0.0, 0.5, u), 0.0, 0.0))  # leaving both edges tangentially
            for i in range(NU):
                for j in range(NV):
                    q = [b0 + i * (NV + 1) + j, b0 + (i + 1) * (NV + 1) + j, b0 + (i + 1) * (NV + 1) + j + 1, b0 + i * (NV + 1) + j + 1]
                    fs.append(q if (sgn > 0) == (layer == 0) else q[::-1])
        web = add_part("CheekWeb" + ("L" if sgn > 0 else "R"), vs, fs, {"_PART": ps, "_A": As, "_B": Bs, "_ZONE": [0] * len(vs)}, ws)
        web.shape_key_add(name="Basis", from_mix=False)
        web.shape_key_add(name="jawOpen", from_mix=False).data.foreach_set(
            "co", to_blender(np.array(vs) + np.array(bulge)).astype(np.float32).ravel())
        objs.append(web)

    # teeth: small flat triangular blades, evenly spaced along each lip edge, each pointing perpendicular to the
    # lip line with its tip raked a little back toward the throat (flight render, limited edition). The lower
    # teeth rise plainly from the lower jaw; the upper ones grow from the roof of the mouth, inward and up
    # behind the upper lip, which hides most of them (tuck_up, inset)
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
            z0 = FT["z"] - FT.get("tuck_back", 0.0)
            for x in np.linspace(-FT["half_span"], FT["half_span"], FT["count"]):
                base = np.array([x, edge_y(z0) + FT.get("tuck_up", 0.0), z0])
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
                base = np.array([sgn * half_w(z), edge_y(z) + TS.get("tuck_up", 0.0), z])  # upper: up behind the lip
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
        # lids: two sheets over the teardrop opening (eye_lid). The upper lid is on two bones (inner and outer
        # half) so its margin can tilt for expression; the lower lid on one. A positive turn about a bone closes its lid.
        hinge = a if np.allclose(np.cross(a, u), g, atol=1e-6) else -a
        skin = eye_skin(c, er, sgn)
        NB = EYE["opening"]["blink_steps"]
        for upper in (True, False):
            rest = EYE["opening"]["upper_rest_closed"] if upper else 0.0  # the upper lid rests across the top of the iris
            v, f, A, Ts = eye_lid(c, er, sgn, skin, upper, closed=rest)
            # the lid moves most mid-eye and not at all at the tip and the back, where it is fixed to the face:
            # the rest of each vertex's weight stays on the head
            ws = []
            for tau in Ts:
                m = 1 - smoothstep(0.55, 1.0, abs(tau))
                if upper:
                    wo = smoothstep(-0.6, 0.6, tau)
                    ws.append([(f"lidUpperOut.{sd}", m * wo), (f"lidUpperIn.{sd}", m * (1 - wo)), ("head", 1 - m + 1e-4)])
                else:
                    ws.append([(f"lidLower.{sd}", m), ("head", 1 - m + 1e-4)])
            ob = add_part(f"Lid{'Upper' if upper else 'Lower'}{sd}", v, f, {"_PART": [7] * len(v), "_A": A, "_B": [0] * len(v), "_ZONE": [0] * len(v)}, ws)
            # blink: the upper margin slides across the opening to the lower one, stored as in-between shapes
            # (blink1..blinkN, each the lid at k/N closed) so it stays on the eyeball's surface on the way
            ob.shape_key_add(name="Basis", from_mix=False)
            for kb in range(1, NB + 1):
                vb = eye_lid(c, er, sgn, skin, upper, closed=rest + (1 - rest) * kb / NB if upper else 0.0)[0]
                ob.shape_key_add(name=f"blink{kb}", from_mix=False).data.foreach_set("co", to_blender(np.array(vb)).astype(np.float32).ravel())
            objs.append(ob)
        for bn, axis in (("lidUpperIn", hinge), ("lidUpperOut", hinge), ("lidLower", -hinge)):
            lid_bones.append((f"{bn}.{sd}", c, c + axis * 0.04))
        v, f = caruncle(c, er, sgn, skin)
        objs.append(add_part("Caruncle" + sd, v, f, {"_PART": [12] * len(v), "_A": [1] * len(v), "_B": [0] * len(v), "_ZONE": [0] * len(v)}, rigid(len(v))))
        # horn: a smooth tube with incised ring lines, starting buried in the roof; the roof plates are
        # sculpted up into its root (horn_fillet), so it grows out of the head rather than sitting on it
        hp, hr = horn_path()
        path = [[sgn * p[0], p[1], p[2]] for p in hp]
        v, f, A, B = tube(path, hr, around=24, step=0.001, grooves=HORN["grooves"])
        objs.append(add_part("Horn" + sd, v, f, {"_PART": [8] * len(v), "_A": A, "_B": B, "_ZONE": [0] * len(v)}, rigid(len(v))))
        # ear: laid back along the side of the head under the horn, pointing back and up, like a horse's ear laid
        # flat, and grown out of the face itself. Its section is one closed loop: the hollow (pale, an arc curling up
        # at the lower edge and over at the upper front edge into a rolled rim), then back round its solid back. The
        # loft starts from a footprint lying on the face's own surface at the top-back corner of the cheek, where the
        # S line behind the cheek begins, and rises out of it tangentially (a fillet) into that section, so the face's
        # skin runs on into the ear with no seam (the root keeps the face's pebbled orange: _A < 0)
        face_x = lambda y, z: abs(face_pt(z, side_th(z, y))[0])
        b_yz = np.array(FRILL["base"][1:])
        base = np.array([sgn * (face_x(*b_yz) + FRILL["stand_off"]), *b_yz])
        tipp = np.array([sgn * FRILL["tip"][0], FRILL["tip"][1], FRILL["tip"][2]])
        L = tipp - base; length = np.linalg.norm(L); L /= length
        nrm = norm([sgn * 1.0, FRILL["face_up"], FRILL["face_forward"]]); nrm = norm(nrm - L * (nrm @ L))
        W = np.cross(nrm, L); W = W if W[1] > 0 else -W  # across the ear, toward its upper front edge
        G, H, NF = 26, 20, 8
        lo, up = (math.radians(a) for a in FRILL["roll_deg"])
        dk, th = FRILL["depth"], FRILL["thickness"]

        def ear_pt(a, c, out):
            half = FRILL["width"] / 2 * math.sin(math.pi * (0.12 + 0.88 * a)) ** 0.75 * (1 - 0.35 * a)
            t = c * (up if c > 0 else lo)  # angle round the arc from the bottom of the hollow
            o = base + L * a * length + nrm * half * dk
            p = o + W * half * math.sin(t) - nrm * half * dk * math.cos(t)
            if out:  # the back: a solid body behind the hollow, thick toward the root, thin at the tip
                q = p - o; q = q / (np.linalg.norm(q) + 1e-9)
                p = p + norm(0.4 * q - nrm) * (th * (1 - 0.6 * a) + FRILL["body"] * (1 - a) ** 1.5)
            return p

        M = 2 * (H + 1)
        loop = [(0, j) for j in range(H + 1)] + [(1, j) for j in range(H, -1, -1)]  # hollow lower->upper, back upper->lower
        a1 = FRILL["fillet_a"]
        sec1 = [ear_pt(a1, -1 + 2 * j / H, layer) for layer, j in loop]
        # the footprint: an oval on the face round the root, the hollow's side forward-out, the back's side behind
        Ls = norm(np.array([0.0, L[1], L[2]])); Ws = norm(np.array([0.0, W[1], W[2]]))
        foot = []
        for k in range(M):
            ph = math.pi * (k / (M - 1)) * 2 - math.pi / 2
            yz = b_yz + (Ws[1:] * FRILL["foot"][1] * math.sin(ph) + Ls[1:] * FRILL["foot"][0] * (1 + math.cos(ph)) * 0.5)
            foot.append(np.array([sgn * (face_x(*yz) - 0.002), *yz]))
        vs, fs, us, bs, zs = [], [], [], [], []
        for i in range(G + 1):
            for k, (layer, j) in enumerate(loop):
                if i <= NF:  # the fillet: from the footprint on the face, rising tangentially into the section
                    e = (i / NF) ** 2
                    P = foot[k] + (sec1[k] - foot[k]) * e
                    us.append(-1.0 + i / NF)
                else:
                    P = ear_pt(a1 + (1 - a1) * (i - NF) / (G - NF), -1 + 2 * j / H, layer)
                    us.append(a1 + (1 - a1) * (i - NF) / (G - NF))
                vs.append(tuple(P)); bs.append(j / H); zs.append(float(layer))
        for i in range(G):
            for k in range(M):
                q = [i * M + k, (i + 1) * M + k, (i + 1) * M + (k + 1) % M, i * M + (k + 1) % M]
                fs.append(q if sgn > 0 else q[::-1])
        objs.append(add_part("Frill" + ("L" if sgn > 0 else "R"), vs, fs, {"_PART": [9] * len(vs), "_A": us, "_B": bs, "_ZONE": zs},
                             rigid(len(vs))))

    bones = [("head", (0, 1.57, 1.36), (0, 1.44, 2.017), None),
             ("jaw", HINGE, (0, 1.24, 1.86), "head"),
             ("tongue1", (0, 1.42, 1.56), (0, 1.38, 1.66), "jaw"),
             ("tongue2", (0, 1.38, 1.66), (0, 1.34, 1.75), "tongue1"),
             ("tongue3", (0, 1.34, 1.75), (0, 1.31, 1.84), "tongue2")]
    bones += [(bn, h0, h1, "head") for bn, h0, h1 in lid_bones]
    bones = warp_snout(objs, bones)
    return objs, bones


def pose_clips(arm, bones, clips):
    """Key each clip on the armature: rest at frame 0, the pose at frame 1 (see assemble)."""
    from mathutils import Matrix
    C = np.array([[1.0, 0, 0], [0, 0, -1.0], [0, 1.0, 0]])  # the model's frame to Blender's
    order = [b[0] for b in bones]
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    arm.animation_data_create()
    for clip, pose in clips.items():
        arm.animation_data.action = bpy.data.actions.new(clip)
        names = [n for n in order if n in pose]
        for n in names:
            pb = arm.pose.bones[n]; pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
            pb.keyframe_insert("rotation_quaternion", frame=0)
        bpy.context.view_layer.update()
        for n in names:  # parents first, so each bone's head follows its parent's pose
            Rm, head = pose[n]
            pb = arm.pose.bones[n]; rest = np.array(arm.data.bones[n].matrix_local)
            M = np.eye(4); M[:3, :3] = (C @ Rm @ C.T) @ rest[:3, :3]
            M[:3, 3] = to_blender(np.array(head)) if head is not None else np.array(pb.matrix)[:3, 3]
            pb.matrix = Matrix(M.tolist())
            bpy.context.view_layer.update()
            pb.keyframe_insert("rotation_quaternion", frame=1)
        for n in names:
            arm.pose.bones[n].rotation_quaternion = (1, 0, 0, 0); arm.pose.bones[n].location = (0, 0, 0)
    bpy.context.scene.frame_set(0)
    bpy.ops.object.mode_set(mode="OBJECT")


def assemble(objs, bones, out, name="ClayRig", clips=None):
    """Make the armature from (name, head, tail, parent) specs, join the parts into one skinned mesh
    on it, and export a .glb. clips: {clip name: {bone: (turn, head)}}, each exported as an animation from
    rest (time 0) to that pose (its end): per bone its turn from rest (a 3x3 in the model's frame) and its
    head in the pose (None: wherever its parent carries it)."""
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
    if clips:
        pose_clips(arm, bones, clips)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True); arm.select_set(True)
    bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_skins=True, export_attributes=True,
                              export_yup=True, export_animations=bool(clips), export_force_sampling=False, export_materials="NONE")
    print(f"exported {out}: {len(mesh.data.vertices)} verts, {len(mesh.data.polygons)} faces")


def main():
    """The head on its own, on a stub neck bone."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    objs, bones = head_parts()
    bones = [("neck3", (0, 1.30, 1.10), (0, 1.57, 1.36), None)] + [(n, h, t, p or "neck3") for n, h, t, p in bones]
    assemble(objs, bones, OUT, "HeadRig")


if __name__ == "__main__":
    main()
