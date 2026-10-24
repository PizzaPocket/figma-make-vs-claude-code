"""Clay, head and body, built in Blender from measured data, exported as one rigged .glb.

The head comes from ../head/build_head.py. The body is built here, element by element (see
body_design.json and body_sheets.md):
- trunk: neck, torso and tail as one loft along a curved spine, with cross-sections perpendicular
  to it, skinned to a chain of spine bones.
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
def trunk_frames(step=0.01):
    """Spine points (bind pose), depths, and a parallel-transported frame (dorsal normal N, side B)."""
    st = np.array(TR["stations"], float)
    s_all = np.arange(-TR["front_overlap"], st[-1, 0] + 1e-9, step)
    pose = TR["tail_pose"]
    P, DU, DV = [], [], []
    for s in s_all:
        sc = max(s, 0.0)
        z, y, du, dv = (table(st, sc, c) for c in (1, 2, 3, 4))
        if s < 0:  # run on into the head along the first tangent, so the join is hidden inside it
            z1, y1 = table(st, 0.02, 1), table(st, 0.02, 2)
            z, y = z + (z - z1) / 0.02 * (-s), y + (y - y1) / 0.02 * (-s)
        lift = max(0.0, pose["ground_y"] + dv - y) * smoothstep(pose["ground_from_s"] - 0.4, pose["ground_from_s"], sc)
        x = pose["curl_x"] * smoothstep(pose["curl_from_s"], st[-1, 0], sc) ** 1.5
        P.append((x, y + lift, z)); DU.append(du); DV.append(dv)
    P = np.array(P)
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


def zone_value(s, f):
    """0 dark back, 0.5 orange side, 1 cream underside, at side fraction f (0 dorsal .. 1 ventral)."""
    rows = TR["zones"]["rows"]
    fd, fc = table(rows, s, 1), table(rows, s, 2)
    return 0.5 * smoothstep(fd - 0.015, fd + 0.015, f) + 0.5 * smoothstep(fc - 0.015, fc + 0.015, f)


def trunk_bones():
    """Spine bones (name, head, tail, parent) and, per bone, its s range."""
    s_all, P, *_ = trunk_frames()
    at = lambda s: tuple(P[int(np.argmin(abs(s_all - s)))])
    bones, ranges = [], []
    parent = None
    for name, s0, s1 in TR["bones"]["chain_forward"]:
        bones.append((name, at(s0), at(s1), parent)); ranges.append((name, min(s0, s1), max(s0, s1)))
        parent = name
    t0, n = TR["bones"]["tail_from"], TR["bones"]["tail_count"]
    t1 = TR["stations"][-1][0]
    edges = [t0 + (t1 - t0) * (k / n) ** 0.85 for k in range(n + 1)]  # shorter segments toward the tip
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


def trunk_part(ranges, around=72):
    s_all, P, DU, DV, N, Bv = trunk_frames()
    verts, faces, A, Bf, Z, W = [], [], [], [], [], []
    for i, s in enumerate(s_all):
        sc = max(s, 0.0)
        nsq = table(TR["squareness"], sc)
        wf = table(TR["width"]["factor"], sc) * (DU[i] + DV[i]) / 2
        taper = 1.0 if i < len(s_all) - 1 else 0.0  # close the tail tip
        for k in range(around):
            th = 2 * math.pi * k / around  # 0 dorsal, pi ventral, pi/2 Clay's left
            c, sn = math.cos(th), math.sin(th)
            v = (DU[i] if c > 0 else DV[i]) * math.copysign(abs(c) ** (2 / nsq), c)
            w = wf * math.copysign(abs(sn) ** (2 / nsq), sn)
            verts.append(tuple(P[i] + (N[i] * v + Bv[i] * w) * taper))
            f = (1 - c) / 2
            A.append(sc); Bf.append(f); Z.append(zone_value(sc, f)); W.append(trunk_weights(sc, ranges))
    for i in range(len(s_all) - 1):
        for k in range(around):
            a = i * around + k; b = i * around + (k + 1) % around
            faces.append([a, a + around, b + around, b])
    return H.add_part("Trunk", verts, faces, {"_PART": [20] * len(verts), "_A": A, "_B": Bf, "_ZONE": Z}, W)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    tb, ranges = trunk_bones()
    objs, head_bones = H.head_parts()
    objs.append(trunk_part(ranges))
    neck_end = TR["bones"]["chain_forward"][-1][0]
    bones = tb + [(n, h, t, p or neck_end) for n, h, t, p in head_bones]
    H.assemble(objs, bones, OUT, "ClayRig")


if __name__ == "__main__":
    main()
