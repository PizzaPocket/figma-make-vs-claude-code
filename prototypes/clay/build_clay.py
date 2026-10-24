"""Build a rigged Clay (.glb) with Blender, shaped and posed from the side-view reference.

Model space: x = Clay's left, y = up, z = forward (glTF axes). Units: 1 = 343 px
of the 1400 px-wide reference, measured with the ground at y = 830 px and z = 0 at x = 700 px.
The bind pose is the reference pose (wings folded and raised), so the reference art
lines up with the model and can be projected onto it.
"""
import math
import sys
import time

import bpy  # bmesh is only importable once bpy is loaded
import bmesh
import numpy as np
from PIL import Image
from skimage import measure

OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "clay.glb"
REF = sys.argv[sys.argv.index("--ref") + 1] if "--ref" in sys.argv else "ref1400.png"
CELL = 0.012
BLEND = 0.05
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:6.1f}s] {msg}", flush=True)


def ref_to_model(px, py):
    return (700 - px) / 343.0, (830 - py) / 343.0  # z, y


# ---------------------------------------------------------------- measurements
# Centre-line stations from nose to tail tip: z, y, half-height above, below, half-width, squareness.
# Head values come from scanning the reference outline column by column.
STATIONS = [
    (2.02, 1.42, 0.045, 0.045, 0.05, 2.2),
    (1.988, 1.42, 0.067, 0.067, 0.075, 2.4),
    (1.953, 1.417, 0.099, 0.099, 0.09, 2.5),
    (1.918, 1.435, 0.14, 0.14, 0.10, 2.5),
    (1.883, 1.462, 0.19, 0.18, 0.11, 2.5),
    (1.848, 1.48, 0.235, 0.235, 0.12, 2.5),
    (1.813, 1.483, 0.264, 0.264, 0.13, 2.5),
    (1.778, 1.489, 0.282, 0.282, 0.14, 2.4),
    (1.743, 1.527, 0.307, 0.307, 0.15, 2.4),
    (1.708, 1.55, 0.31, 0.31, 0.165, 2.4),
    (1.673, 1.573, 0.308, 0.308, 0.18, 2.3),
    (1.638, 1.61, 0.28, 0.28, 0.195, 2.3),
    (1.569, 1.64, 0.25, 0.25, 0.22, 2.2),
    (1.47, 1.63, 0.255, 0.255, 0.235, 2.1),
    (1.36, 1.57, 0.27, 0.27, 0.255, 2.0),  # back of the skull into the neck
    (1.25, 1.46, 0.29, 0.29, 0.28, 2.0),
    (1.13, 1.33, 0.33, 0.33, 0.32, 2.0),
    (0.98, 1.18, 0.42, 0.42, 0.39, 2.0),
    (0.80, 1.10, 0.56, 0.55, 0.43, 2.1),  # deep chest
    (0.58, 1.045, 0.525, 0.525, 0.47, 2.1),
    (0.29, 1.02, 0.51, 0.51, 0.48, 2.1),
    (0.00, 1.055, 0.435, 0.435, 0.46, 2.1),
    (-0.29, 1.065, 0.365, 0.365, 0.43, 2.1),
    (-0.58, 1.08, 0.29, 0.29, 0.40, 2.0),  # waist
    (-0.87, 1.055, 0.29, 0.28, 0.41, 2.0),  # hips
    (-1.17, 1.015, 0.25, 0.235, 0.35, 2.0),
    (-1.50, 0.95, 0.21, 0.21, 0.22, 2.0),  # tail
    (-1.90, 0.82, 0.17, 0.17, 0.175, 2.0),
    (-2.40, 0.62, 0.13, 0.13, 0.135, 2.0),
    (-2.90, 0.45, 0.10, 0.10, 0.10, 2.0),
    (-3.40, 0.32, 0.07, 0.07, 0.07, 2.0),
    (-3.90, 0.22, 0.045, 0.045, 0.045, 2.0),
    (-4.30, 0.16, 0.02, 0.02, 0.02, 2.0),
]
# Colour zones (for areas the reference doesn't show): height in the cross-section
# above which the hide is dark, and below which it is cream.
ZONES = [(0.55, -0.35)] * 14 + [(0.55, -0.15), (0.5, -0.2), (0.45, -0.25), (0.35, -0.3), (0.2, -0.55),
                                (0.15, -0.65), (0.15, -0.65), (0.15, -0.65), (0.1, -0.6), (0.05, -0.55),
                                (0.0, -0.5), (0.0, -0.45)] + [(0.0, -0.35)] * 7

