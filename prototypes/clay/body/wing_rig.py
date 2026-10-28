"""Anatomical wing chain with ordered fan retraction and pose-corrected soft tissue.

The shoulder is a socket, the elbow a hinge and the wrist a shared carpal hub.
The accessory elbow digit telescopes by the character's requested convention.
"""
import math
import numpy as np
from mathutils import Matrix, Quaternion


def unit(p):
    p = np.asarray(p, float)
    return p / max(np.linalg.norm(p), 1e-10)


def frame(direction, normal):
    d = unit(direction); n = np.asarray(normal) - d * (np.asarray(normal) @ d)
    if np.linalg.norm(n) < 1e-7:
        n = np.cross(d, [0, 0, 1] if abs(d[2]) < .9 else [0, 1, 0])
    n = unit(n)
    return np.column_stack([d, n, np.cross(d, n)])


def turn(R, amount):
    return np.array(Quaternion((1, 0, 0, 0)).slerp(Matrix(R.tolist()).to_quaternion(), float(amount)).to_matrix(), float)


def finger_ik(root, target, lengths, initial):
    """Fold the three phalanges without changing their individual lengths."""
    points = np.array(initial, float).copy(); goal = np.array(target, float)
    reach = sum(lengths)
    if np.linalg.norm(goal-root) >= reach:
        d = unit(goal-root); return np.array([root+d*t for t in np.r_[0,np.cumsum(lengths)]])
    for _ in range(24):
        points[-1] = goal
        for i in range(2,-1,-1):points[i] = points[i+1]+unit(points[i]-points[i+1])*lengths[i]
        points[0] = root
        for i in range(3):points[i+1] = points[i]+unit(points[i+1]-points[i])*lengths[i]
        if np.linalg.norm(points[-1]-goal)<1e-6:break
    return points


