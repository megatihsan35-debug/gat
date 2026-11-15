"""v3.1 section (16 Nov 2026, from the user's sketch + reference image): three rings stepping up towards the centre,
with daylight + air gaps between them, and a free-standing ring bridge.

FIRST FLOOR +5.400:  inner ring R9.5-15.5 | gap R15.5-17.0 | RING BRIDGE R17.0-20.0 | gap R20.0-21.5 | outer ring R21.5-26.5
  - the bridge touches nothing but four 3 m walkways on the gate axes (inner ring -> bridge -> outer ring)
  - the gaps are open from the first floor to the roof; over ground-floor rooms they are walk-on (maintenance) opal glass
    rooflights at +5.400, over the gate passages they stay open so light and air reach the gates
SECOND FLOOR +9.600: inner ring only (the deepest ring is the tallest)
ROOF: three tiers, each 1.8 m above the one outside it, all keeping the approved wave (high Selatan + Utara, low Tengah + Timur):
  outer tier R20.6-28.3 (top = wave W), middle tier R15.9-21.2 (W + 1.8), inner tier = the funnel R1.5-16.6 (rim W + 3.6)
  where the tiers overlap in plan (R20.6-21.2 over the outer gap, R15.9-16.6 over the inner gap) the vertical opening
  between them is a clerestory: daylight and stack-effect air in, rain kept out by the overlap."""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'v2'))
import scheme as SC

R_IR0, R_GAL, R_IR1 = 9.5, 11.0, 15.5          # inner ring: court gallery walk R9.5-11.0, rooms R11.0-15.5
R_BG0, R_BG1 = 17.0, 20.0                      # ring bridge
R_OR0, R_OS, R_OR1 = 21.5, 25.0, 26.5          # outer ring: rooms R21.5-25.0 facing the gap, fin walk R25.0-26.5 behind the fins
R_M = 18.5                                     # bridge column ring (grid M) - on ground-floor walls
R_B, R_E = 11.0, 15.5                          # inner ring column rings (grid B in the arcade / walk wall, grid E on the ring edge)
WALK_W = 3.0                                   # the four gate walkways
GAP_IN, GAP_OUT = (R_IR1, R_BG0), (R_BG1, R_OR0)

def ann(r0, r1): return SC.ann(r0, r1)
WALKWAYS = unary_union([SC.strip(s['b'], WALK_W, R_IR1 - 0.05, R_OR0 + 0.05) for s in SC.SPINES])
INNER = ann(R_IR0, R_IR1); BRIDGE = ann(R_BG0, R_BG1); OUTER = ann(R_OR0, R_OR1)
GAPS = ann(*GAP_IN).union(ann(*GAP_OUT)).difference(WALKWAYS)

# ---- roof tiers ----------------------------------------------------------------------------------------------------
T_OUT = (20.6, 28.3); T_MID = (15.9, 21.2); R_OC, R_FUN = 1.5, 16.6
STEP = 1.8; ROOF_T = SC.ROOF_T; MID_T = 0.35; FUN_T = 0.28; Z_OC = 11.4
def W(b): return SC.roof_h(b)
def brg(p): v = np.array(p) - np.array(SC.C); return math.degrees(math.atan2(v[0], v[1])) % 360
def rad(p): return float(np.hypot(*(np.array(p) - np.array(SC.C))))
def out_top(p): return W(brg(p))
def out_under(p):
    r = rad(p); t = out_top(p)
    return t - ROOF_T if r <= 26.5 else t - ROOF_T + (ROOF_T - 0.12) * (r - 26.5) / (T_OUT[1] - 26.5)
def mid_top(p): return W(brg(p)) + STEP
def mid_under(p): return mid_top(p) - MID_T
def fun_rim(b): return W(b) + 2 * STEP
def fun_top(p):
    r = rad(p); b = brg(p)
    return Z_OC + (fun_rim(b) - Z_OC) * (max(r, R_OC) - R_OC) / (R_FUN - R_OC)
def fun_under(p): return fun_top(p) - FUN_T
OUT_FP = ann(*T_OUT).difference(SC.RF_VOID)
MID_FP = ann(*T_MID).difference(SC.RF_VOID)
FUN_FP = ann(R_OC, R_FUN)
SLOT_GLASS = unary_union([ann(*T_OUT), ann(*T_MID)]).intersection(SC.RF_VOID)   # the gate slots are glazed now (dry walkways below)
def roof_under_at(p):
    """underside of the lowest roof element above p (what a wall or column below meets)"""
    r = rad(p); cands = []
    if r <= R_FUN: cands.append(fun_under(p))
    if T_MID[0] <= r <= T_MID[1]: cands.append(mid_under(p))
    if T_OUT[0] <= r <= T_OUT[1]: cands.append(out_under(p))
    return min(cands) if cands else out_under(p)
def roof_top_at(p):
    r = rad(p); cands = []
    if r <= R_FUN: cands.append(fun_top(p))
    if T_MID[0] <= r <= T_MID[1]: cands.append(mid_top(p))
    if T_OUT[0] <= r <= T_OUT[1]: cands.append(out_top(p))
    return max(cands) if cands else out_top(p)
def clerestory(b):
    """clear heights of the two clerestories at bearing b: inner (mid top -> funnel underside at R16.25), outer (outer top -> mid underside at R20.9)"""
    pi = SC.P(16.25, b); po = SC.P(20.9, b)
    return fun_under(pi) - mid_top(pi), mid_under(po) - out_top(po)