# Skeleton joints (rest pose = reference pose).
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

# Left-side joints; the right side mirrors x.
WING_ROOT = (0.30, 1.30, 0.62)
ELBOW = (0.62, *reversed(ref_to_model(800, 430)))   # (x, y, z)
WRIST = (0.72, *reversed(ref_to_model(745, 775)))
FINGER_TIPS = [ref_to_model(1380, 15), ref_to_model(1275, 15), ref_to_model(1155, 45), ref_to_model(1035, 85), ref_to_model(915, 185)]
FINGER_TIPS = [(0.86, y, z) for z, y in FINGER_TIPS]
SIDE = {
    "upperArmL": ((0.34, 0.95, 0.78), "chest"), "foreArmL": ((0.40, 0.50, 0.62), "upperArmL"), "handL": ((0.38, 0.14, 0.78), "foreArmL"),
    "thighL": ((0.36, 0.95, -0.85), "hips"), "shinL": ((0.46, 0.55, -0.55), "thighL"), "metaL": ((0.45, 0.26, -1.00), "shinL"),
    "footL": ((0.45, 0.08, -0.86), "metaL"),
    "wing1L": (WING_ROOT, "chest"), "wing2L": (ELBOW, "wing1L"),
}
SIDE_TAILS = {"upperArmL": "foreArmL", "foreArmL": "handL", "handL": (0.38, 0.04, 1.02), "thighL": "shinL", "shinL": "metaL",
              "metaL": "footL", "footL": (0.45, 0.04, -0.60), "wing1L": "wing2L", "wing2L": WRIST}
for f, tip in enumerate(FINGER_TIPS, 1):
    mid = tuple(WRIST[i] + (tip[i] - WRIST[i]) * 0.48 + (0.04 if i == 0 else 0) for i in range(3))
    SIDE[f"f{f}aL"] = (WRIST, "wing2L"); SIDE[f"f{f}bL"] = (mid, f"f{f}aL")
    SIDE_TAILS[f"f{f}aL"] = f"f{f}bL"; SIDE_TAILS[f"f{f}bL"] = tip
# the inner membrane runs from the last finger down to the hind leg, near the ankle
FLANK = (0.64, 0.42, -1.00)


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
            if isinstance(t, str):
                tail[nn] = pos[t if s > 0 else mirror(t)]
            else:
                tail[nn] = (s * t[0], t[1], t[2])
    return pos, par, tail


JPOS, JPAR, JTAIL = joints()


# ---------------------------------------------------------------- loft
def build_loft():
    P = np.array(STATIONS, float)
    Z = np.array(ZONES, float)
    out = []
    SUB = 6
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(0, i - 1)], P[i], P[i + 1], P[min(len(P) - 1, i + 2)]
        for k in range(SUB):
            t = k / SUB
            cr = lambda a, b, c, d: 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
            out.append([cr(p0[0], p1[0], p2[0], p3[0]), cr(p0[1], p1[1], p2[1], p3[1]), *(p1[2:] + (p2[2:] - p1[2:]) * t), *(Z[i] + (Z[i + 1] - Z[i]) * t)])
    out.append([*P[-1], *Z[-1]])
    L = np.array(out)  # z, y, top, bot, w, e, back, belly
    d = np.diff(L[:, :2], axis=0)
    s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
    tang = np.zeros((len(L), 2))
    tang[1:-1] = L[2:, :2] - L[:-2, :2]; tang[0] = L[1, :2] - L[0, :2]; tang[-1] = L[-1, :2] - L[-2, :2]
    tang /= np.linalg.norm(tang, axis=1, keepdims=True)
    nrm = np.stack([tang[:, 1], -tang[:, 0]], 1)  # (nz, ny): toward the back
    return L, s, tang, nrm


LOFT, LOFT_S, LOFT_T, LOFT_N = build_loft()


