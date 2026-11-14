import numpy as np, json
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.morphology import skeletonize
S='/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/'
lab=np.load('lab.npy')
keep=[10,9,5,6,19,24,31,33,32,3,34,4,17,26,25,27,30,11]
out={}
for c in keep:
    m=lab==c
    sk=skeletonize(m)
    ys,xs=np.where(sk)
    # order skeleton points by walking: start from endpoint (fewest neighbours)
    pts=set(zip(xs.tolist(),ys.tolist()))
    def nb(p): return [(p[0]+dx,p[1]+dy) for dx in (-1,0,1) for dy in (-1,0,1) if (dx or dy) and (p[0]+dx,p[1]+dy) in pts]
    ends=[p for p in pts if len(nb(p))==1] or [min(pts,key=lambda p:p[1])]
    # longest path via BFS twice
    def bfs(s):
        prev={s:None}; q=[s]; last=s
        for p in q:
            for n_ in nb(p):
                if n_ not in prev: prev[n_]=p; q.append(n_); last=n_
        return last,prev
    a,_=bfs(ends[0]); b,prev=bfs(a)
    path=[]; p=b
    while p: path.append(p); p=prev[p]
    path=path[::-1][::4]
    # shift each skeleton point toward NW boundary: march in direction (-1,-1)/sqrt2 until leaving mask
    sh=[]
    for x,y in path:
        k=0
        while 0<y-k-1<m.shape[0] and 0<x-k-1<m.shape[1] and m[int(y-k*0.6),int(x-k*0.8)] and k<20: k+=1
        sh.append((round(x-k*0.8,1),round(y-k*0.6,1)))
    out[c]=sh
json.dump(out,open('edges_px.json','w'))
im=Image.open('/mnt/user-data/attachments/696fbe25-b3a1-58f2-ae57-2aad7225b91b/f4c7a291-image.jpg').convert('RGB')
d=ImageDraw.Draw(im)
cols=[(255,0,0),(0,90,255),(255,140,0),(0,170,0),(200,0,200),(0,180,180),(120,60,0),(255,0,120)]
for i,(c,pp) in enumerate(out.items()):
    d.line(pp,fill=cols[i%len(cols)],width=2); d.text(pp[0],str(c),fill=cols[i%len(cols)])
im.save(S+'edges.png')
im.crop((80,250,560,850)).resize((960,1200)).save(S+'edgesW.png')
