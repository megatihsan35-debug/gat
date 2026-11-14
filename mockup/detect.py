import numpy as np
from PIL import Image, ImageDraw, ImageFilter
S='/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/'
im=Image.open('/mnt/user-data/attachments/696fbe25-b3a1-58f2-ae57-2aad7225b91b/f4c7a291-image.jpg').convert('RGB')
a=np.asarray(im).astype(float)
g=a.mean(2)
from scipy import ndimage
gb=ndimage.gaussian_filter(g,1.2)
# board colour is ~ 150-175; shadows < 110
dark=gb<112
# remove thin pen lines: opening with 3px horizontal+vertical structure
op=ndimage.binary_opening(dark,structure=np.ones((4,4)))
lab,n=ndimage.label(op)
sizes=ndimage.sum(op,lab,range(1,n+1))
keep=np.isin(lab,np.where(sizes>120)[0]+1)
out=im.copy(); d=ImageDraw.Draw(out)
ov=np.zeros_like(a); ov[keep]=[255,0,0]
o=Image.fromarray((a*0.55+ov*0.45).astype('uint8'))
o.save(S+'dark.png')
np.save('shadow.npy',keep)
print(n)
