import pymupdf as fitz, sys
from PIL import Image, ImageChops
PDF='/mnt/user-data/attachments/696fbe25-b3a1-58f2-ae57-2aad7225b91b/3981ad2e-TitikTemu_Crit1_Drawings_A1.pdf'
d=fitz.open(PDF); k=1.8
C={'siteplan':(0,(28,223,602,684)),'roof':(0,(645,223,1182,665)),
   'gf':(1,(34,140,571,582)),'l1':(1,(672,140,1208,582)),
   'secA':(2,(100,150,682,290)),'secB':(2,(765,160,1232,290)),
   'elS':(2,(45,440,712,562)),'elE':(2,(738,440,1278,562)),'elN':(2,(45,700,712,830)),'elW':(2,(738,700,1278,830))}
dpi=int(sys.argv[1]) if len(sys.argv)>1 else 60
for n,(pg,(x0,y0,x1,y1)) in C.items():
    r=fitz.Rect(x0*k,y0*k,x1*k,y1*k)
    pix=d[pg].get_pixmap(dpi=dpi,clip=r,alpha=False)
    im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    if n.startswith(('sec','el')):   # trim pure white margins
        bg=Image.new('RGB',im.size,(255,255,255)); bb=ImageChops.difference(im,bg).convert('L').point(lambda v:255 if v>8 else 0).getbbox()
        if bb: pad=int(dpi*0.08); im=im.crop((max(0,bb[0]-pad),max(0,bb[1]-pad),min(im.width,bb[2]+pad),min(im.height,bb[3]+pad)))
    im.save(f'img/{n}.png' if dpi>100 else f'/tmp/claude-0/-home-claude/696fbe25-b3a1-58f2-ae57-2aad7225b91b/scratchpad/crop_{n}.png'); print(n, im.size)