class Rig:
    def __init__(self, B):
        self.B, self.H, self.SK = B, B.H, B.SK
        self.D = B.B['wing']; self.C = self.D['canonical_fold']
        j = self.D['joints']; self.S = np.array(j['shoulder'], float)
        ef, wf = np.array(j['elbow'], float), np.array(j['wrist'], float)
        self.h = unit(self.D['spread']['humerus_dir']); self.f = unit(self.D['spread']['forearm_dir'])
        self.Lh, self.Lf = np.linalg.norm(ef-self.S), np.linalg.norm(wf-ef)
        self.dorsal0 = np.array(self.C['rest_dorsal'], float)
        self.dorsal1 = np.array(self.C['fold_dorsal'], float)
        self.Rh = frame(ef-self.S, self.dorsal1) @ frame(self.h, self.dorsal0).T
        self.Rf = frame(wf-ef, self.dorsal1) @ frame(self.f, self.dorsal0).T
        self.digits = [unit(d)for d in self.D['spread']['finger_dirs']]
        wrist_px=np.array(self.C['folded_wrist_px']);pixels=self.C['reference_pixels_per_unit']
        self.closed=[unit([x,(wrist_px[1]-p[-1][1])/pixels,(wrist_px[0]-p[-1][0])/pixels])for x,p in zip(self.C['folded_finger_depth_offsets'],self.C['folded_finger_paths_px'])]
        self.fan0 = unit(np.cross(self.digits[0], self.digits[-1])); self.avg0 = unit(sum(self.digits))
        self.across0 = unit(np.cross(self.fan0, self.avg0))
        if self.across0 @ (self.digits[-1]-self.digits[0]) < 0:self.across0 *= -1
        self.restE = self.S + self.h*self.Lh; self.restW = self.restE+self.f*self.Lf
        self.roots = [self.restW+self.avg0*self.C['palm_root_forward']+self.across0*(k-1.5)*self.C['root_spacing']for k in range(4)]
        self.curves=[]; self.fold_nodes=[]; self.lengths=[]
        self.knots=[0,self.D['finger']['knuckle_at'],self.D['finger']['knuckle2_at'],1]
        avg1=unit(sum(self.closed)); fan1=unit(np.cross(self.closed[0],self.closed[-1]))
        folded_carpal=frame(avg1,fan1)@frame(self.avg0,self.fan0).T
        wrist_px=np.array(self.C['folded_wrist_px']); pixels=self.C['reference_pixels_per_unit']
        for k,d in enumerate(self.digits):
            trace=np.array(self.C['folded_finger_paths_px'][k],float)
            distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(trace,axis=0),axis=1))];t=distance/distance[-1]
            path=np.column_stack([t*self.C['folded_finger_depth_offsets'][k],(wrist_px[1]-trace[:,1])/pixels,(wrist_px[0]-trace[:,0])/pixels])
            root=folded_carpal@(self.roots[k]-self.restW)
            path+=(1-t)[:,None]*(root-path[0])
            folded=np.array([curve_at(path,a)for a in self.knots]);self.fold_nodes.append(folded)
            lengths=np.linalg.norm(np.diff(folded,axis=0),axis=1);self.lengths.append(float(lengths.sum()))
            back=unit(np.cross(self.fan0,d))
            if back[2]>0:back=-back
            nodes=[self.roots[k]]
            for length,angle in zip(lengths,np.linspace(-1,1,3)*math.radians(self.D['finger']['bend_deg'])):
                nodes.append(nodes[-1]+length*(d*math.cos(angle)+back*math.sin(angle)))
            self.curves.append(np.array(nodes))
        self.acc0=unit(self.D['spread']['elbow_finger_dir']);self.acc1=unit(self.C['elbow_finger_dir'])
        self.accL=float(self.C['elbow_finger_length'])
        self.rest_claw=self.restW+self.f*self.C['wrist_claw_tip_offset']
        self.rest_claw_dir=unit(self.C['wrist_claw_direction_rest'])
        self.fold_claw_dir=unit(self.C['wrist_claw_direction_fold'])
        self.rest={};self.parent={}
        self.add('wing_humerus',self.S,self.restE,'chest')
        self.add('wing_forearm',self.restE,self.restW,'wing_humerus')
        self.add('wing_carpal',self.restW,self.restW+self.avg0*.1,'wing_forearm')
        for i in [1,2]:self.add('wing_socketBlend'+str(i),self.S,self.restE,'chest')
        self.add('wing_wrist_claw',self.rest_claw,self.rest_claw+self.rest_claw_dir*.1,'wing_forearm')
        self.add('wing_elbowfinger',self.restE,self.restE+self.acc0*self.accL,'wing_forearm')
        self.add('wing_elbowclaw',self.restE+self.acc0*self.accL,self.restE+self.acc0*(self.accL+.1),'wing_forearm')
        for k,curve in enumerate(self.curves):
            names=['wing_finger'+str(k+1)+s for s in ['', 'b', 'c']]
            for i,name in enumerate(names):self.add(name,curve[i],curve[i+1],'wing_carpal'if i==0 else names[i-1])
        self.states={}

    def add(self,name,a,b,parent):self.rest[name]=(np.array(a),np.array(b));self.parent[name]=parent

    def state(self,u):
        u=float(u)
        if u in self.states:return self.states[u]
        rh,rf=turn(self.Rh,u),turn(self.Rf,u)
        E=self.S+rh@(self.restE-self.S);W=E+rf@(self.restW-self.restE)
        dirs=[unit(turn(self.B.align(a,b),u)@a)for a,b in zip(self.digits,self.closed)]
        fan=unit(np.cross(dirs[0],dirs[-1]));avg=unit(sum(dirs));rc=frame(avg,fan)@frame(self.avg0,self.fan0).T
        data={'wing_humerus':(rh,self.S,1.),'wing_forearm':(rf,E,1.),'wing_carpal':(rc,W,1.)}
        for i in [1,2]:data['wing_socketBlend'+str(i)]=(turn(rh,i/3),self.S,1.)
        claw_dir=unit(turn(self.B.align(self.rest_claw_dir,self.fold_claw_dir),u)@self.rest_claw_dir)
        claw_R=frame(claw_dir,(1-u)*self.dorsal0+u*self.dorsal1)@frame(self.rest_claw_dir,self.dorsal0).T
        data['wing_wrist_claw']=(claw_R,W+rf@(self.rest_claw-self.restW),1.)
        ad=unit(turn(self.B.align(self.acc0,self.acc1),u)@self.acc0)
        ra=frame(ad,np.cross(rh@self.h,rf@self.f))@frame(self.acc0,np.cross(self.h,self.f)).T
        length_scale=1-u*(1-self.C['elbow_fold_length'])
        data['wing_elbowfinger']=(ra,E,length_scale)
        data['wing_elbowclaw']=(ra,E+ad*self.accL*length_scale,1.)
        for k,d in enumerate(dirs):
            root=W+rc@(self.roots[k]-self.restW)
            goal=W+(1-u)*(self.curves[k][-1]-self.restW)+u*self.fold_nodes[k][-1]
            lengths=np.linalg.norm(np.diff(self.curves[k],axis=0),axis=1)
            if u==0:
                nodes=self.curves[k].copy()
            else:
                seed=W+(1-u)*(self.curves[k]-self.restW)+u*self.fold_nodes[k]
                nodes=finger_ik(root,goal,lengths,seed)
            for i,suffix in enumerate(['','b','c']):
                rest_axis=self.curves[k][i+1]-self.curves[k][i]
                r=frame(nodes[i+1]-nodes[i],(1-u)*self.dorsal0+u*self.dorsal1)@frame(rest_axis,self.dorsal0).T
                data['wing_finger'+str(k+1)+suffix]=(r,nodes[i],1.)
        self.states[u]=data
        return data

    def maps(self,u,sgn):
        mirror=np.diag([sgn,1.,1.]);out={'chest':(np.eye(3),np.zeros(3)),'hips':(np.eye(3),np.zeros(3))}
        sd='L'if sgn>0 else'R'
        for name,(R,head,scale)in self.state(u).items():
            a,b=self.rest[name];axis=unit(b-a)
            linear=R@(np.eye(3)+(scale-1)*np.outer(axis,axis));offset=head-linear@a
            out[name+'.'+sd]=(mirror@linear@mirror,mirror@offset)
        return out

    def bones(self,sgn):
        m=np.array([sgn,1,1]);sd='L'if sgn>0 else'R'
        return [(n+'.'+sd,tuple(a*m),tuple(b*m),self.parent[n]+('.'+sd if self.parent[n]!='chest'else''))for n,(a,b)in self.rest.items()]

    def clip(self,u,sgn):
        m=np.diag([sgn,1.,1.]);sd='L'if sgn>0 else'R'
        return {name+'.'+sd:(m@R@m,m@head,scale)for name,(R,head,scale)in self.state(u).items()}

    def pieces(self,u,sgn):
        st=self.state(u);rh,E,_=st['wing_humerus'];rf,_,_=st['wing_forearm'];E=st['wing_forearm'][1];W=st['wing_carpal'][1]
        dh,df=rh@self.h,rf@self.f;rc=st['wing_carpal'][0];out=[];sd='L'if sgn>0 else'R'
        def bone(name,a,b,r,bn,k=.04):out.append(self.SK.Piece({'name':name,'from':a,'to':b,'r':r,'k':k,'rig':{bn+'.'+sd:1}},sgn,'bone'))
        def muscle(name,a,b,r,hint,rig,k=.055,endpoints=None):
            sp={'name':name,'from':a,'to':b,'radii':r,'hint':hint,'k':k,'rig':rig}
            if endpoints:sp['endpoint_rig']=endpoints
            out.append(self.SK.Piece(sp,sgn,'muscle'))
        bone('humerus',self.S,E,[.060,.052],'wing_humerus')
        bone('forearm',E,W,[.055,.040],'wing_forearm')
        bone('carpal saddle',W+df*self.C['carpal_span'][0],W+df*self.C['carpal_span'][1],self.C['carpal_radii'],'wing_forearm',self.C['carpal_blend'])
        anchor=self.S-dh*self.C['socket_half_span'][0];insertion=self.S+dh*self.C['socket_half_span'][1]
        muscle('deltoid',insertion,anchor,self.C['shoulder_radii'],rh@self.dorsal0,{'wing_humerus.'+sd:.5,'chest':.5},.075,{'from':'wing_humerus.'+sd,'to':'chest'})
        muscle('humeral head',self.S-dh*.02,self.S+dh*.08,[.10,.095],rh@np.array([0,1,0]),{'wing_humerus.'+sd:1},.06)
        muscle('upper arm',self.S+dh*.08,E-dh*.055,[.115,.105],rh@np.array([0,1,0]),{'wing_humerus.'+sd:1})
        muscle('forearm belly',E+df*.025,E+df*np.linalg.norm(W-E)*.48,[.082,.075],rf@np.array([0,1,0]),{'wing_forearm.'+sd:1})
        # Arm, metacarpals and phalanges are one smoothly united skin surface.
        for k,curve in enumerate(self.curves):
            for i,suffix in enumerate(['','b','c']):
                name='wing_finger'+str(k+1)+suffix;R,head,_=st[name]
                tip=head+R@(curve[i+1]-curve[i])
                radii=np.interp(self.knots[i:i+2],np.linspace(0,1,len(self.D['finger']['radius'])),self.D['finger']['radius'])
                bone('digit '+str(k)+' link '+str(i),head,tip,radii,name,self.D['finger']['union_blend'])
        Ra,A,scale=st['wing_elbowfinger']
        bone('elbow accessory',A,A+Ra@self.acc0*self.accL*scale,[.033,.012],'wing_elbowfinger',.023)
        return out


