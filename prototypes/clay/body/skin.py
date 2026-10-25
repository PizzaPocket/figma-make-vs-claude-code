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


LIMB_BONES = {"upperarm", "forearm", "hand", "thigh", "shin", "foot", "wing_humerus", "wing_forearm"}


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

    def _segment(self, X):
        """Each point's place along the spine, continuously: the segment it projects onto and how far along it."""
        _, i = self.tree.query(X)
        n = len(self.P)
        t = np.einsum("ij,ij->i", X - self.P[i], self.T[i])
        i0 = np.where(t >= 0, i, i - 1).clip(0, n - 2)
        seg = self.P[i0 + 1] - self.P[i0]
        L2 = np.einsum("ij,ij->i", seg, seg)
        u = (np.einsum("ij,ij->i", X - self.P[i0], seg) / L2).clip(0.0, 1.0)
        return i0, u

    def local(self, X):
        """The point's offsets in the spine's frame there (v toward the back, w to the left, t along), and the
        nearest spine sample, with the frame interpolated between samples so nothing steps."""
        i0, u = self._segment(X)
        lerp = lambda A: A[i0] * (1 - u)[:, None] + A[i0 + 1] * u[:, None]
        P, N, Bv, T = lerp(self.P), lerp(self.N), lerp(self.Bv), lerp(self.T)
        d = X - P
        v = np.einsum("ij,ij->i", d, N); w = np.einsum("ij,ij->i", d, Bv); t = np.einsum("ij,ij->i", d, T)
        idx = np.where(u < 0.5, i0, i0 + 1)
        return idx, v, w, t, i0, u

    def sdf(self, X):
        """The distance from each point to the trunk's section there, interpolated along the spine."""
        idx, v, w, t, i0, u = self.local(X)
        phi = np.arctan2(w, v)
        j = (phi + math.pi) / (2 * math.pi) * len(self.phi)
        j0 = np.floor(j).astype(int) % len(self.phi); j1 = (j0 + 1) % len(self.phi); f = j - np.floor(j)
        Rr = lambda i: self.R[i, j0] * (1 - f) + self.R[i, j1] * f
        R = Rr(i0) * (1 - u) + Rr(i0 + 1) * u
        d = np.hypot(v, w) - R
        d = np.where((i0 == 0) & (u <= 0.0), np.maximum(d, -t), d)
        return np.where((i0 == len(self.P) - 2) & (u >= 1.0), np.maximum(d, t), d)


def pieces(anat):
    out = []
    for sgn in (1, -1):
        out += [Piece(b, sgn, "bone") for b in anat["bones"]]
        out += [Piece(m, sgn, "muscle") for m in anat["muscles"]]
    return out


def field(X, trunk, parts, all_parts=False):
    """The body's field at points X: the trunk joined smoothly with every bone and muscle (or, with no
    trunk, the pieces alone: the wing arm)."""
    D = [p.sdf(X) for p in parts]
    dt = trunk.sdf(X) if trunk is not None else np.full(len(X), 1e3)
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


