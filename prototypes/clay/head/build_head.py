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
HINGE = tuple(D["lower_jaw"]["hinge"])
EYE = D["eye"]
PLATE_EDGE = np.array(D["dark_plate_edge"]["zy"])
ROOF = D["roof"]
PLATES = D["roof_plates"]
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


def jaw_from_bones(LJ):
    """The lower jaw's profile table (z, top, bottom, half-width), generated from its named bones
    (lower_jaw.bones) rather than traced:
    - the alveolar margin (the tooth row's top edge) runs just inside the upper lip's edge, bite_gap below it,
      from the chin back to the mouth corner; behind the corner the coronoid line carries the jaw's top edge up
      inside the cheek to the hinge;
    - the underside is one smooth curve through the symphysis (the chin's front), the chin's lowest point and the
      throat junction, rising on behind it inside the throat to the ear;
    - the half-width runs smoothly through the width of each landmark;
    - the chin rounds off over its last round_len, in side view and from above (a U)."""
    from scipy.interpolate import PchipInterpolator
    B = LJ["bones"]
    sy, ch, tn, cor = B["symphysis"], B["chin"], B["throat_junction"], B["coronoid_line"]
    ra = B["retroarticular"]
    zt = sy["z"]
    bot_pts = [(zt, sy["bottom"]), (ch["z"], ch["bottom"]), (tn["z"], tn["bottom"])] + [tuple(p) for p in ra["bottom"]]
    bz, by = zip(*sorted(bot_pts))
    bottom = PchipInterpolator(bz, by)
    wz, ww = zip(*sorted([(zt, sy["half_width"])] + [tuple(p) for p in B["half_width"]]))
    width = PchipInterpolator(wz, ww)
    cz, cy = zip(*sorted(tuple(p) for p in cor["zy"]))
    z_corner = max(cz)
    rows = []
    zs = sorted(set(np.round(np.concatenate([np.arange(zt, min(cz) - 1e-9, -0.01), [zt - 0.003, zt - 0.008, zt - 0.015], cz]), 4)), reverse=True)
    for z in zs:
        if z >= z_corner + B["alveolar"]["blend"]:
            top = interp(UPPER, z, 2) - B["alveolar"]["bite_gap"]
        elif z <= z_corner:
            top = float(np.interp(z, cz, cy))
        else:  # from the coronoid line's front point into the alveolar margin
            f = smoothstep(z_corner, z_corner + B["alveolar"]["blend"], z)
            top = float(np.interp(z, cz, cy)) * (1 - f) + (interp(UPPER, z, 2) - B["alveolar"]["bite_gap"]) * f
        b, w = float(bottom(z)), float(width(z))
        u = (z - (zt - sy["round_len"])) / sy["round_len"]
        if u > 0:  # the chin's round, in side view and from above
            r = math.sqrt(max(0.0, 1 - min(u, 1.0) ** 2))
            w *= max(r, sy["tip_frac"])
            b += (top - b) * 0.5 * (1 - r)
        rows.append([float(z), top, b, w])
    return np.array(rows)


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


JAW = jaw_from_bones(D["lower_jaw"]) if "bones" in D["lower_jaw"] else np.array(D["lower_jaw"]["rows"])


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
    from above, the middle forward of the sides) and gently convex in profile. Both
    vanish at the face's outline, where it joins the sides."""
    F = D["upper_head"]["front"]
    z0 = UPPER[0, 0]
    lo, top = interp(UPPER, z0, 2), interp(UPPER, z0, 1)
    q = min(1.0, max(0.0, (y - lo) / (top - lo)))
    xo = abs(face_pt(z0, side_th(z0, min(max(y, lo + 1e-4), top - 1e-4)))[0]) or 1e-6
    # zero all round the outline, its peak included; broad across (across_power), so the front stays full out to its
    # corners and rounds into them, rather than a dome peaked in the middle with a ledge where it runs out
    across = max(0.0, 1 - abs(x / xo) ** F.get("across_power", 2)) * (1 - smoothstep(0.8, 1.0, q))
    # convex forward both ways: rounded across from above, and bulging in side profile between the nose and the lip
    base = F["convex"] + F.get("convex_side", 0.0) * math.sin(math.pi * q) - F["concave"] * math.sin(math.pi * q ** 0.8)
    WP = F.get("whisker_pads")
    if WP:  # a lion's muzzle under the nose: two fleshy pads either side of the philtrum's groove, over the front teeth
        (px, py), (rx, ry) = WP["centre_xy"], WP["radii"]
        band = math.exp(-((y - py) / ry) ** 2)
        base += WP["amount"] * math.exp(-((abs(x) - px) / rx) ** 2) * band - WP["philtrum_depth"] * math.exp(-(x / WP["philtrum_width"]) ** 2) * band
    return across * base


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
        if MT.get("corner_shape") == "chamfer":  # a straight cut across the corner, its ends softened
            f *= 1 - (1 - MT["corner_min"]) * smoothstep(0.0, 0.25, tc) * min(tc, 1.0)
        else:
            f *= MT["corner_min"] + (1 - MT["corner_min"]) * math.sqrt(max(0.0, 1 - min(tc, 1.0) ** 2))
    return f


