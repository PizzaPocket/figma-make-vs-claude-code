"""Clay's skin as one surface over his skeleton and muscles.

The body is built from the inside out (see body_design.json "anatomy" and the creature-sculpting skill):
- the trunk (neck, torso, tail): a sweep of measured cross-sections along the spine;
- bones: tapered capsules (humerus, forearm, femur, shin, the points of the elbow and heel);
- muscles: ellipsoid bellies laid from origin to insertion (shoulder cap, triceps, pectoral, gluteals,
  hamstrings, caudofemoralis...).
Each is a signed distance field; they are joined with a smooth minimum, so the shoulders grow out of
the chest and back and the haunches out of the hips and tail, and the skin is the zero surface of the
union, meshed with marching cubes.
"""
import math

import numpy as np
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes


def norm(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-12)


def smin(a, b, k):
    """Polynomial smooth minimum: the union of two fields, filleted over a radius of about k."""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Piece:
    """A bone (tapered capsule) or a muscle (ellipsoid belly from origin to insertion), on the left side
    (sgn +1) or mirrored to the right (sgn -1)."""

    def __init__(self, spec, sgn, kind):
        m = np.array([sgn, 1.0, 1.0])
        self.name, self.kind, self.k = spec["name"], kind, spec["k"]
        self.a, self.b = np.array(spec["from"]) * m, np.array(spec["to"]) * m
        self.rig = {f"{bn}.{'L' if sgn > 0 else 'R'}" if bn in LIMB_BONES else bn: w for bn, w in spec["rig"].items()}
        self.zone = spec.get("zone", 0.5 if kind == "bone" else None)  # bones near the skin show orange
        ax = norm(self.b - self.a)
        if kind == "bone":
            self.r = spec["r"]
        else:
            hint = np.array(spec.get("hint", [1.0, 0, 0])) * m
            e_out = norm(hint - ax * (hint @ ax))
            self.E = np.array([ax, e_out, np.cross(ax, e_out)])
            self.radii = np.array([np.linalg.norm(self.b - self.a) / 2, spec["radii"][0], spec["radii"][1]])
            self.c = (self.a + self.b) / 2
        self.ax, self.len = ax, np.linalg.norm(self.b - self.a)

    def sdf(self, X):
        if self.kind == "bone":
            ba = self.b - self.a
            h = np.clip(((X - self.a) @ ba) / (ba @ ba), 0.0, 1.0)
            r = self.r[0] + (self.r[1] - self.r[0]) * h
            return np.linalg.norm(X - self.a - h[:, None] * ba, axis=1) - r
        q = (X - self.c) @ self.E.T  # ellipsoid (approximate distance, exact on the surface)
        k0 = np.linalg.norm(q / self.radii, axis=1)
        k1 = np.linalg.norm(q / self.radii ** 2, axis=1)
        return k0 * (k0 - 1) / np.maximum(k1, 1e-9)

    def zone_at(self, X):
        """Its colour zone at points X: a number, or None (the trunk's zone there)."""
        return None if self.zone is None else np.full(len(X), float(self.zone))

    def along(self, X):
        return (X - self.a) @ self.ax


LIMB_BONES = {"upperarm", "forearm", "hand", "thigh", "shin", "foot"}