def spaced(P, gap):
    """A subset of points P, none closer than gap to another (greedy, in order)."""
    keep, grid = [], {}
    for i, p in enumerate(P):
        c = tuple((p // gap).astype(int))
        near = [j for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
                for j in grid.get((c[0] + dx, c[1] + dy, c[2] + dz), [])]
        if all(np.linalg.norm(P[j] - p) >= gap for j in near):
            keep.append(i); grid.setdefault(c, []).append(i)
    return P[keep]


def shell(V, F, Z, sh, N, s, f, band, level=0.25):
    """The dark shell: the skin's dark region (zone below `level`) raised as one layer of plates.
    d is each vertex's distance in from the shell's edge (the zone's level line, found on the skin's
    edges). Along the edge runs a rolled rim divided into small square scutes (their centres spaced
    evenly along the edge, so they go round the shoulder and hip caps too). Inside it the shell is
    transverse bands (band(s): the band coordinate, one per band, from the spine position s), their
    joints slanting forward down the side (slant * f, f the place round the body) like the sheet's,
    each band a shingle thicker toward its back edge, with a groove at each joint. Returns verts,
    faces, the source vertex of each, the distance to the nearest drawn line (edge, joint or scute
    border: inked) and a tint per plate."""
    Z = np.asarray(Z); F = np.asarray(F)
    inside = Z < level
    # small islands of non-shell inside the shell (a few points where the colour flickers) are filled, so the shell
    # has no pinholes: any patch outside it of fewer than `island` points that touches the shell is made shell
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    E0 = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    out = ~inside
    Eo = E0[out[E0[:, 0]] & out[E0[:, 1]]]
    G = coo_matrix((np.ones(len(Eo)), (Eo[:, 0], Eo[:, 1])), shape=(len(V), len(V)))
    _, lab = connected_components(G, directed=False)
    size = np.bincount(lab)
    inside = inside | (out & (size[lab] < sh.get("island", 200)))
    E = np.vstack([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]])
    E = E[inside[E[:, 0]] != inside[E[:, 1]]]
    t = ((level - Z[E[:, 0]]) / (Z[E[:, 1]] - Z[E[:, 0]]))[:, None]
    edge = V[E[:, 0]] + (V[E[:, 1]] - V[E[:, 0]]) * t
    d = np.where(inside, cKDTree(edge).query(V)[0], 0.0)
    keep = inside[F].any(axis=1)
    used = np.unique(F[keep]); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    Vu, Nu, du, su, fu = V[used], N[used], d[used], np.asarray(s)[used], np.asarray(f)[used]
    rw = sh["rim_width"]
    foot = np.sqrt(np.clip(du / sh["foot"], 0.0, 1.0))
    rim = sh["rim_height"] * np.sin(math.pi * np.clip(du / rw, 0.0, 1.0)) ** 0.8
    # bands: joints at whole band coordinates
    bc = band(su + sh["band_slant"] * fu)
    u = bc - np.floor(bc)
    spacing = 1.0 / np.maximum(np.gradient(band(np.linspace(0, 6, 601)), 0.01), 1e-6)
    sp = np.interp(su, np.linspace(0, 6, 601), spacing)
    joint = np.minimum(u, 1 - u) * sp
    in_band = np.clip((du - 0.85 * rw) / (0.15 * rw), 0.0, 1.0)
    # rim scutes: cells round centres spaced along the edge
    centres = spaced(edge, sh["scute_every"])
    dd, ii = cKDTree(centres).query(Vu, k=2)
    border = (dd[:, 1] - dd[:, 0]) / 2
    in_rim = 1 - in_band
    g, gw = sh["groove_depth"], sh["groove_width"]
    groove = g * np.maximum(in_band * (1 - np.clip(joint / gw, 0, 1)), in_rim * (1 - np.clip(border / gw, 0, 1)) * (du > 0.004))
    # the shingle falls into the groove at each joint, so the surface has no cliff for the mesh to saw into teeth
    h = (sh["thickness"] + rim + sh["shingle"] * u * np.clip(joint / gw, 0, 1) * in_band) * foot - groove * foot
    S = Vu + Nu * h[:, None]
    ink = np.minimum(du, np.where(in_band > 0.5, joint, border))
    plate = np.where(in_band > 0.5, np.floor(bc), 1000 + ii[:, 0])
    tint = (np.sin(plate * 12.9898) * 43758.5453) % 1.0
    return S, remap[F[keep]], used, ink, tint


def mesh(trunk, parts, h, pad=0.06):
    """Marching cubes over the body's bounding box at spacing h. Returns verts (N, 3) and faces."""
    pts = [trunk.P - trunk.R.max(axis=1)[:, None], trunk.P + trunk.R.max(axis=1)[:, None]] if trunk is not None else []
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


def piece_weights(V, parts, blend=0.02):
    """Rig weights for a surface over pieces alone: each piece's say is how close it lies to the skin."""
    D = np.array([p.sdf(V) for p in parts])
    infl = np.exp(-(D - D.min(axis=0)) / blend); infl /= infl.sum(axis=0)
    W = []
    for n in range(len(V)):
        acc = {}
        for k, p in enumerate(parts):
            for bn, wt in p.rig.items():
                acc[bn] = acc.get(bn, 0.0) + infl[k, n] * wt
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]; tot = sum(wt for _, wt in top)
        W.append([(bn, wt / tot) for bn, wt in top])
    return W


def vertex_data(V, trunk, parts, trunk_weights, trunk_zone, dark_zone, tail_trust_s, blend=0.025):
    """Per vertex: rig weights, colour zone, the pattern coordinate A (s along the spine) and f (round the body),
    and T, the trunk's share of the surface there (the belly bands are drawn only where it is the trunk).
    Each part's say is how close it lies to the skin there (within ~blend of the nearest). The dark
    shell (dark_zone: 1 inside it) covers whatever lies under it, trunk or muscle."""
    _, dt, D = field(V, trunk, parts, all_parts=True)
    idx, v, w, _, _, _ = trunk.local(V)
    s = trunk.s[idx]
    f = (1 - v / np.maximum(np.hypot(v, w), 1e-9)) / 2  # 0 along the top of the spine, 1 underneath
    allD = np.vstack([dt[None], D])
    infl = np.exp(-(allD - allD.min(axis=0)) / blend)
    infl /= infl.sum(axis=0)
    ZP = [p.zone_at(V) for p in parts]
    W, Z, A, T = [], [], [], []
    for n in range(len(V)):
        sc = max(float(s[n]), 0.0)
        zt = trunk_zone(sc, float(f[n]), V[n, 2], V[n, 1])
        acc = {}
        for bn, wt in trunk_weights(sc):
            acc[bn] = acc.get(bn, 0.0) + infl[0, n] * wt
        z = infl[0, n] * zt
        for k, p in enumerate(parts):
            ik = infl[k + 1, n]
            if ik < 1e-3:
                continue
            for bn, wt in p.rig.items():
                acc[bn] = acc.get(bn, 0.0) + ik * wt
            z += ik * (zt if ZP[k] is None else ZP[k][n])
        top = sorted(acc.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(wt for _, wt in top)
        # the tail's dark-top rule holds only on the tail itself: a limb lying near the tail (the forearm
        # beside its tip) is not part of it
        dk = dark_zone(sc, float(f[n]), V[n, 2], V[n, 1]) if (sc < tail_trust_s or dt[n] < 0.04) else 0.0
        W.append([(bn, wt / tot) for bn, wt in top]); Z.append(z * (1 - dk)); A.append(sc); T.append(float(infl[0, n]))
    return W, Z, A, list(f), T
