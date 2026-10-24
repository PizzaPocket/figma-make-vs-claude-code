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
CREST = D["nose_crest"]
HORN = D["horn"]
FRILL = D["ear_frill"]
N_AROUND = 64  # points around the face contour (fine enough to carry the lid creases)


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


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def brush_offset(z, y):
    """Outward (+) / inward (-) offset of the side surface from the anatomy layers (bone, muscle, skin)."""
    off = 0.0
    for b in BRUSHES:
        k = b["kind"]
        if k == "dent":
            d = math.hypot(z - b["zy"][0], y - b["zy"][1])
            off -= b["depth"] * math.exp(-(d / b["radius"]) ** 2)
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
        elif k == "shelf":  # a bony ridge: crisp on its upper edge, sloping off below, tapering at its ends
            d, above, end = seg_dist(z, y, b["zy"])
            w = b["width_up"] if above else b["width_down"]
            off += b["height"] * math.exp(-(d / w) ** 2) * smoothstep(-0.01, 0.04, end)
        else:
            d, _, end = seg_dist(z, y, b["zy"])
            amt = b["height"] if k == "ridge" else -b["depth"]
            off += amt * math.exp(-(d / b["width"]) ** 2) * smoothstep(-0.01, 0.02, end)
    return off


# ---------------------------------------------------------------- face
def face_pt(z, th):
    """Point on the face at station z, angle th (0 = left lip edge, pi/2 = top, pi = right lip edge).
    Boxy cross-section (flat top, steep sides, cheeks wider than the top), then the brushes."""
    top, low, wt, wb = (interp(UPPER, z, c) for c in (1, 2, 3, 4))
    b = top - low
    c, s = math.cos(th), math.sin(th)
    yy = b * abs(s) ** (2 / SQ)
    a = wb + (wt - wb) * (yy / b) ** 1.6
    x = a * math.copysign(abs(c) ** (2 / SQ), c)
    y = low + yy
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
    return [face_pt(z, math.pi * i / N_AROUND) for i in range(N_AROUND + 1)], interp(UPPER, z, 2)


def jaw_contour(z):
    top, bot, w = (interp(JAW, z, c) for c in (1, 2, 3))
    b = top - bot
    pts = []
    for i in range(N_AROUND + 1):
        th = math.pi * i / N_AROUND  # 0 = one edge, pi/2 = chin bottom, pi = other edge
        c, s = math.cos(th), math.sin(th)
        n = 2.6
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


def roof_ring(z, K=26):
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


def crest_ring(z, K=22):
    st = np.array(CREST["stations"])
    half, h = (float(np.interp(-z, -st[:, 0], st[:, c])) for c in (1, 2))
    t, _ = roof_t(z)
    nz0, nz1 = CREST["nostril"]["z"]
    fr0, fr1 = CREST["nostril"]["side_frac"]
    outer, inner, nost = [], [], []
    for i in range(K):
        u = -1 + 2 * i / (K - 1)  # across the crest
        th = math.pi / 2 + u * half
        x, y = face_pt(z, th)
        nx, ny = face_normal(z, th)
        hh = h * max(0.0, 1 - u * u) ** 0.8  # centre ridge, flattening onto the roof at the flare's outer corner
        w = 0.0
        if nz1 <= z <= nz0 and fr0 <= abs(u) <= fr1:  # nostril: a trough under each flare
            w = math.sin(math.pi * (nz0 - z) / (nz0 - nz1)) * math.sin(math.pi * (abs(u) - fr0) / (fr1 - fr0))
        hh = max(0.0006, hh - CREST["nostril"]["depth"] * w)
        outer.append((x + nx * (t + hh), y + ny * (t + hh), z))
        inner.append((x + nx * (t - 0.004), y + ny * (t - 0.004), z))
        nost.append(w)
    return outer, inner, nost


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
    for k in (0, len(idx) - 1):
        r = idx[k]
        c = len(verts)
        verts.append(tuple(np.mean([verts[i] for i in r], 0))); A.append(A[r[0]]); B.append(0.0); Z.append(0.5)
        for i in range(M):
            j = (i + 1) % M
            faces.append([r[j], r[i], c] if k == 0 else [r[i], r[j], c])
    return verts, faces, A, B, Z


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
        # inner (mouth-side) surface between the two lip edges
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