def loft_query(x, y, z, want=False):
    """Vectorised approximate distance to the loft for points (x, y, z) arrays."""
    best = np.full(x.shape, np.inf)
    bs = np.zeros(x.shape); bh = np.zeros(x.shape); bi = np.zeros(x.shape, int)
    for i in range(len(LOFT) - 1):
        A, B = LOFT[i], LOFT[i + 1]
        m = (y > min(A[1], B[1]) - 0.75) & (y < max(A[1], B[1]) + 0.75) & (z > min(A[0], B[0]) - 0.75) & (z < max(A[0], B[0]) + 0.75)
        if not m.any():
            continue
        xs, ys, zs = x[m], y[m], z[m]
        dz, dy = B[0] - A[0], B[1] - A[1]
        l2 = dz * dz + dy * dy
        t = ((zs - A[0]) * dz + (ys - A[1]) * dy) / l2
        tc = np.clip(t, 0, 1)
        cz, cy = A[0] + dz * tc, A[1] + dy * tc
        nz = LOFT_N[i, 0] + (LOFT_N[i + 1, 0] - LOFT_N[i, 0]) * tc
        ny = LOFT_N[i, 1] + (LOFT_N[i + 1, 1] - LOFT_N[i, 1]) * tc
        nl = np.hypot(nz, ny)
        tz = LOFT_T[i, 0] + (LOFT_T[i + 1, 0] - LOFT_T[i, 0]) * tc
        ty = LOFT_T[i, 1] + (LOFT_T[i + 1, 1] - LOFT_T[i, 1]) * tc
        tl = np.hypot(tz, ty)
        qn = ((zs - cz) * nz + (ys - cy) * ny) / nl
        qt = ((zs - cz) * tz + (ys - cy) * ty) / tl
        w = A[4] + (B[4] - A[4]) * tc
        e = A[5] + (B[5] - A[5]) * tc
        a = np.where(qn >= 0, A[2] + (B[2] - A[2]) * tc, A[3] + (B[3] - A[3]) * tc)
        r = (np.abs(xs / w) ** e + np.abs(qn / a) ** e) ** (1 / e)
        d = (r - 1) * np.minimum(w, a)
        out = (t < 0) | (t > 1)
        d = np.where(out, np.where(d > 0, np.hypot(d, qt), np.maximum(d, np.abs(qt))), d)
        cur = best[m]
        better = d < cur
        idx = np.where(m)[0][better]
        best[idx] = d[better]
        if want:
            bs[idx] = (LOFT_S[i] + (LOFT_S[i + 1] - LOFT_S[i]) * tc)[better]
            bh[idx] = (qn / a)[better]
            bi[idx] = i
    return (best, bs, bh, bi) if want else best


