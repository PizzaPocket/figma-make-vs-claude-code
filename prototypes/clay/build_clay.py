"""Build a rigged Clay (.glb) in Blender from clay_design.json.

The design file describes Clay as data: body cross-sections, the rules for each
zone's plates and scales, and the raised features (tail studs, wing-arm blocks,
finger studs, hooked claws, ridged horns, mane, ear frills, eyes). This script
turns that into one continuous skinned mesh, carving the large plates into the
surface, and writes per-vertex data the viewer uses for colour and fine detail.
Model space: x = Clay's left, y = up, z = forward. Bind pose = reference pose.
"""
import json
import math
import sys
import time

import bpy  # bmesh is only importable once bpy is loaded
import bmesh
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import measure

ARGS = dict(zip(sys.argv[1::2], sys.argv[2::2]))
OUT = ARGS.get("--out", "clay.glb")
DESIGN = json.load(open(ARGS.get("--design", "clay_design.json")))
CELL = 0.011
BLEND = 0.05
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


def ref_to_model(px, py):
    return (700 - px) / 343.0, (830 - py) / 343.0  # z, y


ROWS = np.array(DESIGN["body_stations"]["rows"], float)
FEAT = DESIGN["features"]

# ---------------------------------------------------------------- skeleton (rest pose = reference pose)
CENTER = {
    "hips": (0, 1.055, -0.87), "spine1": (0, 1.065, -0.29), "spine2": (0, 1.02, 0.29), "chest": (0, 1.10, 0.80),
    "neck1": (0, 1.18, 0.98), "neck2": (0, 1.33, 1.13), "neck3": (0, 1.46, 1.25), "head": (0, 1.57, 1.36),
    "tail1": (0, 1.015, -1.17), "tail2": (0, 0.95, -1.50), "tail3": (0, 0.82, -1.90), "tail4": (0, 0.62, -2.40),
    "tail5": (0, 0.45, -2.90), "tail6": (0, 0.32, -3.40),
}
PARENT = {"hips": None, "spine1": "hips", "spine2": "spine1", "chest": "spine2", "neck1": "chest", "neck2": "neck1",
          "neck3": "neck2", "head": "neck3", "tail1": "hips", "tail2": "tail1", "tail3": "tail2", "tail4": "tail3",
          "tail5": "tail4", "tail6": "tail5"}
TAILS = {"hips": "spine1", "spine1": "spine2", "spine2": "chest", "chest": "neck1", "neck1": "neck2", "neck2": "neck3",
         "neck3": "head", "head": (0, 1.42, 2.02), "tail1": "tail2", "tail2": "tail3", "tail3": "tail4", "tail4": "tail5",
         "tail5": "tail6", "tail6": (0, 0.16, -4.30)}
WING_ROOT = (0.30, 1.30, 0.62)
ELBOW = (0.62, *reversed(ref_to_model(800, 430)))
WRIST = (0.72, *reversed(ref_to_model(745, 790)))
FINGER_TIPS = [ref_to_model(1380, 15), ref_to_model(1275, 15), ref_to_model(1155, 45), ref_to_model(1035, 85), ref_to_model(915, 185)]
FINGER_TIPS = [(0.86, y, z) for z, y in FINGER_TIPS]
SIDE = {
    "upperArmL": ((0.34, 0.95, 0.78), "chest"), "foreArmL": ((0.40, 0.50, 0.62), "upperArmL"), "handL": ((0.38, 0.14, 0.78), "foreArmL"),
    "thighL": ((0.36, 0.95, -0.85), "hips"), "shinL": ((0.46, 0.55, -0.55), "thighL"), "metaL": ((0.45, 0.26, -1.00), "shinL"),
    "footL": ((0.45, 0.08, -0.86), "metaL"), "wing1L": (WING_ROOT, "chest"), "wing2L": (ELBOW, "wing1L"),
}
SIDE_TAILS = {"upperArmL": "foreArmL", "foreArmL": "handL", "handL": (0.38, 0.04, 1.02), "thighL": "shinL", "shinL": "metaL",
              "metaL": "footL", "footL": (0.45, 0.04, -0.60), "wing1L": "wing2L", "wing2L": WRIST}
for f, tip in enumerate(FINGER_TIPS, 1):
    mid = tuple(WRIST[i] + (tip[i] - WRIST[i]) * 0.48 + (0.04 if i == 0 else 0) for i in range(3))
    SIDE[f"f{f}aL"] = (WRIST, "wing2L"); SIDE[f"f{f}bL"] = (mid, f"f{f}aL")
    SIDE_TAILS[f"f{f}aL"] = f"f{f}bL"; SIDE_TAILS[f"f{f}bL"] = tip
FLANK = (0.64, 0.42, -1.00)  # the inner membrane runs down to the hind leg near the ankle


def mirror(name):
    return name[:-1] + "R" if name.endswith("L") else name


def joints():
    pos, par, tail = {}, {}, {}
    for n, p in CENTER.items():
        pos[n] = p; par[n] = PARENT[n]
    for n, (p, pr) in SIDE.items():
        for s in (1, -1):
            nn = n if s > 0 else mirror(n)
            pos[nn] = (s * p[0], p[1], p[2]); par[nn] = pr if s > 0 else mirror(pr)
    for n, t in list(TAILS.items()) + list(SIDE_TAILS.items()):
        for s in ((1,) if n in CENTER else (1, -1)):
            nn = n if s > 0 else mirror(n)
            tail[nn] = pos[t if s > 0 else mirror(t)] if isinstance(t, str) else (s * t[0], t[1], t[2])
    return pos, par, tail


JPOS, JPAR, JTAIL = joints()


