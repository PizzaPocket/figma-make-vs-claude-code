"""Trace and measure Clay's trunk on the side sheet (how body_design.json's trunk stations were made).

The spine, dorsal outline and ventral outline are traced by hand in working px of the 1400-px side
sheet. At stations along the spine, the depth to each outline is measured along the perpendicular,
and an overlay is drawn on the sheet to check the trace.

    python3 trunk_trace.py SHEET_1400.png overlay.jpg > rows.json
"""
import json, sys, numpy as np
from PIL import Image, ImageDraw
# traced in working px of the 1400-px side sheet
spine = [(225,262),(280,300),(330,345),(385,395),(445,430),(550,465),(650,478),(750,482),(850,478),(950,472),(1050,490),(1150,545),(1225,620),(1252,700),(1250,780),(1215,850),(1150,893),(1050,906),(950,904),(850,903),(760,908),(690,930),(645,962),(625,995)]
dorsal = [(233,188),(300,183),(360,186),(420,200),(480,225),(540,262),(580,300),(650,320),(750,335),(850,355),(950,385),(1050,430),(1150,505),(1230,590),(1290,690),(1312,780),(1295,850),(1250,895),(1185,935),(1092,955),(969,955),(846,943),(754,949),(661,974),(625,998)]
ventral = [(206,333),(240,372),(268,400),(285,440),(292,490),(296,540),(300,580),(330,630),(400,655),(550,652),(650,642),(760,640),(850,620),(950,600),(1050,615),(1135,668),(1180,730),(1191,789),(1172,851),(1120,862),(1000,860),(850,860),(760,868),(690,900),(645,945),(625,995)]
def dense(P, n=600):
    P=np.array(P,float); s=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))])
    t=np.linspace(0,s[-1],n); return np.stack([np.interp(t,s,P[:,0]),np.interp(t,s,P[:,1])],1), t
def ray_hit(o, d, poly):
    best=None
    for a,b in zip(poly[:-1],poly[1:]):
        a=np.array(a,float); b=np.array(b,float); e=b-a
        M=np.array([[d[0],-e[0]],[d[1],-e[1]]])
        if abs(np.linalg.det(M))<1e-9: continue
        t,u=np.linalg.solve(M,a-o)
        if t>0 and 0<=u<=1 and (best is None or t<best): best=t
    return best
S, s = dense(spine, 200)
T = np.gradient(S, axis=0); T /= np.linalg.norm(T,axis=1)[:,None]
rows=[]
for i in range(len(S)):
    n_up = np.array([T[i,1], -T[i,0]])
    a1, b1 = ray_hit(S[i], n_up, dorsal), ray_hit(S[i], -n_up, ventral)
    a2, b2 = ray_hit(S[i], -n_up, dorsal), ray_hit(S[i], n_up, ventral)
    ok1 = (a1 or 9e9) + (b1 or 9e9); ok2 = (a2 or 9e9) + (b2 or 9e9)
    if ok2 < ok1: n_up, a1, b1 = -n_up, a2, b2
    du, dv = a1, b1
    rows.append((s[i], S[i][0], S[i][1], du, dv, n_up))
img = Image.open(sys.argv[1]).convert('RGB'); d = ImageDraw.Draw(img)
d.line([tuple(p) for p in spine], fill=(0,255,0), width=2)
d.line(dorsal, fill=(0,200,255), width=2); d.line(ventral, fill=(255,0,255), width=2)
out=[]
for k,(si,x,y,du,dv,n) in enumerate(rows):
    if k % 4: continue
    if du and dv:
        d.line([(x+n[0]*du, y+n[1]*du),(x-n[0]*dv, y-n[1]*dv)], fill=(255,255,0), width=1)
    out.append([round(si/343,4), round((700-x)/343,4), round((830-y)/343,4), None if du is None else round(du/343,4), None if dv is None else round(dv/343,4)])
img.save(sys.argv[2], quality=88)
print(json.dumps(out))
