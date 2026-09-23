import requests, json, sys, os
S=requests.Session(); S.headers['User-Agent']='KarstEduVideo/1.0 (educational)'
queries={'guilin':'Li River Guilin karst','yangshuo':'Yangshuo karst landscape','stoneforest':'Stone Forest Shilin Yunnan','libo':'Libo karst Guizhou','wulong':'Wulong karst natural bridge','xiaozhai':'Xiaozhai Tiankeng','cave':'Reed Flute Cave','stalactite':'stalactites cave China','fengcong':'Bama karst Guangxi','fengcong2':'karst peaks Guizhou','rockdesert':'karst bare rock desertification','coral':'coral reef','libo2':'Xiaoqikong Libo','limestone':'limestone fossils'}
credits=[]
for k,q in queries.items():
    import time
    for _ in range(4):
      try:
        r=S.get('https://commons.wikimedia.org/w/api.php',params=dict(action='query',generator='search',gsrsearch=q+' filetype:bitmap',gsrnamespace=6,gsrlimit=8,prop='imageinfo',iiprop='url|size|extmetadata',iiurlwidth=1920,format='json'),timeout=30).json(); break
      except Exception: time.sleep(5)
    else: continue
    pages=sorted(r.get('query',{}).get('pages',{}).values(),key=lambda p:p.get('index',99))
    n=0
    for p in pages:
        ii=p['imageinfo'][0]; m=ii.get('extmetadata',{})
        lic=m.get('LicenseShortName',{}).get('value','')
        if ii['width']<1400 or ii['width']<ii['height']: continue
        if not any(x in lic for x in ['CC','Public','PD']) or 'NC' in lic or 'ND' in lic: continue
        fn=f'img/{k}_{n}.jpg'
        d=S.get(ii['thumburl'],timeout=60).content
        open(fn,'wb').write(d)
        import re
        art=re.sub('<[^>]+>','',m.get('Artist',{}).get('value','unknown')).strip()
        credits.append(f"{fn}\t{p['title']}\t{art}\t{lic}")
        n+=1
        time.sleep(1)
        if n>=3: break
    print(k,n,flush=True)
open('credits.tsv','w').write('\n'.join(credits))