def horn_from_roof(sgn, around=24, step=0.001):
    """The horn grown out of the roof's back corner. Its first cross-section is the roof's corner itself
    (the outer surface from the eave up over the shoulder, closed by a chord buried in the face), so the
    roof's top line runs on into the horn's top and the eave wraps under its root. Over `blend` of its
    length that section morphs into the horn's round section, which then carries the incised rings."""
    zc, top_th = HORN["root"]["z"], HORN["root"]["top_angle"]
    th_e = eave_th(zc)
    t, _ = roof_t(zc)
    loop = []
    for th in np.linspace(th_e, top_th, 14):  # outer: eave up over the shoulder
        x, y = face_pt(zc, th); nx, ny = face_normal(zc, th)
        loop.append((x + nx * t, y + ny * t))
    for f in np.linspace(0, 1, 8)[1:-1]:  # chord back down, buried inside the face
        (x0, y0), (x1, y1) = loop[-1], loop[0]
        loop.append((x0 + (x1 - x0) * f - 0.035 * math.sin(math.pi * f), y0 + (y1 - y0) * f - 0.01 * math.sin(math.pi * f)))
    loop = np.array([(sgn * x, y, zc) for x, y in loop])
    centre = loop.mean(0)
    path = [centre.tolist()] + [[sgn * p[0], p[1], p[2]] for p in HORN["path"]]
    C, R, s, N, Bv = spline_frames(path, HORN["radius"], step)
    T = np.cross(N, Bv)
    total = s[-1]
    # resample the root loop evenly and express it in the start frame
    seg = np.linalg.norm(np.diff(np.vstack([loop, loop[:1]]), axis=0), axis=1)
    cs = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, cs[-1], around, endpoint=False)
    closed = np.vstack([loop, loop[:1]])
    pts = np.stack([np.interp(u, cs, closed[:, k]) for k in range(3)], 1) - C[0]
    off = np.stack([pts @ N[0], pts @ Bv[0], pts @ T[0]], 1)
    phi = np.arctan2(off[:, 1], off[:, 0])
    G = HORN["grooves"]; blend = HORN["root"]["blend"]
    verts, A, B = [], [], []
    for i in range(len(C)):
        w = smoothstep(0.0, blend, s[i])
        g = 0.0
        if G["start_s"] <= s[i] <= G["end_frac"] * total:
            m = (s[i] - G["start_s"]) % G["every"]
            g = math.exp(-(min(m, G["every"] - m) / G["width"]) ** 2)
        r = R[i] - G["depth"] * g
        for k in range(around):
            root = N[i] * off[k, 0] + Bv[i] * off[k, 1] + T[i] * off[k, 2]
            ring = (N[i] * math.cos(phi[k]) + Bv[i] * math.sin(phi[k])) * r
            verts.append(tuple(C[i] + root * (1 - w) + ring * w))
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


