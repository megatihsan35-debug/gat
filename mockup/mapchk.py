import json, numpy as np, cv2, sys
sys.path.insert(0,'/home/claude/crit1')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from geom import *
import site_el as SE
H=np.load('H.npy')
def mp(pts): return cv2.perspectiveTransform(np.array([pts],float),H)[0]
E=json.load(open('edges_px.json'))
fig,ax=plt.subplots(figsize=(11,11))
ax.plot(*np.vstack([SITE,SITE[:1]]).T,'r--')
for (x0,y0,x1,y1) in [(56,65,106,112),(-18,44,4.4,67),(40,-70,150,-52),(91,5,109,63)]:
    ax.add_patch(plt.Rectangle((x0,y0),x1-x0,y1-y0,fill=False,ec='k'))
road=Polygon([tuple(SE.road_pt(-70)-SE.N_IN*0.5),tuple(SE.road_pt(190)-SE.N_IN*0.5),tuple(SE.road_pt(190)-SE.N_IN*11),tuple(SE.road_pt(-70)-SE.N_IN*11)])
ax.plot(*road.exterior.xy,'g-')
ax.add_patch(plt.Rectangle((113.5,-40),9.5,160,fill=False,ec='g'))
ax.add_patch(plt.Circle(B,R_OVH+3,fill=False,ec='b')); ax.add_patch(plt.Circle(S,RS_OUT+3,fill=False,ec='b'))
for k,pp in E.items():
    q=mp(pp); ax.plot(q[:,0],q[:,1],lw=2); ax.text(*q[len(q)//2],k)
# photo context blocks
for nm,box in [('istana',[(105,470),(205,470),(205,570),(105,570)]),('futsal',[(470,280),(760,265),(785,440),(500,455)]),('tennis',[(680,455),(750,450),(830,800),(760,805)]),('Lblk',[(400,290),(445,290),(470,410),(415,410)]),('sblk',[(425,1000),(490,1000),(490,1070),(425,1070)])]:
    q=mp(box); ax.fill(q[:,0],q[:,1],alpha=0.3); ax.text(*q.mean(0),nm)
q=mp([(90,295),(930,295),(930,1075),(90,1075)]); ax.plot(*np.vstack([q,q[:1]]).T,'k:')
ax.set_aspect('equal'); ax.grid(True); ax.set_xlim(-30,150); ax.set_ylim(-80,120)
plt.savefig('/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/mapchk.png',dpi=80)