def blend_map(V,weights,maps):
    A=np.zeros((len(V),3,3));c=np.zeros_like(V)
    for i,w in enumerate(weights):
        for name,value in w:
            R,t=maps[name];A[i]+=R*value;c[i]+=t*value
    return A,c


def corrected_keys(H,obj,rest,weights,targets,rig,sgn):
    obj.shape_key_add(name='Basis',from_mix=False)
    for step,target in enumerate(targets,1):
        u=step/rig.C['pose_steps'];A,c=blend_map(rest,weights,rig.maps(u,sgn))
        if np.min(abs(np.linalg.det(A)))<1e-5:raise ValueError('singular wing skin blend')
        pre=np.linalg.solve(A,(target-c)[...,None])[...,0]
        key=obj.shape_key_add(name='wingFold'+str(step),from_mix=False)
        key.data.foreach_set('co',H.to_blender(pre).astype(np.float32).ravel())


def project_surface(P,parts,SK,iterations=7):
    P=P.copy();eps=.001
    for _ in range(iterations):
        d=SK.field(P,None,parts)
        g=np.column_stack([(SK.field(P+np.eye(3)[k]*eps,None,parts)-SK.field(P-np.eye(3)[k]*eps,None,parts))/(2*eps)for k in range(3)])
        P-=np.clip(d,-.035,.035)[:,None]*g/np.maximum((g*g).sum(1),.05)[:,None]
    return P


