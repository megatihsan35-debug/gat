"""External works: drives, parking, plazas, ribbon canopies, landscape (metres)."""
import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from geom import *

ROAD_A, ROAD_B = SITE[5], SITE[4]                    # south boundary along Jalan Tok Muda Awang Ngah
T_ROAD = (ROAD_B - ROAD_A) / np.linalg.norm(ROAD_B - ROAD_A)
N_IN = np.array([-T_ROAD[1], T_ROAD[0]])             # inward normal (north-ish)
def road_pt(x):  # point on boundary at given x
    t = (x - ROAD_A[0]) / T_ROAD[0]; return ROAD_A + T_ROAD * t

# drop-off lay-by (inside site, along road)
p1, p2 = road_pt(30), road_pt(57)
LAYBY = Polygon([road_pt(24), road_pt(63), p2 + N_IN * 3.0, p1 + N_IN * 3.0])
OKU_BAY = Polygon([road_pt(58.5) + N_IN * 3.0, road_pt(62.1) + N_IN * 3.0, road_pt(62.1) + N_IN * 9.0, road_pt(58.5) + N_IN * 9.0])

# service drive (centreline) + yard
DRIVE_CL = LineString([road_pt(13) - N_IN * 2, road_pt(13) + N_IN * 3, (15.5, 12), (21, 26), (26, 38), (31, 46), (36, 48.5)])
DRIVE = DRIVE_CL.buffer(2.75, cap_style=2, join_style=1).intersection(SITE_POLY.buffer(0.01).union(LineString([road_pt(5), road_pt(20)]).buffer(3)))
YARD = Polygon([(29, 43.6), (57, 44.5), (57, 55.5), (33, 54.2)]).intersection(SITE_POLY)
SUCTION = Polygon([(50, 46), (55, 46), (55, 49), (50, 49)])     # underground suction tank + pump (hatched)

# staff parking (5) + motorcycles (10) off the drive
PARK_STAFF = [Polygon([road_pt(19 + 2.5 * i) + N_IN * 6.2, road_pt(21.5 + 2.5 * i) + N_IN * 6.2, road_pt(21.5 + 2.5 * i) + N_IN * 11.2, road_pt(19 + 2.5 * i) + N_IN * 11.2]) for i in range(5)]
PARK_AISLE = Polygon([road_pt(17.5) + N_IN * 11.2, road_pt(32) + N_IN * 11.2, road_pt(32) + N_IN * 17.2, road_pt(17.5) + N_IN * 17.2])
MOTOR = [Polygon([road_pt(19 + 1.0 * i) + N_IN * 17.2, road_pt(20 + 1.0 * i) + N_IN * 17.2, road_pt(20 + 1.0 * i) + N_IN * 19.2, road_pt(19 + 1.0 * i) + N_IN * 19.2]) for i in range(10)]

# plazas
PLAZA_SE = Polygon([road_pt(66) + N_IN * 6.0, road_pt(112.8) + N_IN * 0.2, (112.3, 0.1), (92.2, 1.2), (89.8, 22), (80.5, 30.5), (78, 13), (70, 5)]).difference(Point(B).buffer(R_OVH, 180))
GARDEN_N = Polygon([(57.5, 44.5), (86.5, 41), (87, 61.5), (57.5, 58.8)]).intersection(SITE_POLY).difference(Point(B).buffer(R_OVH, 180))
BIKES = [LineString([(96 + 0.8 * i, 4.5), (96 + 0.8 * i, 6.3)]) for i in range(10)]

# ribbon canopies (centrelines; width 4.5 m) – one per region
def gate_pt(bearing, r=R_OVH): return tuple(B + d(bearing) * r)
K = B + d(QIBLA) * R_OUT
PERP = np.array([d(QIBLA)[1], -d(QIBLA)[0]])
NW_DOOR = tuple(K + PERP * 5.2 + d(QIBLA) * 1.0)
RIBBONS = {
    'TENGAH': ('Riben Tengah · Selangor, KL, Putrajaya (235–247°)', [tuple(road_pt(41) + N_IN * 3.0), (42.2, 6), gate_pt(256.3)], 4.5),
    'SELATAN': ('Riben Selatan · N. Sembilan, Melaka, Johor (146–214°)', [tuple(road_pt(73) + N_IN * 1.0), (62, 1.0), gate_pt(211.3)], 4.0),
    'TIMUR': ('Riben Timur · Kuantan, Terengganu, Kelantan (356–68°)', [(103, -7.5), (98.5, 6), (90.5, 19.5), gate_pt(67.3, R_L1)], 4.5),
    'UTARA': ('Riben Utara · Perak, Penang, Kedah, Perlis (311–324°)', [(53, 56), (50.3, 45.5), NW_DOOR], 4.0),
}
def ribbon_poly(pts, w):
    return LineString(pts).buffer(w / 2, cap_style=2, join_style=1)

# trees (x, y, canopy dia)
TREES = [tuple(road_pt(x) + N_IN * 4.2) + (6,) for x in range(70, 112, 8)] + \
        [tuple(road_pt(x) + N_IN * 2.0) + (5,) for x in (6, 34, 50)] + \
        [(8, 22, 6), (12, 34, 6), (19, 47, 5), (62, 56, 6), (72, 56.5, 6), (82, 55, 6), (88.5, 46, 5), (88, 34, 5),
         (106, -4, 6), (84, 3, 5)]
COURT_TREE = (B[0], B[1], 6.0)