class Trunk:
    """The neck, torso and tail as a field: the distance from each point to the cross-section of the
    nearest spine station, with the sections given as outlines round the spine (section(i, th))."""

    def __init__(self, s_all, P, N, Bv, section, nphi=144):
        self.s, self.P, self.N, self.Bv = s_all, P, N, Bv
        self.T = np.gradient(P, axis=0); self.T /= np.linalg.norm(self.T, axis=1)[:, None]
        self.tree = cKDTree(P)
        self.phi = np.linspace(-math.pi, math.pi, nphi, endpoint=False)
        R = np.zeros((len(P), nphi))
        th = np.linspace(0, 2 * math.pi, 360, endpoint=False)
        for i in range(len(P)):
            vw = np.array([section(i, t) for t in th])  # (v dorsal, w left)
            ang = np.arctan2(vw[:, 1], vw[:, 0]); rad = np.hypot(vw[:, 0], vw[:, 1])
            o = np.argsort(ang)
            R[i] = np.interp(self.phi, ang[o], rad[o], period=2 * math.pi)
        self.R = R

    def local(self, X):
        _, idx = self.tree.query(X)
        d = X - self.P[idx]
        v = np.einsum("ij,ij->i", d, self.N[idx]); w = np.einsum("ij,ij->i", d, self.Bv[idx]); t = np.einsum("ij,ij->i", d, self.T[idx])
        return idx, v, w, t

    def sdf(self, X):
        idx, v, w, t = self.local(X)
        phi = np.arctan2(w, v)
        j = (phi + math.pi) / (2 * math.pi) * len(self.phi)
        j0 = np.floor(j).astype(int) % len(self.phi); j1 = (j0 + 1) % len(self.phi); f = j - np.floor(j)
        R = self.R[idx, j0] * (1 - f) + self.R[idx, j1] * f
        d = np.hypot(v, w) - R
        d = np.where(idx == 0, np.maximum(d, -t), d)
        d = np.where(idx == len(self.P) - 1, np.maximum(d, t), d)
        return d


def pieces(anat):
    out = []
    for sgn in (1, -1):
        out += [Piece(b, sgn, "bone") for b in anat["bones"]]
        out += [Piece(m, sgn, "muscle") for m in anat["muscles"]]
    return out


def field(X, trunk, parts, all_parts=False):
    """The body's field at points X: the trunk joined smoothly with every bone and muscle."""
    dt = trunk.sdf(X)
    D = [p.sdf(X) for p in parts]
    d = dt.copy()
    for p, dp in zip(parts, D):
        d = smin(d, dp, p.k)
    return (d, dt, np.array(D)) if all_parts else d


def normals(V, F):
    """Area-weighted vertex normals."""
    N = np.zeros_like(V)
    fn = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    return N / np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]


def smooth_on_mesh(V, F, X, iters=8):
    """Average a per-vertex value with its neighbours on the mesh, a few times: closes pinholes and
    smooths the edges of a colour region."""
    F = np.asarray(F); X = np.asarray(X, float).copy()
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = np.vstack([E, E[:, ::-1]])
    deg = np.bincount(E[:, 0], minlength=len(V)).astype(float)
    for _ in range(iters):
        acc = np.bincount(E[:, 0], weights=X[E[:, 1]], minlength=len(V))
        X = 0.5 * X + 0.5 * acc / np.maximum(deg, 1)
    return X


def smooth_normals(V, F, iters=3):
    """The mesh's normals averaged with their neighbours': smooth, and defined even at points that
    only touch slivers of triangles with no area."""
    N = normals(V, F)
    N = np.stack([smooth_on_mesh(V, F, N[:, k], iters) for k in range(3)], 1)
    return N / np.maximum(np.linalg.norm(N, axis=1), 1e-12)[:, None]