# ---------------------------------------------------------------- body loft
def build_loft():
    P = ROWS
    out = []
    SUB = 6
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
        for k in range(SUB):
            t = k / SUB
            cr = lambda a, b, c, d: 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
            out.append([cr(p0[0], p1[0], p2[0], p3[0]), cr(p0[1], p1[1], p2[1], p3[1]), *(p1[2:] + (p2[2:] - p1[2:]) * t)])
    out.append(list(P[-1]))
    L = np.array(out)  # z, y, top, bot, w, e, dark_above, cream_below
    d = np.diff(L[:, :2], axis=0)
    s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
    tang = np.zeros((len(L), 2))
    tang[1:-1] = L[2:, :2] - L[:-2, :2]; tang[0] = L[1, :2] - L[0, :2]; tang[-1] = L[-1, :2] - L[-2, :2]
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    return L, s, tang, np.stack([tang[:, 1], -tang[:, 0]], 1)


LOFT, LOFT_S, LOFT_T, LOFT_N = build_loft()


def loft_query(x, y, z, want=False):
    best = np.full(x.shape, np.inf)
    bs = np.zeros(x.shape); bh = np.zeros(x.shape); bi = np.zeros(x.shape, int); bth = np.zeros(x.shape); br = np.zeros(x.shape)
    for i in range(len(LOFT) - 1):
        A, B = LOFT[i], LOFT[i + 1]
        m = (y > min(A[1], B[1]) - 0.75) & (y < max(A[1], B[1]) + 0.75) & (z > min(A[0], B[0]) - 0.75) & (z < max(A[0], B[0]) + 0.75)
        if not m.any():
            continue
        xs, ys, zs = x[m], y[m], z[m]
        dz, dy = B[0] - A[0], B[1] - A[1]
        t = ((zs - A[0]) * dz + (ys - A[1]) * dy) / (dz * dz + dy * dy)
        tc = np.clip(t, 0, 1)
        cz, cy = A[0] + dz * tc, A[1] + dy * tc
        nz = LOFT_N[i, 0] + (LOFT_N[i + 1, 0] - LOFT_N[i, 0]) * tc
        ny = LOFT_N[i, 1] + (LOFT_N[i + 1, 1] - LOFT_N[i, 1]) * tc
        tz = LOFT_T[i, 0] + (LOFT_T[i + 1, 0] - LOFT_T[i, 0]) * tc
        ty = LOFT_T[i, 1] + (LOFT_T[i + 1, 1] - LOFT_T[i, 1]) * tc
        qn = ((zs - cz) * nz + (ys - cy) * ny) / np.hypot(nz, ny)
        qt = ((zs - cz) * tz + (ys - cy) * ty) / np.hypot(tz, ty)
        w = A[4] + (B[4] - A[4]) * tc
        e = A[5] + (B[5] - A[5]) * tc
        a = np.where(qn >= 0, A[2] + (B[2] - A[2]) * tc, A[3] + (B[3] - A[3]) * tc)
        r = (np.abs(xs / w) ** e + np.abs(qn / a) ** e) ** (1 / e)
        d = (r - 1) * np.minimum(w, a)
        out = (t < 0) | (t > 1)
        d = np.where(out, np.where(d > 0, np.hypot(d, qt), np.maximum(d, np.abs(qt))), d)
        better = d < best[m]
        idx = np.where(m)[0][better]
        best[idx] = d[better]
        if want:
            bs[idx] = (LOFT_S[i] + (LOFT_S[i + 1] - LOFT_S[i]) * tc)[better]
            bh[idx] = (qn / a)[better]
            bi[idx] = i
            bth[idx] = np.arctan2(xs, qn)[better]
            br[idx] = (0.5 * (w + 0.5 * (A[2] + A[3])))[better]
    return (best, bs, bh, bi, bth, br) if want else best


def loft_top(z):
    """Centre-line point, normal, tangent and top half-height at a given z."""
    i = int(np.argmin(np.abs(LOFT[:, 0] - z)))
    return LOFT[i], LOFT_N[i], LOFT_T[i], LOFT_S[i]


# ---------------------------------------------------------------- shapes and features
def frame_from(dir_, up=(0, 1, 0)):
    a = np.array(dir_, float); a /= np.linalg.norm(a)
    b = np.cross(up, a)
    if np.linalg.norm(b) < 1e-6:
        b = np.cross((1, 0, 0), a)
    b /= np.linalg.norm(b); c = np.cross(a, b)
    return np.stack([a, b, c], 1)  # columns: along, side, up