# ---------------------------------------------------------------- other shapes
def shapes():
    S = []
    def cone(bone, a, ra, b, rb, group="limb"): S.append(dict(t="cone", bone=bone, a=np.array(a, float), ra=ra, b=np.array(b, float), rb=rb, group=group))
    def ell(bone, c, r, group="body"): S.append(dict(t="ell", bone=bone, c=np.array(c, float), r=np.array(r, float), group=group))
    def box(bone, c, h, r, group="limb"): S.append(dict(t="box", bone=bone, c=np.array(c, float), h=np.array(h, float), r=r, group=group))
    for s in (1, -1):
        n = (lambda b: b) if s > 0 else mirror
        X = lambda v: s * v
        P = lambda p: (s * p[0], p[1], p[2])
        ell(n("upperArmL"), (X(0.35), 0.84, 0.76), (0.17, 0.25, 0.22), "limb")
        cone(n("upperArmL"), (X(0.34), 0.95, 0.78), 0.17, (X(0.40), 0.50, 0.62), 0.115)
        cone(n("foreArmL"), (X(0.40), 0.50, 0.62), 0.11, (X(0.38), 0.14, 0.78), 0.075)
        box(n("handL"), (X(0.38), 0.07, 0.89), (0.10, 0.03, 0.11), 0.04)
        for dx in (-0.085, 0, 0.085):
            cone(n("handL"), (X(0.38 + dx * 0.6), 0.07, 0.93), 0.045, (X(0.38 + dx * 1.1), 0.045, 1.07), 0.034)
            cone(n("handL"), (X(0.38 + dx * 1.1), 0.045, 1.07), 0.032, (X(0.38 + dx * 1.15), 0.0, 1.16), 0.006, "claw")
        cone(n("handL"), (X(0.43), 0.13, 0.80), 0.03, (X(0.47), 0.04, 0.84), 0.005, "claw")
        ell(n("thighL"), (X(0.39), 0.80, -0.72), (0.20, 0.31, 0.30), "limb")
        cone(n("thighL"), (X(0.36), 0.95, -0.85), 0.21, (X(0.46), 0.55, -0.55), 0.135)
        cone(n("shinL"), (X(0.46), 0.55, -0.55), 0.12, (X(0.45), 0.26, -1.00), 0.078)
        cone(n("metaL"), (X(0.45), 0.26, -1.00), 0.078, (X(0.45), 0.08, -0.86), 0.07)
        box(n("footL"), (X(0.45), 0.07, -0.76), (0.11, 0.035, 0.12), 0.045)
        for dx in (-0.095, 0, 0.095):
            cone(n("footL"), (X(0.45 + dx * 0.5), 0.07, -0.70), 0.05, (X(0.45 + dx), 0.05, -0.55), 0.04)
            cone(n("footL"), (X(0.45 + dx), 0.05, -0.55), 0.036, (X(0.45 + dx * 1.05), 0.0, -0.45), 0.006, "claw")
        # folded wing arm and fingers (rest pose)
        ell(n("wing1L"), P((0.30, 1.30, 0.58)), (0.14, 0.12, 0.2), "wing")
        cone(n("wing1L"), P(WING_ROOT), 0.11, P(ELBOW), 0.085, "wing")
        cone(n("wing2L"), P(ELBOW), 0.075, P(WRIST), 0.05, "wing")
        cone(n("wing2L"), P(WRIST), 0.045, P((WRIST[0] + 0.02, WRIST[1] - 0.03, WRIST[2] + 0.17)), 0.007, "claw")
        for f in range(1, 6):
            mid = JPOS[f"f{f}bL"]; tip = JTAIL[f"f{f}bL"]
            cone(n(f"f{f}aL"), P(WRIST), 0.035, P(mid), 0.036, "wing")
            cone(n(f"f{f}bL"), P(mid), 0.04, P(tip), 0.026, "wing")
            d = np.array(tip) - np.array(mid); d /= np.linalg.norm(d)
            cone(n(f"f{f}bL"), P(tip), 0.024, P(tuple(np.array(tip) + d * 0.1 + np.array([0, -0.0, -0.06]))), 0.004, "claw")
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
        c, h = s["c"], s["h"]
        q = np.stack([np.abs(x - c[0]) - h[0], np.abs(y - c[1]) - h[1], np.abs(z - c[2]) - h[2]])
        return np.linalg.norm(np.maximum(q, 0), axis=0) + np.minimum(q.max(0), 0) - s["r"]
    a, b, ra, rb = s["a"], s["b"], s["ra"], s["rb"]
    ba = b - a
    l2 = ba @ ba
    rr = ra - rb
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = np.stack([x - a[0], y - a[1], z - a[2]])
    yy = (pa * ba[:, None]).sum(0)
    zz = yy - l2
    q = pa * l2 - ba[:, None] * yy
    x2 = (q * q).sum(0)
    y2 = yy * yy * l2
    z2 = zz * zz * l2
    k = np.sign(rr) * rr * rr * x2
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + yy * rr) * il2 - ra
    d1 = np.sqrt(x2 + z2) * il2 - rb
    d2 = np.sqrt(x2 + y2) * il2 - ra
    return np.where(np.sign(zz) * a2 * z2 > k, d1, np.where(np.sign(yy) * a2 * y2 < k, d2, d3))


def prim_bounds(s):
    if s["t"] == "cone":
        r = max(s["ra"], s["rb"])
        return np.minimum(s["a"], s["b"]) - r, np.maximum(s["a"], s["b"]) + r
    e = s["r"] if s["t"] == "ell" else s["h"] + s["r"]
    return s["c"] - e, s["c"] + e