def shell(V, F, Z, sh, N, level=0.25):
    """The dark shell: the skin's dark region (zone below `level`) raised as one smooth layer, with a
    rolled rim running round its whole edge. d is each vertex's distance in from the edge (the zone's
    level line, found on the skin's edges); the height rises from 0 at the edge (its foot, rounded),
    over the rim, and settles to the shell's thickness. Returns verts, faces, the source vertex of
    each, and d. N: the skin's outward normals."""
    Z = np.asarray(Z); F = np.asarray(F)
    inside = Z < level
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = E[inside[E[:, 0]] != inside[E[:, 1]]]
    t = ((level - Z[E[:, 0]]) / (Z[E[:, 1]] - Z[E[:, 0]]))[:, None]
    edge = V[E[:, 0]] + (V[E[:, 1]] - V[E[:, 0]]) * t
    d = np.where(inside, cKDTree(edge).query(V)[0], 0.0)
    keep = inside[F].any(axis=1)
    used = np.unique(F[keep]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    foot = np.sqrt(np.clip(d / sh["foot"], 0.0, 1.0))
    rim = sh["rim_height"] * np.sin(math.pi * np.clip(d / sh["rim_width"], 0.0, 1.0)) ** 0.8
    h = (sh["thickness"] + rim) * foot
    S = V[used] + N[used] * h[used, None]
    return S, remap[F[keep]], used, d[used]


def mesh(trunk, parts, h, pad=0.06):
    """Marching cubes over the body's bounding box at spacing h. Returns verts (N, 3) and faces."""
    pts = [trunk.P - trunk.R.max(axis=1)[:, None], trunk.P + trunk.R.max(axis=1)[:, None]]
    for p in parts:
        r = max(p.r) if p.kind == "bone" else p.radii.max()
        pts += [np.minimum(p.a, p.b)[None] - r, np.maximum(p.a, p.b)[None] + r]
    lo = np.min(np.vstack(pts), axis=0) - pad; hi = np.max(np.vstack(pts), axis=0) + pad
    axes = [np.arange(lo[k], hi[k] + h, h) for k in range(3)]
    G = np.zeros(tuple(len(a) for a in axes), np.float32)
    for i, x in enumerate(axes[0]):  # one slab of x at a time
        Y, Z = np.meshgrid(axes[1], axes[2], indexing="ij")
        X = np.stack([np.full(Y.size, x), Y.ravel(), Z.ravel()], 1)
        G[i] = field(X, trunk, parts).reshape(Y.shape)
    v, f, _, _ = marching_cubes(G, 0.0, spacing=(h, h, h), gradient_direction="ascent")
    v = v + lo
    N = normals(v, f)  # wind the faces so their normals point out of the body (the field rises outward)
    probe = field(v[::50] + N[::50] * h * 0.5, trunk, parts) - field(v[::50], trunk, parts)
    if np.mean(probe) < 0:
        f = f[:, ::-1]
    return v, np.ascontiguousarray(f)


def vertex_data(V, trunk, parts, trunk_weights, trunk_zone, dark_zone, tail_trust_s, blend=0.025):
    """Per vertex: rig weights, colour zone, and the pattern coordinates (A along, B round).
    Each part's say is how close it lies to the skin there (within ~blend of the nearest). The dark
    shell (dark_zone: 1 inside it) covers whatever lies under it, trunk or muscle."""
    _, dt, D = field(V, trunk, parts, all_parts=True)
    idx, v, w, _ = trunk.local(V)
    s = trunk.s[idx]
    f = (1 - v / np.maximum(np.hypot(v, w), 1e-9)) / 2  # 0 along the top of the spine, 1 underneath
    allD = np.vstack([dt[None], D])
    infl = np.exp(-(allD - allD.min(axis=0)) / blend)
    infl /= infl.sum(axis=0)
    AL = [p.along(V) for p in parts]
    ZP = [p.zone_at(V) for p in parts]
    W, Z, A = [], [], []
    for n in range(len(V)):
        sc = max(float(s[n]), 0.0)
        zt = trunk_zone(sc, float(f[n]), V[n, 2], V[n, 1])
        acc = {}
        for bn, wt in trunk_weights(sc):
            acc[bn] = acc.get(bn, 0.0) + infl[0, n] * wt
        z = infl[0, n] * zt
        a = infl[0, n] * sc
        for k, p in enumerate(parts):
            ik = infl[k + 1, n]
            if ik < 1e-3:
                continue
            for bn, wt in p.rig.items():
                acc[bn] = acc.get(bn, 0.0) + ik * wt
            z += ik * (zt if ZP[k] is None else ZP[k][n])
            a += ik * (10 + AL[k][n])
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(wt for _, wt in top)
        # the tail's dark-top rule holds only on the tail itself: a limb lying near the tail (the forearm
        # beside its tip) is not part of it
        dk = dark_zone(sc, float(f[n]), V[n, 2], V[n, 1]) if (sc < tail_trust_s or dt[n] < 0.04) else 0.0
        W.append([(bn, wt / tot) for bn, wt in top]); Z.append(z * (1 - dk)); A.append(a)
    return W, Z, A, list(f)
