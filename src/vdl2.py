import json, subprocess, os, time, urllib.parse
S=json.load(open('vsel.json'))
for i,(w,v) in enumerate(S.items()):
    out=f'vraw/{i:02d}.webm'
    if os.path.exists(out) and os.path.getsize(out)>500000: continue
    url=v['url'].split('?')[0]
    p=url.split('/commons/')[1]            # a/ab/Name.webm
    name=p.split('/')[-1]
    cands=[f'https://upload.wikimedia.org/wikipedia/commons/transcoded/{p}/{name}.1080p.vp9.webm',
           f'https://upload.wikimedia.org/wikipedia/commons/transcoded/{p}/{name}.720p.vp9.webm',
           f'https://upload.wikimedia.org/wikipedia/commons/transcoded/{p}/{name}.720p.webm']
    ok=False
    for c in cands:
        for attempt in range(3):
            subprocess.run(['curl','-sL','-A','KarstEduVideo/1.0 (https://github.com/defidehathorn389-max/karst-video; educational)','--max-time','300','-r','0-60000000','-o',out,c])
            if os.path.exists(out) and os.path.getsize(out)>500000 and not open(out,'rb').read(15).startswith(b'<!'):
                ok=True; break
            time.sleep(8*(attempt+1))
        if ok: break
    print(i,w,'OK' if ok else 'FAIL',os.path.getsize(out)//1000000 if ok else 0,flush=True)
    if not ok and os.path.exists(out): os.remove(out)
    time.sleep(4)