# ---------------------------------------------------------------- field and surface
def build_surface():
    S = shapes()
    lo = np.array([-1.0, -0.03, -4.40]); hi = np.array([1.0, 2.45, 2.12])
    n = np.ceil((hi - lo) / CELL).astype(int) + 1
    log(f"grid {n} = {n.prod() / 1e6:.1f}M cells")
    xs = lo[0] + np.arange(n[0]) * CELL; ys = lo[1] + np.arange(n[1]) * CELL; zs = lo[2] + np.arange(n[2]) * CELL
    body = np.zeros(n[::-1], np.float32)   # [k, j, i] = z, y, x
    wing = np.zeros(n[::-1], np.float32)
    margin = 6 * BLEND

    # loft, in slabs along z
    ii = np.where(np.abs(xs) < 0.7)[0]
    dl = np.full((n[2], n[1], len(ii)), 1.0, np.float32)
    for k0 in range(0, n[2], 40):
        k1 = min(n[2], k0 + 40)
        Zg, Yg, Xg = np.meshgrid(zs[k0:k1], ys, xs[ii], indexing="ij")
        dl[k0:k1] = np.minimum(loft_query(Xg.ravel(), Yg.ravel(), Zg.ravel()).reshape(Zg.shape), 1.0)
    # the loft is a minimum over short segments, which leaves faint creases where
    # neighbouring segments meet; a light blur of the distance field removes them
    from scipy.ndimage import gaussian_filter
    dl = gaussian_filter(dl, sigma=1.6)
    body[:, :, ii[0]:ii[-1] + 1] += np.where(dl < margin, np.exp(-np.clip(dl, -1, margin) / BLEND), 0).astype(np.float32)
    del dl
    log("loft done")
    for s in S:
        blo, bhi = prim_bounds(s)
        i0, j0, k0 = np.maximum(0, np.floor((blo - margin - lo) / CELL).astype(int))
        i1, j1, k1 = np.minimum(n - 1, np.ceil((bhi + margin - lo) / CELL).astype(int))
        Zg, Yg, Xg = np.meshgrid(zs[k0:k1 + 1], ys[j0:j1 + 1], xs[i0:i1 + 1], indexing="ij")
        d = sd_prim(s, Xg, Yg, Zg)
        target = wing if s["group"] == "wing" or (s["group"] == "claw" and s["bone"].startswith(("wing", "f"))) else body
        target[k0:k1 + 1, j0:j1 + 1, i0:i1 + 1] += np.where(d < margin, np.exp(-np.clip(d, -1, margin) / BLEND), 0).astype(np.float32)
    log("shapes done")
    fb = np.where(body > 0, -BLEND * np.log(np.maximum(body, 1e-30)), 1.0).astype(np.float32)
    fw = np.where(wing > 0, -BLEND * np.log(np.maximum(wing, 1e-30)), 1.0).astype(np.float32)
    del body, wing
    # Wing arms join the body smoothly only at the shoulder; elsewhere they stay separate
    # (the folded arm lies close to the flank and must not fuse with it).
    Zg, Yg, Xg = np.meshgrid(zs, ys, xs, indexing="ij")
    near_root = np.exp(-(((np.abs(Xg) - WING_ROOT[0]) ** 2 + (Yg - WING_ROOT[1]) ** 2 + (Zg - WING_ROOT[2]) ** 2) / 0.06))
    k = (0.004 + 0.05 * near_root).astype(np.float32)
    del Xg, Yg, Zg, near_root
    m = np.minimum(fb, fw)
    F = m - k * np.log(np.exp(-(fb - m) / k) + np.exp(-(fw - m) / k))
    del fb, fw, k, m
    log("field done; marching cubes")
    verts, faces, _, _ = measure.marching_cubes(F, level=0.0, spacing=(CELL, CELL, CELL))
    verts = verts[:, ::-1] + lo  # back to x, y, z
    log(f"surface: {len(verts)} verts, {len(faces)} faces")
    return verts, faces, S