def surface_targets(B,rig,sgn,V,p0):
    SK=B.SK;D=np.array([p.sdf(V)for p in p0])
    influence=np.exp(-(D-D.min(0))/.022);influence/=influence.sum(0)
    nearest=np.argmin(D,axis=0);family=np.full(len(V),-1,int);distance=np.zeros(len(V))
    for index,piece in enumerate(p0):
        if not piece.name.startswith('digit '):continue
        _,k,_,j=piece.name.split();k,j=int(k),int(j);mask=nearest==index
        ls=np.linalg.norm(np.diff(rig.curves[k],axis=0),axis=1)
        family[mask]=k;distance[mask]=ls[:j].sum()+np.clip((V[mask]-piece.a)@piece.ax,0,piece.len)
    targets=[]
    for step in range(1,rig.C['pose_steps']+1):
        u=step/rig.C['pose_steps'];parts=rig.pieces(u,sgn);maps=rig.maps(u,sgn);target=np.zeros_like(V)
        for k,(a,b)in enumerate(zip(p0,parts)):
            if a.kind=='muscle':
                q=(V-a.c)@a.E.T/np.maximum(a.radii,1e-6);mapped=(q*b.radii)@b.E+b.c
            else:
                bone=max(a.rig,key=a.rig.get);R,t=maps[bone];mapped=V@R.T+t
            target+=mapped*influence[k,:,None]
        target=project_surface(target,parts,SK)
        # A folded neighbor must not capture another finger's surface. Global
        # union projection changes topology where slender rays approach each other.
        for k in range(4):
            domain=rig.C['deformation_domains'];start=domain['finger_start'];span=domain['finger_blend_length']
            mask=(family==k)&(distance>start)
            if not mask.any():continue
            indices=[i for i,p in enumerate(p0)if p.name.startswith('digit '+str(k)+' ')]
            share=np.exp(-(D[indices][:,mask]-D[indices][:,mask].min(0))/.012);share/=share.sum(0)
            local=np.zeros((mask.sum(),3))
            for weight,index in zip(share,indices):
                bone=max(p0[index].rig,key=p0[index].rig.get);R,t=maps[bone]
                local+=(V[mask]@R.T+t)*weight[:,None]
            local=project_surface(local,[parts[i]for i in indices],SK)
            blend=np.clip((distance[mask]-start)/span,0,1);blend=blend*blend*(3-2*blend)
            target[mask]=target[mask]*(1-blend[:,None])+local*blend[:,None]
        targets.append(target)
    return targets


