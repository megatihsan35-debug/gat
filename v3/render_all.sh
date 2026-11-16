#!/bin/sh
# final renders, one after another (2 CPU cores): 1920x1080, adaptive 48 spp + OpenImageDenoise
cd /home/claude/gat/v3
for v in hero gate dusk aerial_nw bridge court arcade; do
  /home/claude/bpyenv/.venv/bin/python render_blender.py $v 100 48 2>&1 | grep -E "RENDERED|Traceback|Error"
done
echo ALLDONE
