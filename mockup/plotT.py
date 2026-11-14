import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
from terrain import *
fig,ax=plt.subplots(figsize=(12,11))
cm=plt.cm.terrain
for f,L in zip(FACES,LEVELS):
    for g in getattr(f,'geoms',[f]):
        ax.fill(*g.exterior.xy, color=cm((L or 0)/10) if L is not None else 'magenta', alpha=0.8)
        ax.text(*g.representative_point().coords[0], str(L), fontsize=12)
for k,v in LINES.items():
    a=np.array(v); ax.plot(a[:,0],a[:,1],'k-',lw=1); ax.text(*a[len(a)//2],k,color='r',fontsize=14)
ax.plot(*np.vstack([SITE,SITE[:1]]).T,'r--')
for p,L in SEEDS: ax.plot(*p,'r*')
ax.set_xlim(XL-5,XR+5); ax.set_ylim(YB-5,YT+5); ax.set_aspect('equal'); ax.grid(True)
plt.savefig('/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/terr.png',dpi=70)