def arm(B,rig,sgn):
    H,SK=B.H,B.SK;sd='L'if sgn>0 else'R';p0=rig.pieces(0,sgn)
    V,F=SK.mesh(None,p0,rig.D['anatomy']['resolution']);W=SK.piece_weights(V,p0)
    for i,weights in enumerate(W):
        a=dict(weights);wh=a.pop('wing_humerus.'+sd,0);wc=a.pop('chest',0);total=wh+wc
        if total>1e-9:
            u=3*wh/total;j=min(2,int(u));t=u-j;names=['chest','wing_socketBlend1.'+sd,'wing_socketBlend2.'+sd,'wing_humerus.'+sd]
            a[names[j]]=a.get(names[j],0)+total*(1-t);a[names[j+1]]=a.get(names[j+1],0)+total*t
        top=sorted(a.items(),key=lambda x:-x[1])[:4];s=sum(w for _,w in top);W[i]=[(n,w/s)for n,w in top if w>1e-9]
    E,Wrist=rig.restE*np.array([sgn,1,1]),rig.restW*np.array([sgn,1,1]);S=rig.S*np.array([sgn,1,1]);path=np.array([S,E,Wrist]);distances=np.linalg.norm(np.diff(path,axis=0),axis=1)
    along=[]
    D=np.array([p.sdf(V)for p in p0]);nearest=np.argmin(D,axis=0)
    finger_share=np.array([sum(w for n,w in weights if n.startswith('wing_finger') or n.startswith('wing_elbowfinger'))for weights in W])
    for index,p in enumerate(V):
        piece=p0[nearest[index]]
        if piece.name.startswith('digit '):
            _,k,_,i=piece.name.split();k,i=int(k),int(i)
            curve=rig.curves[k];ls=np.linalg.norm(np.diff(curve,axis=0),axis=1)
            t=np.clip((p-piece.a)@piece.ax/max(piece.len,1e-9),0,1)
            along.append(float(distances.sum()+ls[:i].sum()+t*ls[i]))
        else:
            candidates=[]
            for k in range(2):
                d=path[k+1]-path[k];t=np.clip((p-path[k])@d/(d@d),0,1);candidates.append((np.linalg.norm(p-path[k]-d*t),distances[:k].sum()+distances[k]*t))
            along.append(min(candidates)[1])
    skin=H.add_part('WingArm'+sd,V.tolist(),F.tolist(),{'_PART':[24]*len(V),'_A':along,'_B':np.clip(finger_share*2,0,1).tolist(),'_ZONE':[0]*len(V)},W)
    normals=SK.normals(V,F);ar=rig.D['armor']
    Z=SK.smooth_on_mesh(V,F,np.maximum((normals[:,1]<=ar['top_from']*2-1).astype(float),(finger_share>.32).astype(float)),iters=4)
    S,SF,src,ink,tint=SK.shell(V,F,Z,ar,SK.smooth_normals(V,F),np.array(along),np.zeros(len(V)),lambda x:np.asarray(x)/ar['band'])
    sw=[W[i]for i in src];shell=H.add_part('WingArmor'+sd,S.tolist(),SF.tolist(),{'_PART':[13]*len(S),'_A':list(ink),'_B':list(tint),'_ZONE':[0]*len(S)},sw)
    targets=surface_targets(B,rig,sgn,V,p0);shell_targets=[]
    for target in targets:
        n=SK.normals(target,F);old=normals[src];new=n[src];axis=np.cross(old,new);cos=np.clip((old*new).sum(1),-.98,1)
        offset=S-V[src];rotated=offset+np.cross(axis,offset)+np.cross(axis,np.cross(axis,offset))/np.maximum(1+cos,.02)[:,None]
        shell_targets.append(target[src]+rotated)
    corrected_keys(H,skin,V,W,targets,rig,sgn);corrected_keys(H,shell,S,sw,shell_targets,rig,sgn)
    return [skin,shell]


