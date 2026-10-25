#!/bin/bash
# Set up what the Clay model build needs, outside the repo (nothing here is committed):
#   - Blender as a Python module (bpy 5.2.3, Python 3.13) plus numpy, scipy and Pillow, in a virtualenv;
#   - three.js r128 and its GLTFLoader, for the render viewer;
#   - the reference images (tools/fetch_refs.py).
# Safe to run again: each step is skipped once done. Locations (override with env vars):
#   CLAY_ENV  (default ~/.cache/clay-env)   the virtualenv
#   CLAY_THREE (default ~/.cache/clay-three) three.min.js and GLTFLoader.js
#   CLAY_REFS (default prototypes/clay/refs, git-ignored) the reference images
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ENV="${CLAY_ENV:-$HOME/.cache/clay-env}"
THREE="${CLAY_THREE:-$HOME/.cache/clay-three}"

if [ ! -x "$ENV/bin/python" ] || ! "$ENV/bin/python" -c "import bpy" 2>/dev/null; then
  echo "clay setup: creating $ENV with bpy (a large download, a few minutes)"
  if command -v uv >/dev/null; then
    uv venv --python 3.13 "$ENV"
    uv pip install --python "$ENV/bin/python" bpy==5.2.3 numpy scipy pillow
  else
    python3.13 -m venv "$ENV"
    "$ENV/bin/pip" install --quiet bpy==5.2.3 numpy scipy pillow
  fi
fi

if [ ! -f "$THREE/three.min.js" ] || [ ! -f "$THREE/GLTFLoader.js" ]; then
  echo "clay setup: fetching three.js r128 into $THREE"
  mkdir -p "$THREE/pkg"
  (cd "$THREE/pkg" && npm install --silent --no-save --prefix . three@0.128.0 >/dev/null)
  cp "$THREE/pkg/node_modules/three/build/three.min.js" "$THREE/pkg/node_modules/three/examples/js/loaders/GLTFLoader.js" "$THREE/"
fi

"$ENV/bin/python" -I "$HERE/fetch_refs.py"
echo "clay setup: ready (python: $ENV/bin/python, three: $THREE)"