def lip_tuck(z):
    """Width factor (<= 1) at the upper lip's edge, station z (upper_head.lip_tuck): the cheek is flesh draped over
    the upper teeth and the lower jaw, so along the mouth the lip edge comes in to just outside the lower jaw
    instead of standing out as a puffed shelf; faded out at the mouth corner and at the front muzzle."""
    LT = D["upper_head"]["lip_tuck"]
    w = smoothstep(*LT["from_z"], z) * (1 - smoothstep(*LT["to_z"], z))
    target = interp(JAW, z, 3) + LT["overhang"]
    return 1 - w * max(0.0, 1 - target / interp(UPPER, z, 4))


def lip_roll(dd):
    """Outward swell of a lip's fleshy margin at height dd above (upper lip) or below (lower lip) its edge
    (mouth.lip_roll): a rounded rim of lip along the mouth, as on a reptile's labial scales, so the lip has a
    soft edge that can move, not a cut edge."""
    LR = D["mouth"]["lip_roll"]
    return LR["amount"] * math.exp(-((dd - LR["at"]) / LR["width"]) ** 2)


def face_pt(z, th):
    """Point on the face at station z, angle th (0 = left lip edge, pi/2 = top, pi = right lip edge).
    Boxy cross-section (flat top, steep sides, cheeks wider than the top), then the brushes."""
    top, low, wt, wb = (interp(UPPER, z, c) for c in (1, 2, 3, 4))
    b = top - low
    c, s = math.cos(th), math.sin(th)
    yy = b * abs(s) ** (2 / SQ)
    a = (wb + (wt - wb) * (yy / b) ** 1.6) * muzzle_taper(z)
    x = a * math.copysign(abs(c) ** (2 / SQ), c)
    x *= 1 - (1 - lip_tuck(z)) * (1 - yy / b) ** D["upper_head"]["lip_tuck"]["power"]  # the cheek drapes in to the lip
    x += math.copysign(lip_roll(yy), x)  # the lip's fleshy margin
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
        y = top - b * abs(s) ** (2 / n)
        pts.append((x + math.copysign(lip_roll(top - y), x), y))
    return pts, top


# ---------------------------------------------------------------- roof thickness (the profile the shield and nose are laid out on)
def roof_t(z):
    """Shell thickness: overlapping bands, each thickest at its back edge."""
    f = ((ROOF["front_z_band_origin"] - z) / ROOF["band"]) % 1.0
    return ROOF["thickness"][0] + (ROOF["thickness"][1] - ROOF["thickness"][0]) * f, f


def tooth(vs, fs, base, d, tang, length, ra, rs, sink=0.004, recurve=0.18, NA=10, NL=8):
    """One tooth, a reptile's: a cone rooted in the gum (its base sunk `sink` into it), its section an oval
    flattened side to side (ra along the jaw, rs across), tapering to a sharp tip that curves back toward the
    throat (recurve, a fraction of its length). d points from the root to the tip; tang along the jaw, forward.
    Appends to vs/fs; returns the vertex count added."""
    side = norm(np.cross(d, tang))
    b0 = len(vs)
    for i in range(NL + 1):
        t = i / NL
        c = base - d * sink + d * (length + sink) * t - tang * recurve * length * t * t
        r = (1 - t) ** 0.85
        for j in range(NA):
            a = 2 * math.pi * j / NA
            vs.append(tuple(c + tang * ra * r * math.cos(a) + side * rs * r * math.sin(a)))
    for i in range(NL):
        for j in range(NA):
            k = (j + 1) % NA
            q = [b0 + i * NA + j, b0 + i * NA + k, b0 + (i + 1) * NA + k, b0 + (i + 1) * NA + j]
            fs.append(q)  # outward: (tang, side, d) is right-handed
    tip = len(vs); vs.append(tuple(base + d * length - tang * recurve * length))
    top = b0 + NL * NA  # the last ring is a point already; close it with a fan to the tip
    for j in range(NA):
        f = [top + j, top + (j + 1) % NA, tip]
        fs.append(f)
    return len(vs) - b0


# ---------------------------------------------------------------- muzzle shield and lion's nose
def smax(a, b, k):
    """Smooth maximum (radius k)."""
    return 0.5 * (a + b + math.sqrt((a - b) ** 2 + k * k))