def shapes():
    S = []
    def cone(bone, a, ra, b, rb, group="limb"): S.append(dict(t="cone", bone=bone, a=np.array(a, float), ra=ra, b=np.array(b, float), rb=rb, group=group))
    def ell(bone, c, r, group="body"): S.append(dict(t="ell", bone=bone, c=np.array(c, float), r=np.array(r, float), group=group))
    def box(bone, c, h, r, group="limb", R=None): S.append(dict(t="box", bone=bone, c=np.array(c, float), h=np.array(h, float), r=r, group=group, R=R))
    def hook(bone, base, fwd, length, r0, group="claw"):
        """A curved claw: three segments bending down toward the ground."""
        p = np.array(base, float); d = np.array(fwd, float); d /= np.linalg.norm(d)
        rad = r0
        for k in range(3):
            d = d + np.array([0, -0.45, 0]); d /= np.linalg.norm(d)
            q = p + d * length / 3
            cone(bone, p, rad, q, rad * 0.6 if k < 2 else 0.004, group)
            p, rad = q, rad * 0.6
    tailS = FEAT["tail_studs"]
    for s in (1, -1):
        n = (lambda b: b) if s > 0 else mirror
        X = lambda v: s * v
        P = lambda p: (s * p[0], p[1], p[2])
        b = FEAT["eye"]["brow"]
        ell("head", (X(b["centre"][0]), b["centre"][1], b["centre"][2]), b["radii"])
        # front leg
        ell(n("upperArmL"), (X(0.35), 0.84, 0.76), (0.17, 0.25, 0.22), "limb")
        cone(n("upperArmL"), (X(0.34), 0.95, 0.78), 0.17, (X(0.40), 0.50, 0.62), 0.115)
        cone(n("foreArmL"), (X(0.40), 0.50, 0.62), 0.11, (X(0.38), 0.14, 0.78), 0.075)
        box(n("handL"), (X(0.38), 0.07, 0.89), (0.10, 0.03, 0.11), 0.04)
        for dx in (-0.085, 0, 0.085):
            cone(n("handL"), (X(0.38 + dx * 0.6), 0.07, 0.93), 0.045, (X(0.38 + dx * 1.1), 0.05, 1.05), 0.034)
            hook(n("handL"), (X(0.38 + dx * 1.1), 0.05, 1.05), (X(dx * 0.3), 0.15, 1), 0.13, 0.03)
        hook(n("handL"), (X(0.44), 0.14, 0.80), (X(0.3), -0.2, 0.4), 0.08, 0.022)
        # hind leg
        ell(n("thighL"), (X(0.39), 0.80, -0.72), (0.20, 0.31, 0.30), "limb")
        cone(n("thighL"), (X(0.36), 0.95, -0.85), 0.21, (X(0.46), 0.55, -0.55), 0.135)
        cone(n("shinL"), (X(0.46), 0.55, -0.55), 0.12, (X(0.45), 0.26, -1.00), 0.078)
        cone(n("metaL"), (X(0.45), 0.26, -1.00), 0.078, (X(0.45), 0.08, -0.86), 0.07)
        box(n("footL"), (X(0.45), 0.07, -0.76), (0.11, 0.035, 0.13), 0.045)
        for dx in (-0.095, 0, 0.095):
            cone(n("footL"), (X(0.45 + dx * 0.5), 0.07, -0.70), 0.05, (X(0.45 + dx), 0.05, -0.56), 0.04)
            hook(n("footL"), (X(0.45 + dx), 0.05, -0.56), (X(dx * 0.3), 0.15, 1), 0.13, 0.032)
        # folded wing arm and fingers
        ell(n("wing1L"), P((0.30, 1.30, 0.58)), (0.14, 0.12, 0.2), "wing")
        cone(n("wing1L"), P(WING_ROOT), 0.11, P(ELBOW), 0.085, "wing")
        cone(n("wing2L"), P(ELBOW), 0.075, P(WRIST), 0.055, "wing")
        for k, fwd in enumerate(((0.1, 0, 1), (0.2, 0, -0.6))[:FEAT["wrist_claws"]]):
            hook(n("wing2L"), P((WRIST[0] + 0.02, WRIST[1] - 0.02, WRIST[2] + (0.05 if k == 0 else -0.04))), P(fwd), 0.15, 0.035)
        for f in range(1, 6):
            mid = JPOS[f"f{f}bL"]; tip = JTAIL[f"f{f}bL"]
            cone(n(f"f{f}aL"), P(WRIST), 0.04, P(mid), 0.038, "wing")
            cone(n(f"f{f}bL"), P(mid), 0.038, P(tip), 0.026, "wing")
            dd = np.array(tip) - np.array(mid); dd /= np.linalg.norm(dd)
            hook(n(f"f{f}bL"), P(tip), P(tuple(dd + np.array([0, 0.3, -0.6]))), 0.12, 0.024)
            # square studs down the outer face of each finger
            fs = FEAT["finger_studs"]
            for seg, (a0, b0, bone) in enumerate(((WRIST, mid, f"f{f}aL"), (mid, tip, f"f{f}bL"))):
                a0, b0 = np.array(a0), np.array(b0)
                L_ = np.linalg.norm(b0 - a0); along = (b0 - a0) / L_
                R = frame_from(P(tuple(along)) if s < 0 else along, up=(1, 0, 0))
                for k in range(int(L_ / fs["spacing"])):
                    c = a0 + along * (k + 0.5) * fs["spacing"]
                    rad = 0.038 + (0.026 - 0.038) * ((k + 0.5) * fs["spacing"] / L_) if seg else 0.04
                    c = c + np.array([rad * 0.85, 0, 0])
                    box(n(bone), P(tuple(c)), (fs["size"] / 2, fs["size"] / 2, 0.012), 0.004, "wingplate", R=R)
        # raised blocks along the leading edge of the wing arm
        wb = FEAT["wing_arm_blocks"]
        for a0, b0, bone, cnt, off in ((WING_ROOT, ELBOW, "wing1L", wb["humerus"], np.array([0.0, 0.105, 0.0])),
                                       (ELBOW, WRIST, "wing2L", wb["forearm"], np.array([0.0, 0.0, 0.075]))):
            a0, b0 = np.array(a0), np.array(b0)
            along = (b0 - a0) / np.linalg.norm(b0 - a0)
            for k in range(cnt):
                t = 0.08 + 0.84 * k / max(1, cnt - 1)
                c = a0 + (b0 - a0) * t + off * (1 - 0.3 * t)
                R = frame_from(along if s > 0 else (-along[0], along[1], along[2]))
                box(n(bone), P(tuple(c)), (wb["size"][0] / 2, wb["size"][1] / 2, wb["size"][2] / 2), 0.008, "wingplate", R=R)
    # leaf-shaped studs along the top of the tail
    for k in range(tailS["count"]):
        t = k / max(1, tailS["count"] - 1)
        z = tailS["first_z"] - k * tailS["spacing"]
        St, Nn, Tt, _ = loft_top(z)
        top = St[2]
        base = np.array([0, St[1] + Nn[1] * (top - 0.01), St[0] + Nn[0] * (top - 0.01)])
        L_ = tailS["length"][0] + (tailS["length"][1] - tailS["length"][0]) * t
        W_ = tailS["width"][0] + (tailS["width"][1] - tailS["width"][0]) * t
        H_ = tailS["height"][0] + (tailS["height"][1] - tailS["height"][0]) * t
        bone = min((b for b in CENTER if b.startswith("tail")), key=lambda b: abs(CENTER[b][2] - z - 0.15)) if z < -1.17 else "hips"
        R = frame_from((0, Tt[1], Tt[0]), up=(0, Nn[1], Nn[0]))
        rr = min(W_, H_) * 0.4
        box(bone, tuple(base + np.array([0, Nn[1], Nn[0]]) * H_ * 0.4),
            (max(L_ / 2 - rr, 0.01), max(W_ * 0.4 - rr, 0.005), max(H_ / 2 - rr, 0.003)), rr, "stud", R=R)
    return S


