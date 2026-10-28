"""Validate wing anatomy and optional unjoined skin topology in Blender.

blender -b --python prototypes/clay/body/check_wing.py -- --blend PATH
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_body as B
import wing_rig as W


def model_points(data):
    p = np.array([v.co for v in data])
    return np.column_stack([p[:, 0], p[:, 2], -p[:, 1]])


def check(blend=None):
    rig = W.Rig(B)
    lengths = np.array([np.linalg.norm(np.diff(p, axis=0), axis=1).sum() for p in rig.curves])
    assert (np.diff(lengths) > 0).all(), 'The outermost finger must remain the longest'
    max_error = 0.0
    for u in np.linspace(0, 1, 17):
        pose = rig.state(float(u)); tips = []
        for k, curve in enumerate(rig.curves):
            previous = None
            for j, suffix in enumerate(('', 'b', 'c')):
                rotation, head, scale = pose['wing_finger' + str(k + 1) + suffix]
                assert scale == 1, 'Main fingers must not telescope'
                end = head + rotation @ (curve[j + 1] - curve[j])
                max_error = max(max_error, abs(np.linalg.norm(end - head) - np.linalg.norm(curve[j + 1] - curve[j])))
                if previous is not None:
                    assert np.linalg.norm(previous - head) < 1e-6, 'Broken finger joint'
                previous = end
            tips.append(previous)
        rays = np.array(tips) - pose['wing_carpal'][1]
        rotation = pose['wing_carpal'][0]
        angles = np.arctan2(rays @ (rotation @ rig.across0), rays @ (rotation @ rig.avg0))
        assert (np.diff(angles) > 0).all(), 'Finger order changes during folding'
        assert np.isfinite(rays).all()
    assert max_error < 1e-8
    rotation, _, scale = rig.state(1)['wing_elbowfinger']
    direction = rotation @ rig.acc0
    assert direction[1] > .99 and -.15 < direction[0] < 0 and abs(direction[2]) < .05
    assert abs(scale - .5) < 1e-9
    report = {'main_finger_lengths': lengths.tolist(), 'fold_samples': 17,
              'max_link_length_error': float(max_error), 'folded_elbow_direction': direction.tolist(), 'skins': []}
    if blend:
        bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
        for obj in bpy.data.objects:
            if obj.name not in ('WingArmL', 'WingArmR'):
                continue
            faces = np.array([p.vertices for p in obj.data.polygons])
            edges = np.sort(np.vstack([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]), axis=1)
            unique, counts = np.unique(edges, axis=0, return_counts=True)
            graph = coo_matrix((np.ones(len(unique)), (unique[:, 0], unique[:, 1])), shape=(len(obj.data.vertices),) * 2)
            components, _ = connected_components(graph, directed=False)
            assert components == 1, (obj.name, 'Arm and fingers must be one connected skin', components)
            assert (counts == 2).all(), (obj.name, 'Skin has open or nonmanifold edges')
            names = [g.name for g in obj.vertex_groups]
            assert all(any(n.startswith('wing_finger' + str(k) + suffix + '.') for n in names) for k in range(1, 5) for suffix in ('', 'b', 'c'))
            assert all(np.isfinite(model_points(key.data)).all() for key in obj.data.shape_keys.key_blocks)
            report['skins'].append({'name': obj.name, 'vertices': len(obj.data.vertices), 'components': int(components), 'nonmanifold_edges': int((counts != 2).sum())})
        assert report['skins'], 'No unjoined WingArm skin was found'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--blend')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    print('WING_ANATOMY_CHECK ' + json.dumps(check(args.blend)), flush=True)
