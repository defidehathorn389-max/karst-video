import json, subprocess, glob
FF='/usr/local/lib/python3.13/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
# name: (src idx, start, src_len, out_len)
C={'kostivere':(1,2,6,5.6),'halong':(11,0,6,4.6),'halong_boat':(13,1,6,5.6),'janicja_a':(3,62,4,4.1),'janicja_b':(3,70,4.5,4.6),
   'planina':(29,18,4,4.1),'coral':(6,2,7.6,7.6),'redsea':(8,3,6.6,6.6),'clouds':(27,2,6.5,6.4),'rain':(23,3,6.6,6.6),
   'monsoon':(28,3,6.6,6.6),'seep':(22,1,5.4,5.4),'rak':(30,10,6.6,6.6),'drip':(5,5,5.6,5.6),'forest':(9,0,4,5.1)}
for n,(i,s,L,out) in C.items():
    src=glob.glob(f'vraw/{i:02d}.*')[0]
    k=out/L
    vf=f"setpts={k:.4f}*(PTS-STARTPTS),scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,eq=saturation=1.05"
    r=subprocess.run([FF,'-y','-loglevel','error','-ss',str(s),'-t',str(L),'-i',src,'-an','-vf',vf,'-c:v','libx264','-preset','veryfast','-crf','16','-pix_fmt','yuv420p',f'clips/{n}.mp4'])
    d=subprocess.run([FF,'-i',f'clips/{n}.mp4'],capture_output=True,text=True).stderr.split('Duration: ')[1][:11]
    print(n,d,flush=True)