def sd_prim(s, x, y, z):
    shape = np.shape(x)
    return _sd_prim(s, np.ravel(x), np.ravel(y), np.ravel(z)).reshape(shape)


def _sd_prim(s, x, y, z):
    if s["t"] == "ell":
        c, r = s["c"], s["r"]
        px, py, pz = (x - c[0]) / r[0], (y - c[1]) / r[1], (z - c[2]) / r[2]
        k0 = np.sqrt(px * px + py * py + pz * pz)
        k1 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2)
        return k0 * (k0 - 1) / np.maximum(k1, 1e-9)
    if s["t"] == "box":
        p = np.stack([x - s["c"][0], y - s["c"][1], z - s["c"][2]])
        if s.get("R") is not None:
            p = s["R"].T @ p
        q = np.abs(p) - s["h"][:, None]
        return np.linalg.norm(np.maximum(q, 0), axis=0) + np.minimum(q.max(0), 0) - s["r"]
    a, b, ra, rb = s["a"], s["b"], s["ra"], s["rb"]
    ba = b - a
    l2 = ba @ ba
    rr = ra - rb
    a2 = l2 - rr * rr
    pa = np.stack([x - a[0], y - a[1], z - a[2]])
    yy = (pa * ba[:, None]).sum(0)
    zz = yy - l2
    q = pa * l2 - ba[:, None] * yy
    x2 = (q * q).sum(0)
    y2 = yy * yy * l2
    z2 = zz * zz * l2
    k = np.sign(rr) * rr * rr * x2
    d3 = (np.sqrt(np.maximum(x2 * a2 / l2, 0)) + yy * rr) / l2 - ra
    d1 = np.sqrt(x2 + z2) / l2 - rb
    d2 = np.sqrt(x2 + y2) / l2 - ra
    return np.where(np.sign(zz) * a2 * z2 > k, d1, np.where(np.sign(yy) * a2 * y2 < k, d2, d3))


def prim_bounds(s):
    if s["t"] == "cone":
        r = max(s["ra"], s["rb"])
        return np.minimum(s["a"], s["b"]) - r, np.maximum(s["a"], s["b"]) + r
    if s["t"] == "box":
        e = np.linalg.norm(s["h"]) + s["r"]
        return s["c"] - e, s["c"] + e
    return s["c"] - s["r"], s["c"] + s["r"]


def carve(x, y, z):
    """Mouth groove, nostrils and eye sockets."""
    m = FEAT["mouth"]
    (az, ay), (bz, by) = m["from_zy"], m["corner_zy"]
    dz, dy = bz - az, by - ay; l = math.hypot(dz, dy)
    t = ((z - az) * dz + (y - ay) * dy) / (l * l)
    off = np.abs((z - az) * (dy / l) - (y - ay) * (dz / l))
    # a shallow groove: only near the surface (|x| close to the head's half-width)
    i = np.clip(np.searchsorted(-LOFT[:, 0], -z), 0, len(LOFT) - 1)
    half_w = LOFT[i, 4]
    mouth = np.maximum.reduce([off - 0.008, (t - 1) * l, (-t) * l, half_w - FEAT["mouth"]["groove_depth"] - np.abs(x)])
    e = FEAT["eye"]; nostril = FEAT["nostril"]
    eye = np.sqrt((np.abs(x) - e["centre"][0]) ** 2 + (y - e["centre"][1]) ** 2 + (z - e["centre"][2]) ** 2) - e["radius"] * 1.05
    nos = np.sqrt((np.abs(x) - nostril["centre"][0]) ** 2 + (y - nostril["centre"][1]) ** 2 + (z - nostril["centre"][2]) ** 2) - nostril["radius"]
    return np.minimum.reduce([mouth, eye, nos])


# ---------------------------------------------------------------- surface relief from the zone rules
def body_relief(s, th, h, seg, R, z):
    """Large plates carved into the body: back plates, border squares, belly bands."""
    rules = DESIGN["surface_rules"]
    dark_t, cream_t = LOFT[seg, 6], LOFT[seg, 7]
    v = th * R
    rel = np.zeros_like(s)
    head = z > 1.35
    dark = h > dark_t
    cream = h < cream_t
    # back plates: overlapping, each plate's free edge raised toward the tail
    bp = rules["back_plates"]
    row = np.floor(v / bp["width"])
    f = (s / bp["length"] + bp["stagger"] * row) % 1.0
    plate = bp["relief_step"] * (f - 0.5)
    side = np.abs((v / bp["width"]) % 1.0 - 0.5)
    plate -= 0.006 * (side > 0.45)
    rel = np.where(dark & ~head, plate, rel)
    # head plate: segments across the dark plate on the snout and forehead
    hs = (s / rules["head_plate"]["segment"]) % 1.0
    rel = np.where(dark & head, -0.008 * (np.minimum(hs, 1 - hs) < 0.06), rel)
    # border of square plates where the dark back meets the orange (neck to tail)
    bs_ = rules["border_squares"]
    band = (np.abs(h - dark_t) < bs_["band_width_h"]) & (z < 1.3)
    fs = (s / bs_["size"]) % 1.0
    rel = np.where(band, bs_["relief"] * (np.minimum(fs, 1 - fs) > 0.12), rel)
    # belly bands, narrower on the throat; three columns under the tail
    bb = rules["belly_bands"]
    period = np.where(z > 0.95, bb["period_throat"], bb["period_body"])
    fb = (s / period) % 1.0
    bands = -bb["relief"] * (np.minimum(fb, 1 - fb) < 0.08) + 0.004 * np.sin(np.pi * fb)
    tail = z < -1.15
    cols = (np.abs(v) / 0.07) % 1.0
    bands = np.where(tail & (np.minimum(cols, 1 - cols) < 0.08), bands - 0.008, bands)
    rel = np.where(cream & ~head, bands, rel)
    # flank scales: a slight step at each row edge
    fl = (s / rules["flank_scales"]["row"]) % 1.0
    rel = np.where(~dark & ~cream & ~band & ~head, 0.004 * fl, rel)
    return rel