# ---------------------------------------------------------------- Blender helpers
def to_blender(p):
    """Model (x, y, z) with y up and z forward -> Blender (x, -z, y), so glTF export gives back model axes."""
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


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    verts, faces, S = build_surface()
    body = make_mesh("Clay", verts, faces)

    # keep the largest pieces only (drop stray specks), smooth lightly, decimate
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
    islands.sort(key=len, reverse=True)
    drop = [v for isl in islands if len(isl) < 200 for v in isl]
    bmesh.ops.delete(bm, geom=drop, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.update_edit_mesh(body.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    log(f"islands kept: {sum(1 for i in islands if len(i) >= 200)}")
    sm = body.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); sm.iterations = 10; sm.smooth_type = "LENGTH_WEIGHTED"
    sm.use_only_smooth = True
    dec = body.modifiers.new("decimate", "DECIMATE"); dec.ratio = min(1.0, 60000 / len(body.data.vertices))
    bpy.ops.object.modifier_apply(modifier="smooth")
    bpy.ops.object.modifier_apply(modifier="decimate")
    log(f"decimated: {len(body.data.vertices)} verts")
    for p in body.data.polygons:
        p.use_smooth = True

    # ---- armature
    arm_data = bpy.data.armatures.new("ClayRig")
    arm = bpy.data.objects.new("ClayRig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    activate(arm)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for name in JPOS:
        b = arm_data.edit_bones.new(name)
        b.head = to_blender(JPOS[name]).tolist()
        b.tail = to_blender(JTAIL[name]).tolist()
        eb[name] = b
    for name, pr in JPAR.items():
        if pr:
            eb[name].parent = eb[pr]
    bpy.ops.object.mode_set(mode="OBJECT")
    log(f"armature: {len(JPOS)} bones")

    # ---- bone-heat weights for the body
    activate(arm, [body])
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        log("bone heat weights done")
    except Exception as ex:  # noqa
        log(f"bone heat failed: {ex}")
    groups = {g.index: g.name for g in body.vertex_groups}
    nv = len(body.data.vertices)
    log(f"vertex groups: {len(groups)}")

    # per-vertex surface data, measured on the final body mesh
    V = from_blender(np.array([v.co for v in body.data.vertices]))
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    dl, s_along, h_cross, seg = loft_query(x, y, z, want=True)
    dl = np.where(np.abs(x) < 0.75, dl, np.inf)
    gd = {"body": np.minimum(dl, np.inf), "limb": np.full(nv, np.inf), "wing": np.full(nv, np.inf), "claw": np.full(nv, np.inf)}
    for s in S:
        d = sd_prim(s, x, y, z)
        g = s["group"] if s["group"] != "body" else "body"
        gd[g] = np.minimum(gd[g], d)
    order = ["body", "limb", "wing", "claw"]
    part = np.argmin(np.stack([gd[g] for g in order]), 0).astype(np.float32)
    loft_i = np.clip(seg, 0, len(LOFT) - 1)
    back_t, belly_t = LOFT[loft_i, 6], LOFT[loft_i, 7]
    zone_back = np.clip((h_cross - back_t + 0.04) / 0.08, 0, 1)
    zone_belly = np.clip((belly_t + 0.04 - h_cross) / 0.08, 0, 1)
    zone_back = np.where(part == 0, zone_back, np.where(part == 2, 1.0, 0.0))
    zone_belly = np.where(part == 0, zone_belly, 0.0)
    # lower jaw is cream below the mouth line
    jaw = (z > 1.55) & (y < 1.40 + (z - 1.55) * -0.06) & (part == 0)
    zone_belly[jaw] = 1; zone_back[jaw] = 0

    # Keep wing bones from pulling on the body (and the body off the wings), except at the shoulder.
    wing_bones = {i for i, nme in groups.items() if nme.startswith(("wing", "f"))}
    root_d = np.sqrt((np.abs(x) - WING_ROOT[0]) ** 2 + (y - WING_ROOT[1]) ** 2 + (z - WING_ROOT[2]) ** 2)
    for v in body.data.vertices:
        is_wing = part[v.index] == 2 or (part[v.index] == 3 and min((gd["wing"][v.index], 9)) < 0.08)
        near = root_d[v.index] < 0.3
        for g in list(v.groups):
            if near:
                continue
            if (g.group in wing_bones) != is_wing:
                g.weight = 0.0
    log("weights separated between wings and body")

    # ---- thin parts as separate objects with explicit weights, joined afterwards
    extra_objs = []

    def sheet(name, verts_, faces_, weights_, attrs):
        ob = make_mesh(name, np.array(verts_), faces_)
        for p in ob.data.polygons:
            p.use_smooth = True
        for vi, wl in enumerate(weights_):
            for bone, wt in wl:
                if wt <= 1e-4:
                    continue
                g = ob.vertex_groups.get(bone) or ob.vertex_groups.new(name=bone)
                g.add([vi], float(wt), "ADD")
        for an, vals in attrs.items():
            a = ob.data.attributes.new(an, "FLOAT", "POINT")
            a.data.foreach_set("value", np.asarray(vals, np.float32))
        extra_objs.append(ob)

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
                    dl_ = max(1e-3, math.dist(p, wrist))
                    p = lerp(p, wrist, sc / dl_)
                    vs.append(p)
                    ws.append([(b, w * (1 - v)) for b, w in fingerW(fa, u)] + [(b, w * v) for b, w in fingerW(fb, u)])
                    mu.append(u); mv.append(v); mb.append(abs(2 * v - 1) ** 8)
            for iu in range(RU):
                for iv in range(RV):
                    a = base + iu * (RV + 1) + iv
                    fs.append([a, a + RV + 1, a + RV + 2, a + 1])
        # inner panel: arm, last finger, trailing edge to the flank, body line (Coons patch)
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
        sheet(f"Membrane{'L' if sgn > 0 else 'R'}", vs, fs, ws, {"_PART": [5] * len(vs), "_U": mu, "_V": mv, "_ZBACK": mb, "_ZBELLY": [0] * len(vs)})

    # body weights at a point, from the nearest body vertex (so attached sheets ride the skin)
    BW = np.zeros((nv, len(JPOS)), np.float32)
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

    # mane: a fringe of thin dark spines from behind the skull to mid-back
    vs, fs, ws = [], [], []
    # arc length along the centre line just behind the skull, and at mid-back
    s_head = LOFT_S[int(np.argmin(np.abs(LOFT[:, 0] - 1.30)))]
    s_mid = LOFT_S[int(np.argmin(np.abs(LOFT[:, 0] - JPOS["spine1"][2])))]
    k = 0
    sv = s_head + 0.02
    while sv < s_mid + 0.1:
        i = int(np.clip(np.searchsorted(LOFT_S, sv) - 1, 0, len(LOFT) - 2))
        t = (sv - LOFT_S[i]) / (LOFT_S[i + 1] - LOFT_S[i])
        St = LOFT[i] + (LOFT[i + 1] - LOFT[i]) * t
        nz, ny = LOFT_N[i]; tz, ty = LOFT_T[i]
        along = (sv - s_head) / (s_mid + 0.1 - s_head)
        length = (0.42 - 0.24 * along) * (0.75 + 0.5 * ((k * 7919) % 13) / 13)
        for side in (1, -1):
            ox = side * (0.02 + 0.03 * (k % 2))
            base_p = (ox, St[1] + ny * (St[2] - 0.05), St[0] + nz * (St[2] - 0.05))
            d = np.array([side * 0.12, ny * 0.6 + ty * 0.8, nz * 0.6 + tz * 0.8]); d /= np.linalg.norm(d)
            tip = tuple(np.array(base_p) + d * length)
            half = 0.032
            r1 = (base_p[0], base_p[1] - ty * half, base_p[2] - tz * half)
            r2 = (base_p[0], base_p[1] + ty * half, base_p[2] + tz * half)
            w = near_w(base_p)
            b0 = len(vs); vs += [r1, r2, tip]; ws += [w, w, w]; fs.append([b0, b0 + 1, b0 + 2])
        sv += 0.035; k += 1
    sheet("Mane", vs, fs, ws, {"_PART": [6] * len(vs), "_U": [0, 0, 1] * (len(vs) // 3), "_V": [0] * len(vs), "_ZBACK": [0] * len(vs), "_ZBELLY": [0] * len(vs)})

    # ear frills and two slim horns per side (head bone only)
    vs, fs, ws, pu, pp = [], [], [], [], []
    head_w = [("head", 1.0)]
    for sgn in (1, -1):
        fr = [(sgn * 0.20, 1.72, 1.41), (sgn * 0.19, 1.60, 1.36), (sgn * 0.27, 1.92, 1.27), (sgn * 0.25, 1.80, 1.30)]
        b0 = len(vs); vs += fr; ws += [head_w] * 4; pu += [0, 0, 1, 0.7]; pp += [7] * 4
        fs += [[b0, b0 + 1, b0 + 3], [b0, b0 + 3, b0 + 2]]
        for pts, r in (([(0.10, 1.86, 1.58), (0.12, 1.98, 1.53), (0.13, 2.04, 1.46)], (0.03, 0.019, 0.005)),
                       ([(0.165, 1.85, 1.44), (0.19, 1.99, 1.31), (0.205, 2.10, 1.21)], (0.034, 0.021, 0.005))):
            SEG, RAD = 10, 10
            q = lambda kk, tt: (1 - tt) ** 2 * pts[0][kk] + 2 * (1 - tt) * tt * pts[1][kk] + tt * tt * pts[2][kk]
            at = lambda tt: np.array([sgn * q(0, tt), q(1, tt), q(2, tt)])
            b0 = len(vs)
            for i in range(SEG + 1):
                t = i / SEG
                c0 = at(t); tan = at(min(1, t + 0.02)) - at(max(0, t - 0.02)); tan /= np.linalg.norm(tan)
                side_v = np.cross(tan, [1, 0, 0]); side_v /= np.linalg.norm(side_v); up_v = np.cross(side_v, tan)
                rr = r[0] + (r[1] - r[0]) * t * 2 if t < 0.5 else r[1] + (r[2] - r[1]) * (t - 0.5) * 2
                for kk in range(RAD):
                    ang = kk / RAD * 2 * math.pi
                    vs.append(tuple(c0 + (side_v * math.cos(ang) + up_v * math.sin(ang)) * rr)); ws.append(head_w); pu.append(t); pp.append(4)
            for i in range(SEG):
                for kk in range(RAD):
                    a = b0 + i * RAD + kk; b = b0 + i * RAD + (kk + 1) % RAD
                    fs.append([a, b, b + RAD, a + RAD])
    sheet("HeadParts", vs, fs, ws, {"_PART": pp, "_U": pu, "_V": [0] * len(vs), "_ZBACK": [0] * len(vs), "_ZBELLY": [0] * len(vs)})

    # body attributes
    for an, vals in {"_PART": part, "_U": s_along, "_V": h_cross, "_ZBACK": zone_back, "_ZBELLY": zone_belly}.items():
        a = body.data.attributes.new(an, "FLOAT", "POINT")
        a.data.foreach_set("value", np.asarray(vals, np.float32))

    # join everything into one skinned mesh
    activate(body, extra_objs)
    bpy.ops.object.join()
    mod = next((m for m in body.modifiers if m.type == "ARMATURE"), None) or body.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    body.parent = arm

    # ---- where the reference shows the surface directly (for projecting the art)
    allV = from_blender(np.array([v.co for v in body.data.vertices]))
    tris = []
    for p in body.data.polygons:
        vv = list(p.vertices)
        for i in range(1, len(vv) - 1):
            tris.append((vv[0], vv[i], vv[i + 1]))
    tris = np.array(tris)
    depth = np.full((1020, 1400), -np.inf, np.float32)
    # splat points sampled on every triangle, keeping the outermost |x| per reference pixel
    bary = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1 / 3, 1 / 3, 1 / 3], [0.5, 0.5, 0], [0, 0.5, 0.5], [0.5, 0, 0.5],
                     [0.66, 0.17, 0.17], [0.17, 0.66, 0.17], [0.17, 0.17, 0.66]])
    pts = (bary[None, :, :, None] * allV[tris][:, None, :, :]).sum(2).reshape(-1, 3)
    px = np.round(700 - pts[:, 2] * 343).astype(int); py = np.round(830 - pts[:, 1] * 343).astype(int)
    ok = (px >= 0) & (px < 1400) & (py >= 0) & (py < 1020)
    ax = np.abs(pts[:, 0])
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            qx, qy = np.clip(px + dx, 0, 1399), np.clip(py + dy, 0, 1019)
            np.maximum.at(depth, (qy[ok], qx[ok]), ax[ok])
    vpx = np.round(700 - allV[:, 2] * 343).astype(int); vpy = np.round(830 - allV[:, 1] * 343).astype(int)
    inside = (vpx >= 0) & (vpx < 1400) & (vpy >= 0) & (vpy < 1020)
    dvis = np.where(inside, depth[np.clip(vpy, 0, 1019), np.clip(vpx, 0, 1399)], np.inf)
    # also require the reference to have Clay there (not background)
    refimg = np.asarray(Image.open(REF).convert("RGB")).max(2) > 40
    onref = np.where(inside, refimg[np.clip(vpy, 0, 1019), np.clip(vpx, 0, 1399)], False)
    vis = ((np.abs(allV[:, 0]) >= dvis - 0.035) & onref).astype(np.float32)
    # soften the edge between projected art and plain colour
    me = body.data
    ei = np.zeros(len(me.edges) * 2, int); me.edges.foreach_get("vertices", ei); ei = ei.reshape(-1, 2)
    for _ in range(3):
        acc = np.zeros_like(vis); cnt = np.zeros_like(vis)
        np.add.at(acc, ei[:, 0], vis[ei[:, 1]]); np.add.at(acc, ei[:, 1], vis[ei[:, 0]])
        np.add.at(cnt, ei[:, 0], 1); np.add.at(cnt, ei[:, 1], 1)
        vis = 0.5 * vis + 0.5 * acc / np.maximum(cnt, 1)
    a = body.data.attributes.new("_PROJ", "FLOAT", "POINT")
    a.data.foreach_set("value", vis)
    log(f"projection-visible vertices: {vis.mean():.0%}")

    # ---- export
    activate(body, [arm])
    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_skins=True,
                              export_attributes=True, export_yup=True, export_apply=False, export_animations=False,
                              export_materials="NONE")
    log(f"exported {OUT}: {len(body.data.vertices)} verts, {len(body.data.polygons)} faces")


main()