def lid(c, R, a, g, u, phi0, phi1, inset, thick, nps=18, nph=10):
    """A lid: a thick shell around the eye. psi runs along the canthal axis (so the lid pinches to the
    two corners: the almond), phi around it from the margin (phi0) back into the socket (phi1).
    The outer and inner layers meet in a rounded rim at the margin. _A is 0 at the margin."""
    verts, faces, A = [], [], []
    rows = [(R + thick * 0.5 * (1 - math.cos(math.pi * k / 4)), phi0 - math.copysign(math.radians(4), phi1 - phi0) * math.sin(math.pi * k / 4))
            for k in range(5)]  # the rim: a half-round from the outer to the inner layer, bulging past the margin
    layers = [(R + thick, phi0 + (phi1 - phi0) * j / nph) for j in range(nph, 0, -1)] + \
             [(R + thick - (r - R), ph) for r, ph in rows] + \
             [(R, phi0 + (phi1 - phi0) * j / nph) for j in range(1, nph + 1)]
    n = len(layers)
    for i in range(nps + 1):
        psi = inset + (math.pi - 2 * inset) * i / nps
        for j, (rr, phi) in enumerate(layers):
            d = a * math.cos(psi) + math.sin(psi) * (g * math.cos(phi) + u * math.sin(phi))
            verts.append(tuple(np.asarray(c) + d * rr)); A.append(abs(j - (n - 1) / 2) / ((n - 1) / 2))
    for i in range(nps):
        for j in range(n - 1):
            p = i * n + j; q = p + n
            faces.append([p, q, q + 1, p + 1])
    return verts, faces, A


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
    rigid = lambda n: [[("head", 1.0)]] * n

    # face: the orange mass, dense rings near the nose where the shape changes fastest
    z0, z1 = UPPER[0, 0], UPPER[-1, 0]
    zs = np.concatenate([np.linspace(z0, 1.86, 20), np.linspace(1.85, z1, 120)])
    v, f, uv = loft(upper_contour, zs)
    hf = []
    for (x, y, z), (_, w) in zip(v, uv):
        low, top = interp(UPPER, z, 2), interp(UPPER, z, 1)
        hf.append((y - low) / max(top - low, 1e-6))
    # the closed underside in front of the jaw is the overhanging upper lip (skin), not the palate
    part = [1.0 if uv[i][1] >= 0 or v[i][2] > JAW[0, 0] - 0.01 else 3.0 for i in range(len(v))]
    objs.append(add_part("Face", v, f, {"_PART": part, "_A": [u[0] for u in uv], "_B": hf, "_ZONE": [0] * len(v)}, rigid(len(v))))

    # roof: banded shell over the face; its eave stands proud of the orange
    rz = band_zs(z0, ROOF["back_z"], 60)
    rings, at = [], []
    for z in rz:
        outer, inner, fb = roof_ring(z)
        rings.append((outer, inner)); at.append((fb, [fb] * len(outer)))
    v, f, A, B, Z = shell_loft(rings, at)
    objs.append(add_part("Roof", v, f, {"_PART": [10] * len(v), "_A": A, "_B": B, "_ZONE": Z}, rigid(len(v))))

    # nose crest on the front of the roof, nostrils under its flares
    cz = np.linspace(CREST["z"][0], CREST["z"][1], 22)
    rings, at = [], []
    for z in cz:
        outer, inner, nost = crest_ring(z)
        rings.append((outer, inner)); at.append((z, nost))
    v, f, A, B, Z = shell_loft(rings, at)
    objs.append(add_part("NoseCrest", v, f, {"_PART": [11] * len(v), "_A": A, "_B": B, "_ZONE": Z}, rigid(len(v))))

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

    lid_bones = []
    for sgn in (1, -1):
        sd = "L" if sgn > 0 else "R"
        # eye: find the face surface beside the eye and sink the eyeball into it
        ez, ey, er = EYE["centre_zy"][0], EYE["centre_zy"][1], EYE["radius"]
        pts, _ = upper_contour(ez)
        sx = max(abs(x) for x, y in pts if abs(y - ey) < 0.03)
        c = np.array([sgn * (sx - er * EYE["sink"]), ey, ez])  # sx: the face surface, raised there by the lid ring
        g, a, u = eye_frame(sgn)
        v, f, uv = sphere(c, er, up=g)
        objs.append(add_part("Eye" + sd, v, f, {"_PART": [6] * len(v), "_A": [q[0] for q in uv], "_B": [0] * len(v), "_ZONE": [0] * len(v)}, rigid(len(v))))
        # lids: shells hinged on the canthal axis. The bone axis is chosen so a positive turn about it closes the lid.
        hinge = a if np.allclose(np.cross(a, u), g, atol=1e-6) else -a
        R = er * EYE["lid_scale"]; inset = math.radians(EYE["canthus_inset_deg"])
        for name, phi0, phi1, axis in (("Upper", math.radians(EYE["upper_lid_open_deg"]), math.radians(170), hinge),
                                       ("Lower", -math.radians(EYE["lower_lid_open_deg"]), -math.radians(170), -hinge)):
            bn = f"lid{name}.{sd}"
            v, f, A = lid(c, R, a, g, u, phi0, phi1, inset, er * EYE["lid_thickness"])
            objs.append(add_part(f"Lid{name}{sd}", v, f, {"_PART": [7] * len(v), "_A": A, "_B": [0] * len(v), "_ZONE": [0] * len(v)}, [[(bn, 1.0)]] * len(v)))
            lid_bones.append((bn, c, c + axis * 0.04))
        # horn: grown out of the roof's back corner; smooth, with incised ring lines
        v, f, A, B = horn_from_roof(sgn)
        objs.append(add_part("Horn" + sd, v, f, {"_PART": [8] * len(v), "_A": A, "_B": B, "_ZONE": [0] * len(v)}, rigid(len(v))))
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
                             rigid(len(vs))))

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
    for bn, h0, h1 in lid_bones:
        bone(bn, h0, h1, "head")
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
