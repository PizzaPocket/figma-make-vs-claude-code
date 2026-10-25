#!/bin/bash
# Build and render a set of views next to the references.
#   tools/render.sh head SET OUT.jpg     build the head alone, render prototypes/clay/head/views.json SET
#   tools/render.sh body SET OUT.jpg     build the whole creature, render prototypes/clay/body/views.json SET
# NOBUILD=1 renders the last build. Needs tools/setup_env.sh run once.
set -e
CLAY="$(cd "$(dirname "$0")/.." && pwd)"; REPO="$(cd "$CLAY/../.." && pwd)"
ENV="${CLAY_ENV:-$HOME/.cache/clay-env}"; THREE="${CLAY_THREE:-$HOME/.cache/clay-three}"; REFS="${CLAY_REFS:-$CLAY/refs}"
OUTDIR="${CLAY_OUT:-$CLAY/out}"; mkdir -p "$OUTDIR"
PART="$1"; SET="$2"; OUT="$3"
case "$PART" in
  head) GLB="$OUTDIR/head.glb"; BUILD="$CLAY/head/build_head.py" ;;
  body) GLB="$OUTDIR/clay.glb"; BUILD="$CLAY/body/build_body.py" ;;
  *) echo "usage: tools/render.sh head|body SET OUT.jpg"; exit 1 ;;
esac
[ "$NOBUILD" ] || "$ENV/bin/python" "$BUILD" --out "$GLB" 2>&1 | grep -E "exported|Error|Traceback|line " || true
"$ENV/bin/python" "$REPO/.claude/skills/creature-sculpting/scripts/render_sheet.py" --viewer "$CLAY/head/head-viewer.js" --mount mountHead \
  --glb "$GLB" --three "$THREE" --views "$CLAY/$PART/views.json" --set "$SET" --design "$CLAY/head/head_design.json" --refs "$REFS" --out "$OUT"