def limb_relief(t_along, around):
    g = DESIGN["surface_rules"]["limb_grid"]
    a = (t_along / g["size"]) % 1.0
    b = (around / g["size"]) % 1.0
    return -g["relief"] * ((np.minimum(a, 1 - a) < 0.08) | (np.minimum(b, 1 - b) < 0.08))


# ---------------------------------------------------------------- field and surface
GROUPS = ["body", "limb", "wing", "claw", "stud", "wingplate"]


def classify(S, x, y, z):
    """Nearest shape group per point, plus limb coordinates (along, around) from the nearest limb cone."""
    dl = np.where(np.abs(x) < 0.75, loft_query(x, y, z), np.inf)
    gd = {g: np.full(x.shape, np.inf) for g in GROUPS}
    gd["body"] = dl
    lt = np.zeros(x.shape); la = np.zeros(x.shape); lbest = np.full(x.shape, np.inf); lbone = np.zeros(x.shape, int)
    names = list(JPOS.keys())
    for s in S:
        lo, hi = prim_bounds(s)
        m = (x > lo[0] - 0.3) & (x < hi[0] + 0.3) & (y > lo[1] - 0.3) & (y < hi[1] + 0.3) & (z > lo[2] - 0.3) & (z < hi[2] + 0.3)
        if not m.any():
            continue
        d = sd_prim(s, x[m], y[m], z[m])
        idx = np.where(m)[0]
        gd[s["group"]][idx] = np.minimum(gd[s["group"]][idx], d)
        if s["group"] in ("limb", "wing") and s["t"] == "cone":
            better = d < lbest[idx]
            ii = idx[better]
            ab = s["b"] - s["a"]; L_ = np.linalg.norm(ab); u = ab / L_
            rel = np.stack([x[ii] - s["a"][0], y[ii] - s["a"][1], z[ii] - s["a"][2]], 1)
            lt[ii] = rel @ u + names.index(s["bone"]) * 3.7
            perp = rel - np.outer(rel @ u, u)
            ref_ = np.cross(u, [1.0, 0, 0]); ref_ /= max(np.linalg.norm(ref_), 1e-9); ref2 = np.cross(u, ref_)
            la[ii] = np.arctan2(perp @ ref2, perp @ ref_) * (0.5 * (s["ra"] + s["rb"]))
            lbest[ii] = d[better]
    part = np.argmin(np.stack([gd[g] for g in GROUPS]), 0)
    return part, lt, la, gd


def build_surface(S):
    lo = np.array([-1.0, -0.03, -4.40]); hi = np.array([1.0, 2.45, 2.12])
    n = np.ceil((hi - lo) / CELL).astype(int) + 1
    log(f"grid {n} = {n.prod() / 1e6:.1f}M cells")
    xs = lo[0] + np.arange(n[0]) * CELL; ys = lo[1] + np.arange(n[1]) * CELL; zs = lo[2] + np.arange(n[2]) * CELL
    body = np.zeros(n[::-1], np.float32); wing = np.zeros(n[::-1], np.float32)
    margin = 6 * BLEND
    ii = np.where(np.abs(xs) < 0.7)[0]
    dl = np.full((n[2], n[1], len(ii)), 1.0, np.float32)
    for k0 in range(0, n[2], 40):
        k1 = min(n[2], k0 + 40)
        Zg, Yg, Xg = np.meshgrid(zs[k0:k1], ys, xs[ii], indexing="ij")
        dl[k0:k1] = np.minimum(loft_query(Xg.ravel(), Yg.ravel(), Zg.ravel()).reshape(Zg.shape), 1.0)
    dl = gaussian_filter(dl, sigma=1.5)  # removes faint creases where loft segments meet
    body[:, :, ii[0]:ii[-1] + 1] += np.where(dl < margin, np.exp(-np.clip(dl, -1, margin) / BLEND), 0).astype(np.float32)
    del dl
    log("loft done")
    for s in S:
        blo, bhi = prim_bounds(s)
        i0, j0, k0 = np.maximum(0, np.floor((blo - margin - lo) / CELL).astype(int))
        i1, j1, k1 = np.minimum(n - 1, np.ceil((bhi + margin - lo) / CELL).astype(int))
        Zg, Yg, Xg = np.meshgrid(zs[k0:k1 + 1], ys[j0:j1 + 1], xs[i0:i1 + 1], indexing="ij")
        d = sd_prim(s, Xg, Yg, Zg)
        # small parts and the wing fingers join with a tight blend so they stay separate and crisp
        blend = 0.012 if s["group"] in ("claw", "stud", "wingplate") else 0.015 if s["bone"].startswith(("f1", "f2", "f3", "f4", "f5")) else BLEND
        wing_side = s["group"] in ("wing", "wingplate") or (s["group"] == "claw" and s["bone"].startswith(("wing", "f")))
        target = wing if wing_side else body
        # small parts join with a tighter blend so their shapes stay crisp
        target[k0:k1 + 1, j0:j1 + 1, i0:i1 + 1] += np.where(d < margin, np.exp(-np.clip(d, -1, margin) / blend), 0).astype(np.float32)
    log("shapes done")
    fb = np.where(body > 0, -BLEND * np.log(np.maximum(body, 1e-30)), 1.0).astype(np.float32)
    fw = np.where(wing > 0, -BLEND * np.log(np.maximum(wing, 1e-30)), 1.0).astype(np.float32)
    del body, wing
    Zg, Yg, Xg = np.meshgrid(zs, ys, xs, indexing="ij")
    near_root = np.exp(-(((np.abs(Xg) - WING_ROOT[0]) ** 2 + (Yg - WING_ROOT[1]) ** 2 + (Zg - WING_ROOT[2]) ** 2) / 0.06))
    k = (0.004 + 0.05 * near_root).astype(np.float32)
    m = np.minimum(fb, fw)
    F = m - k * np.log(np.exp(-(fb - m) / k) + np.exp(-(fw - m) / k))
    del fb, fw, k, m, near_root
    # carve the mouth groove, nostrils and eye sockets on the head
    sel = (Zg > 1.3) & (Yg > 1.2) & (Yg < 1.95) & (np.abs(Xg) < 0.35)
    c = carve(Xg[sel], Yg[sel], Zg[sel])
    F[sel] = np.maximum(F[sel], -c)
    del Xg, Yg, Zg, sel, c
    log("field done; marching cubes")
    verts, faces, normals, _ = measure.marching_cubes(F, level=0.0, spacing=(CELL, CELL, CELL))
    verts = verts[:, ::-1] + lo
    normals = normals[:, ::-1]
    log(f"surface: {len(verts)} verts")
    return verts, faces, normals


