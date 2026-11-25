"""Adds Turkish strings (tr.json) to resources.arsc: a values-tr type chunk + string pool entries."""
import json, struct
U = struct.unpack_from
P = struct.pack


def add_turkish(d, path):
    J = json.load(open(path, encoding="utf-8"))
    S = {int(i, 16): t for i, t in J["strings"].items()}
    L = {int(i, 16): t for i, t in J["plurals"].items()}
    t,h,sz=U('<HHI',d,0); assert t==2 and sz==len(d)
    pos=h; chunks=[]
    while pos<sz:
        ct,ch,cs=U('<HHI',d,pos); chunks.append((ct,ch,d[pos:pos+cs])); pos+=cs

    pool=[c for c in chunks if c[0]==1][0][2]; pkgs=[c for c in chunks if c[0]==0x200]; assert len(pkgs)==1
    ph=U('<H',pool,2)[0]; n,sc,fl,so,st=U('<IIIII',pool,8); utf8=bool(fl&0x100)
    new=[]; idx={}
    def sid(s):
        if s not in idx: idx[s]=n+len(new); new.append(s)
        return idx[s]
    def l8(x): return bytes([x]) if x<0x80 else bytes([0x80|x>>8,x&0xff])
    def l16(x): return P('<H',x) if x<0x8000 else P('<HH',0x8000|x>>16,x&0xffff)
    def encs(s):
        u=s.encode('utf-16-le')
        if utf8: b=s.encode(); return l8(len(u)//2)+l8(len(b))+b+b'\0'
        return l16(len(u)//2)+u+b'\0\0'
    pk=pkgs[0][2]; pkh=U('<H',pk,2)[0]; parts=[]; pos=pkh
    while pos<len(pk):
        ct,ch,cs=U('<HHI',pk,pos); parts.append([ct,ch,pk[pos:pos+cs]]); pos+=cs
    tn=U('<I',pk,268)[0]
    # tip adlari: kimligin ust bayti
    def key(tid,ei):
        for ct,ch,b in parts:
            if ct==0x201 and b[8]==tid:
                f=b[9]; ec,es=U('<II',b,12)
                if f&1:
                    for k in range(ec):
                        a,o=U('<HH',b,ch+4*k)
                        if a==ei: o*=4; break
                    else: continue
                elif f&2:
                    if ei>=ec: continue
                    o=U('<H',b,ch+2*ei)[0]
                    if o==0xffff: continue
                    o*=4
                else:
                    if ei>=ec: continue
                    o=U('<I',b,ch+4*ei)[0]
                    if o==0xffffffff: continue
                s,fl2,k=U('<HHI',b,es+o)
                return s if fl2&8 else k
        raise SystemExit('anahtar yok %x %x'%(tid,ei))
    def add(tid,ent,bag):
        sp=[i for i,p in enumerate(parts) if p[0]==0x202 and p[2][8]==tid]; assert len(sp)==1
        spec=bytearray(parts[sp[0]][2]); ec=U('<I',spec,12)[0]; sh=parts[sp[0]][1]
        tys=[i for i,p in enumerate(parts) if p[0]==0x201 and p[2][8]==tid]
        m=U('<H',spec,10)[0]
        if m: struct.pack_into('<H',spec,10,m+1)
        for i in ent: o=sh+4*(i&0xffff); struct.pack_into('<I',spec,o,U('<I',spec,o)[0]|4)
        parts[sp[0]][2]=bytes(spec)
        th=parts[tys[0]][1]; cfgsz=U('<I',parts[tys[0]][2],20)[0]; cfg=bytearray(cfgsz); struct.pack_into('<I',cfg,0,cfgsz); cfg[8:10]=b'tr'
        for i in tys:
            c=parts[i][2][20:20+U('<I',parts[i][2],20)[0]]; assert c[8:10]!=b'tr','tr zaten var'
        off=[0xffffffff]*ec; body=b''
        for i in sorted(ent):
            e=i&0xffff; off[e]=len(body); k=key(tid,e)
            if bag:
                mm=sorted(({'other':0x01000004,'zero':0x01000005,'one':0x01000006,'two':0x01000007,'few':0x01000008,'many':0x01000009}[q],sid(v)) for q,v in ent[i].items())
                body+=P('<HHIII',16,1,k,0,len(mm))+b''.join(P('<IHBBI',a,8,0,3,s) for a,s in mm)
            else: body+=P('<HHI',8,0,k)+P('<HBBI',8,0,3,sid(ent[i]))
        hl=20+cfgsz; assert th==hl,(th,hl); es=hl+4*ec
        ch=P('<HHIBBHII',0x201,hl,es+len(body),tid,0,0,ec,es)+bytes(cfg)+P('<%dI'%ec,*off)+body
        parts.insert(tys[-1]+1,[0x201,hl,ch])
    tidS={i>>16&0xff for i in S}; tidL={i>>16&0xff for i in L}; assert len(tidS)==len(tidL)==1
    add(tidS.pop(),S,False); add(tidL.pop(),L,True)
    pk2=bytearray(pk[:pkh])+b''.join(p[2] for p in parts); struct.pack_into('<I',pk2,4,len(pk2))
    # paket ici havuz konumlari degismez (tip/anahtar havuzlari basta)
    ks=U('<I',pk,276)[0]; assert U('<H',pk2,tn)[0]==1 and U('<H',pk2,ks)[0]==1
    # dizge havuzu
    offs=list(U('<%dI'%n,pool,ph)); sto=U('<%dI'%sc,pool,ph+4*n) if sc else ()
    sdata=pool[so:(st if sc else len(pool))]; stdata=pool[st:] if sc else b''
    add_=b''; no=[]
    base=len(sdata)
    for s in new: no.append(base+len(add_)); add_+=encs(s)
    sdata2=sdata+add_; sdata2+=b'\0'*(-len(sdata2)%4)
    nn=n+len(new); so2=ph+4*nn+4*sc; st2=so2+len(sdata2) if sc else 0
    pool2=P('<HHIIIIII',1,ph,0,nn,sc,fl&~1,so2,st2)+pool[28:ph]+P('<%dI'%nn,*offs,*no)+P('<%dI'%sc,*sto)+sdata2+stdata
    pool2=pool2[:4]+P('<I',len(pool2))+pool2[8:]
    out=b''.join(pool2 if c[0]==1 else bytes(pk2) if c[0]==0x200 else c[2] for c in chunks)
    out=bytearray(d[:h])+out; struct.pack_into('<I',out,4,len(out)); return bytes(out)