def shield_eave_y(z):
    """The shield's lower edge at station z: the traced dark-plate edge, lifted where the ear passes so the
    shield stays clear of the ear's whole path by design (muzzle_shield.ear_clearance: the ear's top edge
    measured from its mesh, plus a margin)."""
    EC = D["muzzle_shield"]["ear_clearance"]
    base = float(np.interp(-z, -PLATE_EDGE[:, 0], PLATE_EDGE[:, 1]))
    et = np.array(sorted(EC["ear_top"]))
    if not (et[0, 0] <= z <= et[-1, 0]):
        return base
    return smax(base, float(np.interp(z, et[:, 0], et[:, 1])) + EC["margin"], 0.004)


def shield_eave_th(z):
    top, low = interp(UPPER, z, 1), interp(UPPER, z, 2)
    ye = shield_eave_y(z)
    if ye <= low + 1e-4:
        return 0.0
    q = min(1.0, (ye - low) / (top - low))
    return min(math.asin(q ** (SQ / 2)), math.pi / 2 - 0.03)


def profile_sd(Q):
    """Side-view points Q (n x 2, as (z, y)) to profile coordinates (s along the top profile from the front
    edge, d depth below it)."""
    pr = profile(); P, S, N = pr["P"], pr["s"], pr["N"]
    T = np.stack([-N[:, 1], N[:, 0]], 1)
    T *= np.sign(np.sum(T * np.gradient(P, axis=0), 1))[:, None]
    s_out, d_out = np.zeros(len(Q)), np.zeros(len(Q))
    for a in range(0, len(Q), 4000):
        q = Q[a:a + 4000]
        R = q[:, None, :] - P[None, :, :]
        t = np.einsum("mpk,pk->mp", R, T)
        i = np.argmin(np.abs(t) + 1e3 * (np.einsum("mpk,pk->mp", R, N) < -0.01), axis=1)
        s_out[a:a + 4000] = S[i] + t[np.arange(len(q)), i]
        d_out[a:a + 4000] = np.einsum("mk,mk->m", R[np.arange(len(q)), i], N[i])
    return s_out, d_out