# ---------------------------------------------------------------- Blender helpers
def to_blender(p):
    p = np.asarray(p, float)
    return np.stack([p[..., 0], -p[..., 2], p[..., 1]], -1)


def from_blender(p):
    p = np.asarray(p, float)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], -1)


def make_mesh(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(to_blender(verts).tolist(), [], [list(map(int, f)) for f in faces])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def activate(ob, others=()):
    bpy.ops.object.select_all(action="DESELECT")
    for o in others:
        o.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def set_attrs(ob, attrs):
    for an, vals in attrs.items():
        a = ob.data.attributes.get(an) or ob.data.attributes.new(an, "FLOAT", "POINT")
        a.data.foreach_set("value", np.asarray(vals, np.float32))


def surface_data(S, V):
    """Per-vertex part, coordinates and colour zones for the viewer."""
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    part, lt, la, _ = classify(S, x, y, z)
    _, s_al, h_cr, seg, th, R = loft_query(x, y, z, want=True)
    seg = np.clip(seg, 0, len(LOFT) - 1)
    dark_t, cream_t = LOFT[seg, 6], LOFT[seg, 7]
    zb = np.clip((h_cr - dark_t + 0.03) / 0.06, 0, 1)
    zc = np.clip((cream_t + 0.03 - h_cr) / 0.06, 0, 1)
    edge = np.where(z < 1.3, np.clip(1 - np.abs(h_cr - dark_t) / 0.07, 0, 1), 0)
    body = part == 0
    U = np.where(body, s_al, lt)
    Vv = np.where(body, th * R, la)
    return part, U, Vv, np.where(body, zb, 0), np.where(body, zc, 0), np.where(body, edge, 0), h_cr


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    S = shapes()
    log(f"{len(S)} shapes and features")
    verts, faces, normals = build_surface(S)

    # carve the large plates into the surface (relief along the normal)
    part, lt, la, _ = classify(S, verts[:, 0], verts[:, 1], verts[:, 2])
    _, s_al, h_cr, seg, th, R = loft_query(verts[:, 0], verts[:, 1], verts[:, 2], want=True)
    rel = np.where(part == 0, body_relief(s_al, th, h_cr, np.clip(seg, 0, len(LOFT) - 1), R, verts[:, 2]), 0.0)
    rel = np.where(part == 1, limb_relief(lt, la), rel)
    nrm = normals / np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
    # marching-cubes normals point down the field gradient (inward); relief goes outward
    verts = verts - nrm * rel[:, None]
    log("relief carved")

    body = make_mesh("Clay", verts, faces)
    activate(body)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.verts.ensure_lookup_table()
    seen = set(); islands = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]; isl = []
        seen.add(v.index)
        while stack:
            u = stack.pop(); isl.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index); stack.append(w)
        islands.append(isl)
    drop = [v for isl in islands if len(isl) < 150 for v in isl]
    bmesh.ops.delete(bm, geom=drop, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.update_edit_mesh(body.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    sm = body.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); sm.iterations = 2; sm.use_only_smooth = True
    dec = body.modifiers.new("decimate", "DECIMATE"); dec.ratio = min(1.0, 110000 / len(body.data.vertices))
    bpy.ops.object.modifier_apply(modifier="smooth")
    bpy.ops.object.modifier_apply(modifier="decimate")
    for p in body.data.polygons:
        p.use_smooth = True
    log(f"decimated: {len(body.data.vertices)} verts")

    # armature
    arm_data = bpy.data.armatures.new("ClayRig")
    arm = bpy.data.objects.new("ClayRig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    activate(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name in JPOS:
        b = arm_data.edit_bones.new(name)
        b.head = to_blender(JPOS[name]).tolist(); b.tail = to_blender(JTAIL[name]).tolist()
        eb[name] = b
    for name, pr in JPAR.items():
        if pr:
            eb[name].parent = eb[pr]
    bpy.ops.object.mode_set(mode="OBJECT")
    activate(arm, [body])
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    log("bone heat weights done")

    groups = {g.index: g.name for g in body.vertex_groups}
    V = from_blender(np.array([v.co for v in body.data.vertices]))
    part, U, Vv, zb, zc, ze, hh = surface_data(S, V)
    # keep wing bones off the body (and body bones off the wing), except at the shoulder
    wing_bones = {i for i, nme in groups.items() if nme.startswith(("wing", "f"))}
    root_d = np.sqrt((np.abs(V[:, 0]) - WING_ROOT[0]) ** 2 + (V[:, 1] - WING_ROOT[1]) ** 2 + (V[:, 2] - WING_ROOT[2]) ** 2)
    wing_like = np.isin(part, [2, 5])
    for v in body.data.vertices:
        if root_d[v.index] < 0.3:
            continue
        for g in v.groups:
            if (g.group in wing_bones) != wing_like[v.index]:
                g.weight = 0.0
    # legs: the back of each leg is cream in the reference
    nrm_b = np.array([v.normal for v in body.data.vertices])
    nz = -nrm_b[:, 1]  # model z of the normal
    zc = np.where(part == 1, np.clip((-nz - 0.35) / 0.3, 0, 1), zc)
    set_attrs(body, {"_PART": part, "_U": U, "_V": Vv, "_ZBACK": zb, "_ZBELLY": zc, "_ZEDGE": ze, "_H": hh})
    log("surface data written")

    # ---- thin parts with explicit weights
    extra = []
    BW = np.zeros((len(V), len(JPOS)), np.float32)
    names = list(JPOS.keys()); idx_of = {nme: i for i, nme in enumerate(names)}
    for v in body.data.vertices:
        for g in v.groups:
            nme = groups.get(g.group)
            if nme in idx_of:
                BW[v.index, idx_of[nme]] = g.weight
    def near_w(p):
        i = int(np.argmin(((V - np.array(p)) ** 2).sum(1)))
        row = BW[i]; tot = row.sum() or 1
        return [(names[j], float(row[j] / tot)) for j in np.nonzero(row)[0]]

    def sheet(name, vs, fs, ws, attrs):
        ob = make_mesh(name, np.array(vs), fs)
        for p in ob.data.polygons:
            p.use_smooth = True
        for vi, wl in enumerate(ws):
            for bone, wt in wl:
                if wt > 1e-4:
                    (ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)).add([vi], float(wt), "ADD")
        full = {k: [0] * len(vs) for k in ("_ZBACK", "_ZBELLY", "_ZEDGE", "_H")}
        full.update(attrs)
        set_attrs(ob, full)
        extra.append(ob)

    lerp = lambda a, b, t: tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
    for sgn in (1, -1):
        n = (lambda b: b) if sgn > 0 else mirror
        M = lambda p: (sgn * p[0], p[1], p[2])
        wrist = M(WRIST)

        def finger(f):
            mid, tip = M(JPOS[f"f{f}bL"]), M(JTAIL[f"f{f}bL"])
            return lambda u: lerp(wrist, mid, u / 0.48) if u < 0.48 else lerp(mid, tip, (u - 0.48) / 0.52)

        def fingerW(f, u):
            wa = 1 - min(1, max(0, (u - 0.33) / 0.3)); wr = (1 - u) ** 4
            return [(n("wing2L"), wr), (n(f"f{f}aL"), (1 - wr) * wa), (n(f"f{f}bL"), (1 - wr) * (1 - wa))]

        vs, fs, ws, mu, mv, mb = [], [], [], [], [], []
        RU, RV = 22, 8
        for fa in range(1, 5):
            fb = fa + 1
            A, B = finger(fa), finger(fb)
            gap = math.dist(A(1), B(1))
            base = len(vs)
            for iu in range(RU + 1):
                u = iu / RU
                for iv in range(RV + 1):
                    v = iv / RV
                    p = lerp(A(u), B(u), v)
                    sc = 0.32 * gap * math.sin(math.pi * v) * u ** 3
                    p = lerp(p, wrist, sc / max(1e-3, math.dist(p, wrist)))
                    vs.append(p)
                    ws.append([(b, w * (1 - v)) for b, w in fingerW(fa, u)] + [(b, w * v) for b, w in fingerW(fb, u)])
                    mu.append(u); mv.append(v); mb.append(abs(2 * v - 1) ** 8)
            for iu in range(RU):
                for iv in range(RV):
                    a = base + iu * (RV + 1) + iv
                    fs.append([a, a + RV + 1, a + RV + 2, a + 1])
        root, elbow, lastTip, flank = M(WING_ROOT), M(ELBOW), M(JTAIL["f5bL"]), M(FLANK)
        arm_c = lambda u: lerp(root, elbow, u / 0.45) if u < 0.45 else lerp(elbow, wrist, (u - 0.45) / 0.55)
        LAST = finger(5)
        def trail(u):
            p = lerp(flank, lastTip, u)
            toward = lerp(elbow, wrist, 0.3)
            return lerp(p, toward, 0.25 * math.sin(math.pi * u) / max(1e-3, math.dist(p, toward)))
        body_c = lambda v: lerp(root, flank, v)
        IU, IV = 20, 12
        base = len(vs)
        for iu in range(IU + 1):
            u = iu / IU
            for iv in range(IV + 1):
                v = iv / IV
                c0, c1, d0, d1 = arm_c(u), trail(u), body_c(v), LAST(v)
                p = tuple((1 - v) * c0[i] + v * c1[i] + (1 - u) * d0[i] + u * d1[i]
                          - ((1 - u) * (1 - v) * root[i] + u * (1 - v) * wrist[i] + (1 - u) * v * flank[i] + u * v * lastTip[i]) for i in range(3))
                armW = [(n("wing1L"), 1)] if u < 0.45 else [(n("wing1L"), max(0, 1 - (u - 0.45) / 0.3)), (n("wing2L"), min(1, (u - 0.45) / 0.3))]
                tW = [(n("shinL"), 0.6 * (1 - u)), (n("thighL"), 0.4 * (1 - u))] + [(b, w * u) for b, w in fingerW(5, 1)]
                ws.append([(b, w * (1 - v) * (1 - u * u)) for b, w in armW] + [(b, w * v * (1 - u * u)) for b, w in tW]
                          + [(b, w * u * u) for b, w in fingerW(5, v)])
                vs.append(p); mu.append(v); mv.append(u); mb.append(max((1 - v) ** 8, u ** 8))
        for iu in range(IU):
            for iv in range(IV):
                a = base + iu * (IV + 1) + iv
                fs.append([a, a + IV + 1, a + IV + 2, a + 1])
        sheet(f"Membrane{'L' if sgn > 0 else 'R'}", vs, fs, ws, {"_PART": [6] * len(vs), "_U": mu, "_V": mv, "_ZBACK": mb})

    # mane: two rows of thin spines leaning back, from behind the skull to the shoulders
    mn = FEAT["mane"]
    vs, fs, ws, mu = [], [], [], []
    zz = mn["from_z"]; k = 0
    while zz > mn["to_z"]:
        St, Nn, Tt, _ = loft_top(zz)
        along = (mn["from_z"] - zz) / (mn["from_z"] - mn["to_z"])
        length = (mn["length"][0] + (mn["length"][1] - mn["length"][0]) * along) * (0.75 + 0.5 * ((k * 7919) % 13) / 13)
        for side in (1, -1):
            ox = side * (0.015 + 0.03 * (k % 2))
            base_p = np.array([ox, St[1] + Nn[1] * (St[2] - 0.02), St[0] + Nn[0] * (St[2] - 0.02)])
            d = np.array([side * 0.15, Nn[1] * (1 - mn["lean"]) + Tt[1] * mn["lean"], Nn[0] * (1 - mn["lean"]) + Tt[0] * mn["lean"]])
            d /= np.linalg.norm(d)
            tip = base_p + d * length
            half = 0.03
            r1 = base_p - np.array([0, Tt[1], Tt[0]]) * half; r2 = base_p + np.array([0, Tt[1], Tt[0]]) * half
            w = near_w(base_p)
            b0 = len(vs); vs += [tuple(r1), tuple(r2), tuple(tip)]; ws += [w, w, w]; mu += [0, 0, 1]; fs.append([b0, b0 + 1, b0 + 2])
        zz -= mn["spacing"]; k += 1
    sheet("Mane", vs, fs, ws, {"_PART": [7] * len(vs), "_U": mu, "_V": [0] * len(vs)})

    # ear frills (ribbed fins), ridged horns and eyes, on the head bone
    vs, fs, ws, pu, pv, pp = [], [], [], [], [], []
    head_w = [("head", 1.0)]
    for sgn in (1, -1):
        o = [np.array([sgn * p[0], p[1], p[2]]) for p in FEAT["ear_frill"]["outline"]]
        # a small fan from the base edge (o0-o1) to the outer edge (o2-o3)
        b0 = len(vs)
        G = 6
        for i in range(G + 1):
            for j in range(G + 1):
                a, b = i / G, j / G
                p = (1 - a) * ((1 - b) * o[1] + b * o[0]) + a * ((1 - b) * o[2] + b * o[3])
                vs.append(tuple(p)); ws.append(head_w); pu.append(a); pv.append(b); pp.append(9)
        for i in range(G):
            for j in range(G):
                a = b0 + i * (G + 1) + j
                fs.append([a, a + G + 1, a + G + 2, a + 1])
        hn = FEAT["horn"]
        pts = [np.array([sgn * p[0], p[1], p[2]]) for p in hn["path"]]
        SEG, RAD = 28, 12
        q = lambda tt: (1 - tt) ** 2 * pts[0] + 2 * (1 - tt) * tt * pts[1] + tt * tt * pts[2]
        b0 = len(vs)
        total_len = sum(np.linalg.norm(q((i + 1) / 40) - q(i / 40)) for i in range(40))
        for i in range(SEG + 1):
            t = i / SEG
            c0 = q(t); tan = q(min(1, t + 0.02)) - q(max(0, t - 0.02)); tan /= np.linalg.norm(tan)
            sv = np.cross(tan, [1, 0, 0]); sv /= np.linalg.norm(sv); uv = np.cross(sv, tan)
            r = hn["radius"][0] + (hn["radius"][1] - hn["radius"][0]) * t * 2 if t < 0.5 else hn["radius"][1] + (hn["radius"][2] - hn["radius"][1]) * (t - 0.5) * 2
            ring = 1 + 0.12 * (math.cos(2 * math.pi * t * total_len / hn["ring_every"]) > 0.6)
            for kk in range(RAD):
                ang = kk / RAD * 2 * math.pi
                vs.append(tuple(c0 + (sv * math.cos(ang) + uv * math.sin(ang)) * r * ring)); ws.append(head_w); pu.append(t); pv.append(ring - 1); pp.append(8)
        for i in range(SEG):
            for kk in range(RAD):
                a = b0 + i * RAD + kk; b = b0 + i * RAD + (kk + 1) % RAD
                fs.append([a, b, b + RAD, a + RAD])
        # eye: a sphere in its socket; _U/_V hold the direction from its centre for the iris
        e = FEAT["eye"]; ec = np.array([sgn * e["centre"][0], e["centre"][1], e["centre"][2]])
        look = np.array([sgn * 0.85, 0.05, 0.5]); look /= np.linalg.norm(look)
        b0 = len(vs); LAT, LON = 10, 16
        for i in range(LAT + 1):
            for j in range(LON):
                th_, ph = math.pi * i / LAT, 2 * math.pi * j / LON
                d = np.array([math.sin(th_) * math.cos(ph), math.cos(th_), math.sin(th_) * math.sin(ph)])
                vs.append(tuple(ec + d * e["radius"])); ws.append(head_w); pu.append(float(d @ look)); pv.append(0); pp.append(10)
        for i in range(LAT):
            for j in range(LON):
                a = b0 + i * LON + j; b = b0 + i * LON + (j + 1) % LON
                fs.append([a, b, b + LON, a + LON])
    sheet("HeadParts", vs, fs, ws, {"_PART": pp, "_U": pu, "_V": pv})

    activate(body, extra)
    bpy.ops.object.join()
    log(f"joined: {len(body.data.vertices)} verts, {len(body.data.polygons)} faces")
    activate(body, [arm])
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True,
                              export_attributes=True, export_yup=True, export_apply=False, export_animations=False,
                              export_materials="NONE")
    log(f"exported {OUT}")


main()
