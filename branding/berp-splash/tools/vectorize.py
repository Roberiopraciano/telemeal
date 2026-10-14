import sys
from PIL import Image; import numpy as np, cv2, json
a=np.array(Image.open(sys.argv[1]).convert('RGBA')).astype(np.float32)
alpha=a[...,3]
op=alpha>100
blue=op&(a[...,2]>a[...,0]); orng=op&(a[...,0]>=a[...,2])
S=4
pieces=[]
for cls,m in [('b',blue),('o',orng)]:
    n,lab,st,cen=cv2.connectedComponentsWithStats(m.astype(np.uint8),connectivity=4)
    for i in range(1,n):
        if st[i,4]<40: continue
        x,y,w,h=st[i,:4]; pad=6
        x0,y0=max(x-pad,0),max(y-pad,0); x1,y1=x+w+pad,y+h+pad
        L=lab[y0:y1,x0:x1]; cm=(L==i).astype(np.uint8)
        others=(op[y0:y1,x0:x1]&(L!=i))
        ring=cv2.dilate(cm,np.ones((5,5),np.uint8)).astype(bool)&~others
        soft=np.where(ring,alpha[y0:y1,x0:x1]/255.0,0).astype(np.float32)
        soft[cm.astype(bool)]=np.maximum(soft[cm.astype(bool)],0.75)
        up=cv2.resize(soft,None,fx=S,fy=S,interpolation=cv2.INTER_CUBIC)
        up=cv2.GaussianBlur(up,(0,0),S*0.45)
        bw=(up>0.5).astype(np.uint8)
        cs,hier=cv2.findContours(bw,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
        paths=[]
        for c,hh in zip(cs,hier[0]):
            if cv2.contourArea(c)<S*S*6: continue
            cf=c[:,0,:].astype(np.float32); k=7
            ext=np.concatenate([cf[-k:],cf,cf[:k]])
            ker=np.ones(2*k+1,np.float32)/(2*k+1)
            sm=np.stack([np.convolve(ext[:,j],ker,'same')[k:-k] for j in (0,1)],1)
            ap=cv2.approxPolyDP(sm.reshape(-1,1,2),0.25*S,True)[:,0,:].astype(float)
            pts=[[round(x0+(px+0.5)/S-0.5,2),round(y0+(py+0.5)/S-0.5,2)] for px,py in ap]
            paths.append({'pts':pts,'hole':bool(hh[3]>=0)})
        if not paths: continue
        sel=(lab==i)&(alpha>220)
        if sel.sum()<5: sel=(lab==i)
        col=a[sel][:,:3].mean(0)
        pieces.append({'cls':cls,'color':'#%02x%02x%02x'%tuple(int(round(v)) for v in col),
            'cx':float(cen[i,0]),'cy':float(cen[i,1]),'bbox':[int(x),int(y),int(w),int(h)],'paths':paths})
# classify text vs globe: text is right of x=470
for p in pieces: p['kind']='text' if p['bbox'][0]>470 else 'tile'
# group text into letters by horizontal overlap (i-dot joins its stem)
txt=sorted([p for p in pieces if p['kind']=='text'],key=lambda p:p['bbox'][0])
letters=[]
for p in txt:
    x,y,w,h=p['bbox']; word='berp' if p['cls']=='b' else 'sistemas'
    for L in letters:
        ov=min(x+w,L['x1'])-max(x,L['x0'])
        if L['word']==word and ov>0.5*min(w,L['x1']-L['x0']):
            L['items'].append(p); L['x0']=min(L['x0'],x); L['x1']=max(L['x1'],x+w); break
    else: letters.append({'word':word,'x0':x,'x1':x+w,'items':[p]})
for w in ['berp','sistemas']:
    ls=[L for L in letters if L['word']==w]; ls.sort(key=lambda L:L['x0'])
    for k,L in enumerate(ls):
        for p in L['items']: p['word']=w; p['letter']=k
    print(w,len(ls),[ (L['x0'],L['x1']) for L in ls])
xs=[q[0] for p in pieces for pa in p['paths'] for q in pa['pts']]; ys=[q[1] for p in pieces for pa in p['paths'] for q in pa['pts']]
print('bbox',min(xs),min(ys),max(xs),max(ys),'pieces',len(pieces),'tiles',sum(p['kind']=='tile' for p in pieces),'verts',len(xs))
json.dump(pieces,open(sys.argv[2],'w'))