def muzzle_shield(V, F):
    """The muzzle shield: one solid piece raised from the face itself, over the region above its edge line
    (shield_eave_y: back along the sides and across the front face at the same height), so the top, the angular
    front corners and the upper front are one continuous surface with no seams or fitted front cap. Lifted by its
    thickness along the face's smoothed normals, rounding down onto the face at its edge (edge_round), with its
    plating carved in like an ankylosaur's fused skull armour: grooves at the band joints, down the ridge and along
    the rim row (roof_plates.layout), and a low dome in each tile. Returns verts, faces, _A (distance to the
    nearest groove or edge, where the shader darkens), _B (tile tint)."""
    SH = D["muzzle_shield"]; L = PLATES["layout"]["rows"]
    je, d_row, jr = L[0]["joint_every"], L[0]["d"][1], L[1]["joint_every"]
    T, under, G = SH["thickness"], SH["under"], SH["groove"]
    V = np.asarray(V, float)
    F = np.array([[p[0], p[k], p[k + 1]] for p in F for k in range(1, len(p) - 1)])  # quads and fans as triangles
    def dist(P):  # how far inside the shield's region: above its edge line, in front of its back end
        ye = np.array([shield_eave_y(z) for z in P[:, 2]])
        return np.minimum(P[:, 1] - ye - SH["edge_gap"], P[:, 2] - ROOF["back_z"])
    near = dist(V) > -0.03
    F = F[near[F].any(axis=1)]
    for _ in range(SH["subdivide"]):  # split each triangle into four, so the grooves and the edge are smooth
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
    d = dist(V)
    inside = d > 0
    keep = inside[F].any(axis=1)
    F = F[keep]
    # snap each outside vertex onto the edge line along its edges to inside neighbours, so the edge is smooth
    Ek = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); Ek = np.vstack([Ek, Ek[:, ::-1]])
    Ek = Ek[~inside[Ek[:, 0]] & inside[Ek[:, 1]]]
    o, i = Ek[:, 0], Ek[:, 1]
    t = (-d[o] / (d[i] - d[o]))[:, None]
    acc = np.zeros_like(V); cnt = np.zeros(len(V))
    np.add.at(acc, o, V[o] + (V[i] - V[o]) * t); np.add.at(cnt, o, 1)
    V = V.copy(); V[cnt > 0] = acc[cnt > 0] / cnt[cnt > 0][:, None]; d = np.where(cnt > 0, 0.0, d)
    used = np.unique(F); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    # smooth outward normals
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]); E = np.vstack([E, E[:, ::-1]])
    for _ in range(4):
        accn = np.zeros_like(N)
        for k in range(3):
            accn[:, k] = np.bincount(E[:, 0], weights=N[E[:, 1], k], minlength=len(V))
        N = 0.5 * N + 0.5 * accn / np.maximum(np.linalg.norm(accn, axis=1), 1e-12)[:, None] * np.linalg.norm(N, axis=1)[:, None]
    N /= np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]
    if np.mean(N[used] @ np.array([0.0, 1.0, 0.0])) < 0:
        N = -N
    Vu, Nu, du = V[used], N[used], np.clip(d[used], 0.0, None)
    # the plating, in profile coordinates (s along the top profile from the front edge, depth d below it)
    sv, dv = profile_sd(Vu[:, [2, 1]])
    eds = {}
    tint = lambda k: (math.sin(k * 12.9898) * 43758.5453) % 1.0
    out, A, B = [], [], []
    for k in range(len(Vu)):
        x = Vu[k, 0]; sk, dk = sv[k], dv[k]
        zk = Vu[k, 2]
        key = round(sk, 2)
        if key not in eds:  # the eave's depth at this s: where the edge line meets the profile's normal
            zz, yy = sv_point(max(sk, 0.0), 0.0)
            ye = shield_eave_y(zz)
            eds[key] = max(0.0, yy - ye)
        ed = eds[key]
        rim = ed - d_row >= PLATES["layout"].get("min_rim", 0.025) and sk > 0
        if sk <= je or (not rim) or dk < d_row:  # the top bands (the front band runs on down the front unbroken)
            gd = ([abs(sk - je * max(1, round(sk / je)))] if sk > je * 0.5 else [1.0]) + ([abs(x)] if sk > je else [])
            fs, fd = (max(sk, 0.0) / je) % 1.0, min(1.0, max(dk, 0.0) / (d_row if rim else max(ed, 1e-6)))
            tk = int(max(sk, 0.0) // je) * 2 + (x > 0)
        else:  # the rim row: square marginal scutes
            gd = [abs(sk - jr * round(sk / jr))]
            fs, fd = (sk / jr) % 1.0, (dk - d_row) / max(ed - d_row, 1e-6)
            tk = 100 + int(sk // jr) * 2 + (x > 0)
        if rim and sk > je:
            gd.append(abs(dk - d_row))
        gmin = min(gd)
        dome = SH["dome"] * math.sin(math.pi * fs) ** 0.6 * math.sin(math.pi * min(max(fd, 0.0), 1.0)) ** 0.6 if sk > 0 else 0.0
        g = 1 - smoothstep(0.0, G["width"], gmin)
        edge = math.sqrt(min(1.0, du[k] / SH["edge_round"]))
        h = under * 0.5 + (T + dome - G["depth"] * g) * edge
        q = horn_fillet(Vu[k] + Nu[k] * h, Nu[k], edge)
        out.append(tuple(q)); A.append(min(gmin, du[k])); B.append(tint(tk))
    return out, remap[F].tolist(), A, B


def lion_nose(shield=None, diagnostics=None):
    """A short bridge and raised leather cap built on the finished shield.

    The foot follows the shield mesh, height follows its final unit normal,
    and the cap angle is measured in that frame. The cap closes one trimmed
    loft; no overshooting rings are flattened into extra sheets. _ZONE is
    the carved nostril mask. Returned coordinates are already snout-warped.
    """
    from scipy.interpolate import PchipInterpolator
    NS = D["lion_nose"]; SH = D["muzzle_shield"]
    st = np.array(NS["stations"])  # s, half-width, height above the shield
    wf = PchipInterpolator(st[:, 0], st[:, 1]); hf = PchipInterpolator(st[:, 0], st[:, 2])
    s_front, s_root = NS["s_front"], st[-1, 0]
    bev = NS["cap_bevel"]
    pr = profile()
    nsup, sink, NA = NS["squareness"], NS["sink"], 72
    rings = []
    # ahead of the top profile (s < 0) the nose runs on along the shield's front shelf (front_run, the shield top's
    # centre line in side view), out to the hammer's front edge where the shield turns down
    run = np.array(NS["front_run"]); run_s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(run, axis=0), axis=1))])
    def centre(sv_):
        if sv_ >= 0:
            return sv_point(sv_, 0.0)
        return sv_point(0.0, 0.0) + np.array([np.interp(-sv_, run_s, run[:, k]) for k in (0, 1)]) - run[0]
    # Bind to the actual shield first, then build in its final orthonormal
    # frame. An affine snout warp would shear the raised cap flat again.
    bvh = None
    if shield is not None:
        from mathutils.bvhtree import BVHTree
        bvh = BVHTree.FromPolygons(shield[0], shield[1], all_triangles=True)
    def carrier(sv_, x=0.0):
        zc, yc = centre(sv_)
        n = np.array([np.interp(sv_, pr["s"], pr["N"][:, k]) for k in (0, 1)]); n = n / np.linalg.norm(n)
        out = -n
        base = np.array([0.0, yc, zc]) + np.array([0.0, out[1], out[0]]) * (SH["under"] + SH["thickness"] - roof_t(zc)[0])
        base[0] = x
        if bvh is not None:
            direction = np.array([0.0, out[1], out[0]])
            hit, _, _, _ = bvh.ray_cast(tuple(base + direction * 0.15), tuple(-direction), 0.3)
            if hit is None:
                raise ValueError("nose attachment misses the shield")
            base = np.array(hit)
        base[2] = snout_z(premaxilla_z(np.array(base[2]), np.array(base[1])))
        return base
    def frame(sv_):
        # An attachment follows the anatomical shield plane, not each tiny
        # plate groove. Fit a tangent over a short neighborhood to avoid
        # abrupt cap-angle changes when its position crosses a groove.
        offsets = np.linspace(-NS["frame_span"], NS["frame_span"], 9)
        points = np.array([carrier(sv_ + offset) for offset in offsets])
        forward = -(offsets @ points) / (offsets @ offsets)
        forward[0] = 0; forward /= np.linalg.norm(forward)
        up = np.array([0.0, forward[2], -forward[1]])
        return forward, up
    for sv_ in np.linspace(s_root, s_front - 0.03, 150):
        _, up3 = frame(sv_)
        w, h = float(wf(sv_)), float(hf(sv_))
        ring = []
        for i in range(NA + 1):  # the top and the upright sides: a box with crisp, small-radius corners
            th = math.pi * i / NA
            c, sn = math.cos(th), math.sin(th)
            x = w * math.copysign(abs(c) ** (2 / nsup), c); v = -sink + (h + sink) * abs(sn) ** (2 / nsup)
            x *= np.interp(max(0.0, v / max(h, 1e-6)), *np.array(NS["side_taper"]).T)
            x += math.copysign(NS["fillet"] * (1 - abs(sn) ** (2 / nsup)) ** 2, x)  # its foot flares a little into the shield
            ring.append(carrier(sv_, x) + up3 * v)
        ring += [carrier(sv_, -w + 2 * w * i / 8) - up3 * sink for i in range(1, 8)]
        rings.append(ring)
    V = np.array([p for r in rings for p in r])
    M = len(rings[0])
    # Cap tilt is relative to the final shield, independent of the muzzle's
    # deformation. A small dome and rounded boundary keep it organic.
    forward, up = frame(s_front)
    a_ = math.radians(NS["face_angle_to_shield"])
    nf = math.sin(a_) * forward + math.cos(a_) * up
    cap_up = norm(up - nf * (up @ nf))
    p0 = carrier(s_front) + up * (0.5 * float(hf(s_front)))
    R = float(wf(s_front))
    def face_d(P):
        rel = P - p0; d = rel @ nf
        ip = rel - np.outer(d, nf)
        r2 = (ip[:, 0] / R) ** 2 + (ip @ cap_up / (0.7 * R)) ** 2
        return d - NS["face_dome"] * np.clip(1 - r2, 0.0, 1.0)
    # End each meridian at the leather face. Projecting all the overshooting
    # rings onto it folds repeated sheets into the visible square flap.
    raw = V.reshape(len(rings), M, 3)
    distances = face_d(V).reshape(len(rings), M)
    clipped = np.empty_like(raw)
    for j in range(M):
        crossing = np.flatnonzero(distances[:, j] >= 0)
        end = int(crossing[0]) if len(crossing) else len(rings) - 1
        if end == 0:
            raise ValueError("nose root lies ahead of its leather face")
        t = (-distances[end - 1, j] / (distances[end, j] - distances[end - 1, j])) if len(crossing) else 1.0
        samples = np.linspace(0, end - 1 + t, len(rings))
        for axis in range(3):
            clipped[:, j, axis] = np.interp(samples, np.arange(len(rings)), raw[:, j, axis])
        # The buried underside can stop short of the face plane. Carry just
        # that last meridian smoothly to the boundary; never stack rings there.
        end_distance = face_d(clipped[-1, j][None])[0]
        blend = np.array([smoothstep(0.7, 1.0, u) for u in np.linspace(0, 1, len(rings))])
        clipped[:, j] -= np.outer(blend * end_distance, nf)
    V = clipped.reshape(-1, 3)
    e = face_d(V)
    hh = np.clip(0.5 + 0.5 * e / bev, 0.0, 1.0)
    V += np.outer(e * (1 - hh) - bev * hh * (1 - hh) - e, nf)  # polynomial smooth min of the distance and 0
    # One rounded leather disk closes the trimmed boundary. Its radial rings
    # supply real face area for the dome and nostrils, without overlapping lofts.
    boundary = V[-M:].copy()
    cap_centre = boundary.mean(0)
    cap_rings = []
    for radial in np.linspace(0.875, 0.125, 7):
        ring = cap_centre + radial * (boundary - cap_centre)
        ring -= np.outer(face_d(ring), nf) * smoothstep(0.0, 0.25, 1 - radial)
        cap_rings.append(ring)
    cap_start = len(V)
    V = np.vstack([V] + cap_rings)
    cap_centre -= face_d(cap_centre[None])[0] * nf
    cap_centre_index = len(V)
    V = np.vstack([V, cap_centre])
    e = face_d(V)
    NW = np.zeros(len(V))
    on_face = e > -bev * 0.6
    cap_points = V[(len(rings) - 1) * M:]
    yf = cap_points @ cap_up; y0, y1 = yf.min(), yf.max()
    heights = np.linspace(y0, y1, 25)
    half_widths = np.array([max(abs(cap_points[abs(yf - y) < (y1 - y0) / 12, 0]), default=R * 0.05) for y in heights])
    N_ = NS["nostril"]; C = np.array(N_["path"])  # (fraction of the cap's half-width out, fraction up the face)
    for i in np.where(e > -2.5 * bev)[0]:  # on the face and round its side-front edge
        height = V[i] @ cap_up
        local_width = max(R * 0.1, float(np.interp(height, heights, half_widths)))
        q = np.array([abs(V[i, 0]) / local_width, (height - y0) / max(y1 - y0, 1e-6)])
        sc = np.array([local_width, y1 - y0])
        best, tb = 1e9, 0.0
        for k in range(len(C) - 1):
            a0, b0 = C[k], C[k + 1]; ab = (b0 - a0) * sc; qq = (q - a0) * sc
            t = min(1.0, max(0.0, qq @ ab / (ab @ ab)))
            dd = np.linalg.norm(qq - ab * t)
            if dd < best:
                best, tb = dd, (k + t) / (len(C) - 1)
        wN = N_["half_width"][0] + (N_["half_width"][1] - N_["half_width"][0]) * tb
        g = smoothstep(0.0, 1.0, max(0.0, 1 - best / wN))
        if g > 0:  # cut back into the nose, along the face's normal and in from its side
            cut = nf * N_["cut_forward"] + np.array([math.copysign(N_["cut_side"], V[i, 0]), 0.0, 0.0]); cut /= np.linalg.norm(cut)
            V[i] -= cut * N_["depth"] * g
            NW[i] = smoothstep(0.3, 0.75, g)
    faces = []
    for k in range(len(rings) - 1):
        for i in range(M):
            j = (i + 1) % M
            faces.append([k * M + i, (k + 1) * M + i, (k + 1) * M + j, k * M + j])
    cap_rows = [(len(rings) - 1) * M] + [cap_start + k * M for k in range(len(cap_rings))]
    for row, following in zip(cap_rows, cap_rows[1:]):
        for i in range(M):
            j = (i + 1) % M
            faces.append([row + i, following + i, following + j, row + j])
    for i in range(M):
        faces.append([cap_rows[-1] + i, cap_centre_index, cap_rows[-1] + (i + 1) % M])
    for k in (0,):
        c = len(V); V = np.vstack([V, V[k * M:(k + 1) * M].mean(0)]); NW = np.append(NW, 0.0)
        for i in range(M):
            f = [k * M + i, k * M + (i + 1) % M, c]
            faces.append(f)
    tint = (math.sin(0 * 12.9898) * 43758.5453) % 1.0
    if diagnostics is not None and shield is not None:
        sh = np.array(shield[0]); chosen = (abs(sh[:, 0]) < 0.02) & (sh[:, 1] > UPPER[0, 1] - 0.008) & (sh[:, 2] > UPPER[0, 0] - 0.015)
        edge = sh[chosen].copy(); edge[:, 2] = snout_z(premaxilla_z(edge[:, 2], edge[:, 1]))
        diagnostics.update(clearance=float(max(edge @ forward) - max(V @ forward)), width=float(2 * R), forward=forward.tolist())
    return [tuple(p) for p in V], faces, [0.02] * len(V), [tint] * len(V), list(NW)

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
    bp = O.get("back_point", 0.0)
    def h(p):
        circ = math.sqrt(max(0.0, r0 * r0 - (p - d) ** 2))
        if p > d:  # the outer corner: from the round toward a soft point (an almond's end), by back_point
            circ = (1 - bp) * circ + bp * r0 * math.cos(math.pi / 2 * min(1.0, (p - d) / r0))
        return max(circ, p * ta if 0 <= p <= d else 0.0)
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


