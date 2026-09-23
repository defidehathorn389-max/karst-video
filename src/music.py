import numpy as np, json, wave
SR=32000
M=json.load(open('audio_map.json')); T=M['total']
N=int(T*SR)
out=np.zeros((N,2),np.float32)
def hz(m): return 440*2**((m-69)/12)
# chord progression (D minor-ish, cinematic): Dm - Bb - F - C
chords=[[50,57,62,65],[46,53,58,62],[41,53,57,60],[48,55,60,64]]
CL=10.0
rng=np.random.default_rng(1)
# pad
for ci in range(int(T/CL)+2):
    ch=chords[ci%4]; s0=int(ci*CL*SR); L=int((CL+4)*SR)
    s1=min(N,s0+L)
    if s0>=N: break
    tt=np.arange(s1-s0)/SR
    env=np.minimum(1,tt/3)*np.minimum(1,np.maximum(0,(CL+4-tt)/4))
    for m in ch:
        for det,pan in ((-0.12,0.3),(0.12,0.7)):
            f=hz(m)*2**(det/12/10)
            w=np.sin(2*np.pi*f*tt+0.3*np.sin(2*np.pi*0.2*tt))*0.6+np.sin(2*np.pi*2*f*tt)*0.15
            v=(w*env*0.018).astype(np.float32)
            out[s0:s1,0]+=v*(1-pan); out[s0:s1,1]+=v*pan
    # sub bass
    f=hz(ch[0]-12); v=np.sin(2*np.pi*f*tt)*env*0.05
    out[s0:s1]+=v[:,None].astype(np.float32)
# piano-like plucks (arpeggio notes)
scale=[62,64,65,67,69,72,74,77]
bt=0.0
while bt<T-3:
    ci=int(bt/CL)%4; ch=chords[ci]
    pool=[n+12 for n in ch]+[ch[1]+24]
    m=pool[rng.integers(len(pool))]
    s0=int(bt*SR); L=int(3.5*SR); s1=min(N,s0+L); tt=np.arange(s1-s0)/SR
    f=hz(m)
    w=(np.sin(2*np.pi*f*tt)+0.4*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*3)+0.15*np.sin(2*np.pi*3*f*tt)*np.exp(-tt*5))
    env=np.exp(-tt*1.4)*np.minimum(1,tt/0.005)
    v=(w*env*0.05).astype(np.float32); pan=rng.uniform(0.3,0.7)
    out[s0:s1,0]+=v*(1-pan); out[s0:s1,1]+=v*pan
    bt+=rng.choice([1.25,2.5,2.5,1.25,3.75])
# simple reverb: multi-tap delay
for i0 in range(0,N,SR*10):
    tt=(np.arange(i0,min(N,i0+SR*10))/SR).astype(np.float32)
    out[i0:i0+len(tt)]*=(np.minimum(1,tt/3)*np.minimum(1,np.maximum(0,(T-tt)/4)))[:,None]
out/=np.abs(out).max()/0.7
out*=32767; pcm=out.astype(np.int16); del out
w=wave.open('audio/music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('ok',T)