def curve_at(P,t):
    distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];distance/=distance[-1]
    return np.array([np.interp(t,distance,P[:,k])for k in range(3)])


def build(B,sgn):
    rig=Rig(B);H=B.H;sd='L'if sgn>0 else'R';m=np.array([sgn,1,1]);parts=arm(B,rig,sgn);bones=rig.bones(sgn)
    def claw(name,point,direction,length,radius,hook,bone):
        v,f= B.claw_tube(point,direction,length,radius,hook,down=np.array([0,-1.,0]));parts.append(H.add_part(name,v,f,{'_PART':[23]*len(v),'_A':[0]*len(v),'_B':[0]*len(v),'_ZONE':[0]*len(v)},[[(bone,1)]]*len(v)))
    # The wrist claw belongs to the carpal knuckle, never to a wing finger.
    c=rig.D['thumb']['claw'];claw('WingWristClaw'+sd,rig.rest_claw*m,rig.rest_claw_dir*m,c['length'],c['radius'],c['hook_deg'],'wing_wrist_claw.'+sd)
    accessory=np.array([rig.restE,rig.restE+rig.acc0*rig.accL]);accbone='wing_elbowfinger.'+sd
    ec=rig.D['elbow_finger']['claw'];claw('WingElbowClaw'+sd,accessory[-1]*m,rig.acc0*m,ec['length'],ec['radius'],ec['hook_deg'],'wing_elbowclaw.'+sd)
    # The single skin surface already includes all digits; these paths drive membranes.
    spars=[]
    armline=np.array([rig.restW,rig.restE,accessory[-1]])*m
    fe=np.linalg.norm(rig.restW-rig.restE)/(np.linalg.norm(rig.restW-rig.restE)+rig.accL)
    spars.append((armline,lambda t:'wing_forearm.'+sd if t<fe else accbone))
    for k,curve in enumerate(rig.curves):
        def bn(t,k=k):
            names=['wing_finger'+str(k+1)+suffix+'.'+sd for suffix in ['', 'b', 'c']]
            width=rig.C['finger_joint_blend']
            for i,knot in enumerate(rig.knots[1:-1]):
                if abs(t-knot)<width:
                    blend=(t-knot+width)/(2*width);blend=blend*blend*(3-2*blend)
                    return [(names[i],1-blend),(names[i+1],blend)]
            return names[0]if t<rig.knots[1]else(names[1]if t<rig.knots[2]else names[2])
        full=np.array([curve_at(curve,t)for t in np.linspace(0,1,16)])*m
        tip=curve[-1]*m;direction=unit((curve[-1]-curve[-2])*m);c=rig.D['claw'];claw('WingClaw'+str(k)+sd,tip,direction,c['length'],c['radius'],c['hook_deg'],bn(1))
        spars.append((full,bn))
    body=np.array([rig.S*m]+B.membrane_body_line(sgn));line=np.array([rig.S,rig.restE,accessory[-1]])*m
    fa=rig.Lh/(rig.Lh+rig.accL)
    pairs=[(spars[i],spars[i+1],False)for i in range(4)]+[((line,lambda t:'wing_humerus.'+sd if t<fa else accbone),(body,lambda t:'chest'if t<.5 else'hips'),True)]
    nu,nv=32,20
    for panel,(aa,bb,flank)in enumerate(pairs):
        PA,ba=aa;PB,bbone=bb;v=[];w=[];uv=[]
        for i in range(nu+1):
            for j in range(nv+1):
                u,q=i/nu,j/nv;v.append(curve_at(PA,u)*(1-q)+curve_at(PB,u)*q);selector=ba(u)if q<.5 else bbone(u)
                driver=selector if isinstance(selector,str)else max(selector,key=lambda x:x[1])[0]
                w.append([(driver,1)]);uv.append((u,q))
        v=np.array(v);faces=[]
        for i in range(nu):
            for j in range(nv):
                a=i*(nv+1)+j;faces.append([a,a+1,a+nv+2,a+nv+1]if sgn>0 else[a+nv+1,a+nv+2,a+1,a])
        targets=[]
        def target(amount):
            st=rig.state(amount);S=rig.S;E=st['wing_forearm'][1];Wrist=st['wing_carpal'][1]
            Ra,A,scale=st['wing_elbowfinger'];acc_tip=A+Ra@rig.acc0*rig.accL*scale
            posed=[np.array([Wrist,E,acc_tip])*m]
            for k,curve in enumerate(rig.curves):
                names=['wing_finger'+str(k+1)+suffix for suffix in ['', 'b', 'c']]
                nodes=[st[n][1]for n in names];R,h,_=st[names[-1]];nodes.append(h+R@(curve[-1]-curve[-2]))
                posed.append(np.array(nodes)*m)
            if flank:pa,pb=np.array([S,E,acc_tip])*m,body
            else:pa,pb=posed[panel],posed[panel+1]
            result=[]
            for u,q in uv:
                ue=u*(1-rig.D['membrane']['sag']*math.sin(math.pi*q))
                a=curve_at(pa,ue);b=curve_at(pb,ue)
                p=a*(1-q)+b*q;span=np.linalg.norm(b-a)
                # Sag is scaled by the available span; compressed panels gather in small outward pleats.
                sag=rig.D['membrane']['sag']*span*math.sin(math.pi*q)*math.sin(math.pi*u)
                p+=np.array([0,-1,0])*sag*(1-.7*amount)
                billow=(rig.D['spread']['billow']*(1-amount)+rig.D['membrane']['pleats']['depth']*amount*math.cos(6*math.pi*q))*math.sin(math.pi*q)*math.sin(math.pi*u)
                p+=np.array([sgn,0,0])*billow
                result.append(p)
            return np.array(result)
        rest=target(0)
        for step in range(1,rig.C['pose_steps']+1):targets.append(target(step/rig.C['pose_steps']))
        obj=H.add_part('WingMembrane'+str(panel)+sd,rest.tolist(),faces,{'_PART':[25]*len(rest),'_A':[x[0]for x in uv],'_B':[x[1]for x in uv],'_ZONE':[0]*len(rest)},w)
        corrected_keys(H,obj,rest,w,targets,rig,sgn);parts.append(obj)
    return parts,bones,rig.clip(1,sgn)


def fold_clip(B):
    rig=Rig(B);samples=[]
    for u in np.linspace(0,1,rig.C['pose_steps']+1):
        pose={}
        for sgn in [1,-1]:pose.update(rig.clip(float(u),sgn))
        samples.append((float(u),pose))
    return {'__samples__':samples}