def premaxilla_z(z, y):
    """A crown over an alveolar base, not a skin-only bulge.

    The front shield extends over the lip, turning the front muzzle down in
    the shield's own frame. Fade the extension into the maxilla behind it;
    the lip, tooth bed and lower jaw remain on their shared closure line.
    All parts, expressions and bone anchors pass through this same field.
    """
    P = D.get("premaxilla", {})
    if not P:
        return z
    t = np.clip((z - P["from_z"]) / (P["full_z"] - P["from_z"]), 0.0, 1.0)
    w = t * t * (3 - 2 * t)
    lip = np.interp(z, UPPER[::-1, 0], UPPER[::-1, 2])
    crown = np.interp(z, UPPER[::-1, 0], UPPER[::-1, 1])
    height = np.clip((y - lip) / np.maximum(crown - lip, 1e-6), 0.0, 1.0)
    return z + P["crown_extension"] * w * height


def warp_snout(objs, bones):
    """Apply snout_z to every head part (its vertices and every shape key) and to the bones."""
    for ob in objs:
        if ob.name == "Nose":  # already built against the final shield frame
            continue
        keys = ob.data.shape_keys.key_blocks if ob.data.shape_keys else []
        for data in [ob.data.vertices] + [k.data for k in keys]:
            co = np.zeros(len(data) * 3, np.float32); data.foreach_get("co", co); co = co.reshape(-1, 3)
            co[:, 1] = -snout_z(premaxilla_z(-co[:, 1], co[:, 2]))  # Blender's y is -z
            data.foreach_set("co", co.ravel())
    w = lambda p: (p[0], p[1], float(snout_z(premaxilla_z(np.array(p[2]), np.array(p[1])))))
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
    # expression shapes: one per facial muscle action, exported as morph targets (blend shapes)
    face.shape_key_add(name="Basis", from_mix=False)
    for name, act in D["expressions"]["muscle_actions"].items():
        if act.get("mesh") == "jaw":
            continue
        key = face.shape_key_add(name=name, from_mix=False)
        key.data.foreach_set("co", to_blender(V + expression_offsets(V, act["terms"])).astype(np.float32).ravel())

    # the muzzle shield: one solid piece with its plating carved in, and the lion's nose rising out of it
    v, f, A, B = muzzle_shield(V, f)
    objs.append(add_part("Shield", v, f, {"_PART": [13] * len(v), "_A": A, "_B": B, "_ZONE": [0] * len(v)}, rigid(len(v))))
    v, f, A, B, NW = lion_nose((v, f))
    objs.append(add_part("Nose", v, f, {"_PART": [13] * len(v), "_A": A, "_B": B, "_ZONE": NW}, rigid(len(v))))

    # lower jaw skin
    zj = JAW[:, 0]  # the generated stations: dense, with the landmarks (the throat notch stays crisp)
    v, f, uv = loft(jaw_contour, zj, inner_dip=lambda z: -MO["floor_trough"] * inside(z))
    part = [2.0 if u[1] >= 0 else 3.0 for u in uv]
    jaw = add_part("Jaw", v, f, {"_PART": part, "_A": [u[0] for u in uv], "_B": [u[1] for u in uv], "_ZONE": [0] * len(v)},
                   [[("jaw", 1.0)]] * len(v))
    objs.append(jaw)
    # the lower lip's muscle actions (mesh "jaw"), on the jaw's skin; the face's are on the face
    jaw_acts = {k: a for k, a in D["expressions"]["muscle_actions"].items() if a.get("mesh") == "jaw"}
    if jaw_acts:
        Vj = np.array(v)
        jaw.shape_key_add(name="Basis", from_mix=False)
        for name, act in jaw_acts.items():
            jaw.shape_key_add(name=name, from_mix=False).data.foreach_set(
                "co", to_blender(Vj + expression_offsets(Vj, act["terms"])).astype(np.float32).ravel())

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
                    # the lining a little inside the skin, thickening toward the corner into the lips' fleshy commissure
                    P[0] -= sgn * (0.0 if layer == 0 else MO["web_thickness"] + MO["corner_thickness"] * u ** 3)
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
        # the front edge closed: the skin rolls round into the lining in a half round bowed forward (the mouth's
        # corner, a fleshy commissure, not two loose sheets showing their edges)
        NR = 6
        o0, i0 = NU * (NV + 1), (NU + 1) * (NV + 1) + NU * (NV + 1)  # the front rows of the two layers
        rows = [[o0 + j for j in range(NV + 1)]]
        for k in range(1, NR):
            a = math.pi * k / NR
            row = []
            for j in range(NV + 1):
                O, I = np.array(vs[o0 + j]), np.array(vs[i0 + j])
                half = np.linalg.norm(O - I) / 2
                P = O + (I - O) * (1 - math.cos(a)) / 2 + np.array([0.0, 0.0, 1.0]) * half * math.sin(a)
                row.append(len(vs)); vs.append(tuple(P)); ws.append(ws[o0 + j])
                ps.append(ps[o0 + j] if k < NR / 2 else 3.0); As.append(1.0); Bs.append(Bs[o0 + j]); bulge.append(bulge[o0 + j])
            rows.append(row)
        rows.append([i0 + j for j in range(NV + 1)])
        for r0, r1 in zip(rows, rows[1:]):
            for j in range(NV):
                q = [r0[j], r0[j + 1], r1[j + 1], r1[j]]
                fs.append(q if sgn > 0 else q[::-1])
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
            # the upper tooth row just outside the lower one (outside_lower), as in a closed reptile's bite, and never
            # outside the lip (inset from the lip's edge)
            half_w = lambda z: min(interp(UPPER, z, 4) * muzzle_taper(z) * lip_tuck(z) - TS["inset"],
                                   interp(JAW, z, 3) - TT["lower"]["inset"] + TS["outside_lower"])
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
                tang = np.array([1.0, 0.0, 0.0]); length = FT["length"]
                fwd = np.array([0.0, 0.0, 1.0]); fwd = norm(fwd - (fwd @ d) * d)  # forward, square to the tooth
                # across the front the jaw runs sideways, so these are flattened front to back
                n = tooth(vs, fs, base, d, fwd, length, TT["thickness"] * 0.5, length * TT["base_frac"] * 0.5, recurve=TT["recurve"] * 0.5)
                ws += [[(bone, 1.0)]] * n
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
                n = tooth(vs, fs, base, d, tang, length, length * TT["base_frac"] * 0.5, TT["thickness"] * 0.5,
                          recurve=TT["recurve"])
                ws += [[(bone, 1.0)]] * n
        objs.append(add_part("Teeth" + ("Lower" if jaw_side else "Upper"), vs, fs, {"_PART": [4] * len(vs), "_A": [0] * len(vs), "_B": [0] * len(vs), "_ZONE": [0] * len(vs)}, ws))

    # tongue: a muscular body lying in the trough of the mouth's floor, on three bones: rounded across with a
    # shallow groove down its middle (the median sulcus), thick at the root and thinning to a broad, rounded,
    # free tip that can lift off the floor (mouth.tongue)
    TG = MO["tongue"]
    def tongue_contour(z):
        u = (TG["tip_z"] - z) / (TG["tip_z"] - TG["root_z"])  # 0 at the tip, 1 at the root
        w = TG["width"] * (1 - 0.15 * u) * math.sqrt(max(0.0, 1 - (1 - min(1.0, u / TG["tip_round"])) ** 2))
        w = max(w, 0.002)
        h = TG["thickness"][0] + (TG["thickness"][1] - TG["thickness"][0]) * u ** 0.7
        h *= max(0.15, math.sqrt(max(0.0, 1 - (1 - min(1.0, u / TG["tip_round"])) ** 2)))
        y0 = interp(JAW, z, 1) - MO["floor_trough"] * smoothstep(MO["hinge_z"], MO["hinge_z"] + 0.06, z) + TG["lift"] * (1 - u) ** 2 - 0.002
        pts = []
        for i in range(N_AROUND + 1):
            th = math.pi * i / N_AROUND
            x = w * math.cos(th)
            groove = TG["groove"] * math.exp(-(x / (0.22 * w)) ** 2) * min(1.0, u * 4)
            pts.append((x, y0 + (h * math.sin(th) ** 0.55) - groove * math.sin(th) ** 4))
        return pts, y0
    zt = np.concatenate([np.linspace(TG["tip_z"], TG["tip_z"] - 0.03, 8)[:-1], np.linspace(TG["tip_z"] - 0.03, TG["root_z"], 18)])
    v, f, uv = loft(tongue_contour, zt)
    tw = []
    for (x, y, z) in v:
        t = (TG["tip_z"] - z) / (TG["tip_z"] - TG["root_z"])
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
        # ear: a flap of skin on a thin stalk growing out of the face's flesh at the top-back corner of the cheek (where
        # the S line behind the cheek begins), flaring into a leaf that lies back along the head under the horn and
        # curls round its length like a tulip petal, the upper front edge rolling over furthest: cream inside, orange
        # outside (user). Its section is one closed loop, inside then outside; the loft rises tangentially out of a
        # small footprint on the face's own surface (a fillet), so the face's skin runs on into the stalk (_A < 0)
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
            # a narrow stalk at the root, flaring into the flap (widest about halfway), narrowing to the tip
            half = FRILL["width"] / 2 * (FRILL["stalk"] + (1 - FRILL["stalk"]) * math.sin(math.pi * min(1.0, a / FRILL["widest_at"]) / 2) ** 1.5) \
                * (1 if a <= FRILL["widest_at"] else math.cos(math.pi / 2 * (a - FRILL["widest_at"]) / (1 - FRILL["widest_at"])) ** 0.8)
            t = c * (up if c > 0 else lo)  # angle round the arc from the bottom of the hollow
            o = base + L * a * length + nrm * half * dk
            p = o + W * half * math.sin(t) - nrm * half * dk * math.cos(t)
            if out:  # the outside of the flap: the skin's thickness further from the curl's centre (thicker at the stalk)
                q = p - o; q = q / (np.linalg.norm(q) + 1e-9)
                p = p + q * (th * (1 - 0.5 * a) + FRILL["body"] * (1 - a) ** 3)
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
             ("jaw", HINGE, (0, 1.24, 1.985), "head"),
             ("tongue1", (0, 1.42, 1.56), (0, 1.37, 1.68), "jaw"),
             ("tongue2", (0, 1.37, 1.68), (0, 1.32, 1.80), "tongue1"),
             ("tongue3", (0, 1.32, 1.80), (0, 1.29, 1.93), "tongue2")]
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
