# -*- coding: utf-8 -*-
"""KARST / FIELD NOTES — original editorial motion graphics for the v3 cut.
All artwork is constructed in vector Cairo from procedural geometry, geological
cross-sections, real-map vector data and hand-designed kinetic typography. No
third-party template or traced animation is used. Safe within the v2 timeline.
"""
import cairo, math, random
from functools import lru_cache

G = {}
W, H = 1920, 1080
INK = (.033, .067, .076)
DEEP = (.042, .088, .102)
PAPER = (.932, .903, .829)
BONE = (.778, .749, .657)
GOLD = (.86, .681, .409)
AQUA = (.395, .756, .752)
SEA = (.113, .355, .431)
SAGE = (.469, .619, .506)
RUST = (.766, .454, .338)
SOIL = (.43, .316, .221)
MUTED = (.564, .650, .637)


def install(namespace):
    global G
    G = namespace
    for name in ('anim_world', 'anim_china', 'anim_deposit', 'anim_plates',
                 'anim_fold', 'anim_chem', 'anim_rate', 'anim_evolve', 'anim_cave',
                 'anim_soil', 'anim_timeline', 'card_title', 'card_end',
                 'make_chapter', 'loc_tag'):
        namespace[name] = globals()[name]


def E(t, a, b): return G['seg'](t, a, b)
def M(a, b, u): return a + (b - a) * u

def C(c, rgb, alpha=1):
    c.set_source_rgba(rgb[0], rgb[1], rgb[2], max(0., min(1., alpha)))


def txt(c, s, x, y, size, col=PAPER, a=1, serif=False, bold=False,
        align='l', spacing=0, shadow=False):
    if a <= .001: return 0
    return G['text'](c, s, x, y, size, col, a, serif, bold, align, shadow, spacing)


def mono(c, s, x, y, sz=18, color=MUTED, a=1, align='l', track=2.5):
    if a <= .001: return
    c.select_font_face('DejaVu Sans Mono')
    c.set_font_size(sz)
    widths = [c.text_extents(ch).x_advance + track for ch in s]
    span = sum(widths) - track
    if align == 'c': x -= span/2
    elif align == 'r': x -= span
    C(c,color,a)
    for ch,wd in zip(s,widths):
        c.move_to(x,y); c.show_text(ch); x+=wd


def line(c, a, b, col=MUTED, alpha=1, w=1.5, dash=None):
    if alpha <= .001: return
    c.set_line_width(w); C(c,col,alpha)
    if dash: c.set_dash(dash)
    c.move_to(*a); c.line_to(*b); c.stroke()
    if dash: c.set_dash([])


def poly(c, pts, col, a=1):
    if not pts or a <= .001: return
    C(c,col,a); c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]
    c.close_path();c.fill()


def glow(c, x, y, r, color=GOLD, strength=.2):
    g=cairo.RadialGradient(x,y,1,x,y,r)
    g.add_color_stop_rgba(0,*color,strength)
    g.add_color_stop_rgba(.28,*color,strength*.26)
    g.add_color_stop_rgba(1,*color,0)
    c.set_source(g);c.arc(x,y,r,0,math.tau);c.fill()


def reg(c):
    # Discreet printing-house registration marks, not a visible boxed frame.
    for x,dx in ((55,1),(W-55,-1)):
        for y,dy in ((55,1),(H-55,-1)):
            line(c,(x,y),(x+dx*22,y),PAPER,.19,1)
            line(c,(x,y),(x,y+dy*22),PAPER,.19,1)


@lru_cache(maxsize=1)
def ground_ink():
    s=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
    z=cairo.Context(s)
    gr=cairo.LinearGradient(0,0,W,H)
    gr.add_color_stop_rgb(0,.023,.052,.064)
    gr.add_color_stop_rgb(.55,.055,.099,.110)
    gr.add_color_stop_rgb(1,.014,.035,.046)
    z.set_source(gr);z.paint()
    # Contour-like engravings sit at the periphery; the central composition breathes.
    z.set_line_width(1.1)
    for i in range(40):
        yy=-320+i*39
        a=.021 + .019*(i%5==0)
        C(z,MUTED,a)
        z.move_to(-40,yy)
        for xx in range(0,W+100,26):
            yy2=yy+32*math.sin(xx*.004+i*.33)+19*math.sin(xx*.014-i*.44)
            yy2+=15*math.exp(-((xx-1660)/300)**2)*math.sin(i*.45)
            z.line_to(xx,yy2)
        z.stroke()
    r=random.Random(87)
    for j in range(3900):
        x=r.randrange(W);y=r.randrange(H)
        C(z,PAPER,r.choice([.018,.024,.028,.036]));z.rectangle(x,y,1.1,1.1);z.fill()
    # A large, highly subdued illuminated area gives relief a cinematographic backdrop.
    gg=cairo.RadialGradient(950,590,20,950,590,920)
    gg.add_color_stop_rgba(0,.27,.42,.42,.07)
    gg.add_color_stop_rgba(1,.18,.28,.30,0)
    z.set_source(gg);z.paint()
    return s


def bg(c):
    c.set_source_surface(ground_ink(),0,0);c.paint();reg(c)


def mast(c, zh, en, t, D, n=''):
    a=E(t,.18,1.05)
    mono(c,'K A R S T   /   F I E L D  N O T E S',110,62,17,GOLD,.88*a,track=1.2)
    mono(c,(n+'  /  '+en).strip(' /'),1810,62,15,MUTED,.80*a,'r',1.2)
    line(c,(110,82),(1810,82),PAPER,.18*a,1)
    shift=18*(1-E(t,.25,1.35))
    line(c,(110,131-shift),(110,187-shift),GOLD,.94*a,3)
    txt(c,zh,137,177-shift,56,PAPER,a,serif=True,bold=False)
    mono(c,en,140,218-shift,18,GOLD,.88*a,track=2.3)
    # A tiny progressive rule reads as filmic motion without TV-style UI boxes.
    p=max(0,min(1,t/max(D,.01)))
    line(c,(110,931),(1810,931),PAPER,.15,1)
    line(c,(110,931),(110+1700*p,931),GOLD,.68,2)


def marker(c,x,y,n,zh,en,a=1,side=1):
    glow(c,x,y,48,GOLD,.12*a)
    C(c,GOLD,a);c.arc(x,y,5.5,0,math.tau);c.fill()
    C(c,GOLD,.5*a);c.set_line_width(1);c.arc(x,y,15,0,math.tau);c.stroke()
    ex=x+side*36
    line(c,(x+side*11,y),(ex,y),GOLD,.72*a,1)
    sx=ex+side*12
    mono(c,n,sx,y-13,16,GOLD,a,'l' if side>0 else 'r',1.2)
    txt(c,zh,sx,y+22,27,PAPER,a,serif=True,bold=True,align='l' if side>0 else 'r')
    mono(c,en,sx,y+48,12,MUTED,a,'l' if side>0 else 'r',.9)


def loc_tag(c,zh,en,a):
    if a<=.01:return
    # Photo/video geography label; on bright footage the soft scrim preserves legibility.
    gr=cairo.LinearGradient(42,0,640,0)
    gr.add_color_stop_rgba(0,0,0,0,.48*a)
    gr.add_color_stop_rgba(1,0,0,0,0)
    c.set_source(gr);c.rectangle(42,83,620,148);c.fill()
    line(c,(94,118),(94,177),GOLD,a,2.4)
    txt(c,zh,112,151,37,PAPER,a,serif=True,bold=False,shadow=True)
    mono(c,en,114,179,16,PAPER,.75*a,track=1.3)


def strands(c,x,y,t,cut=False):
    r=random.Random(39)
    for j in range(32):
        dx=(j-16)*13+r.uniform(-5,5)
        px=x+dx;py=y+r.uniform(-5,4)
        C(c,BONE,.18);c.set_line_width(r.uniform(.6,1.3))
        c.move_to(px,py)
        c.curve_to(px+5,py+12,px-7,py+25,px+4,py+36)
        c.stroke()


# ---------------------------------------------------------------- CARTOGRAPHY
@lru_cache(maxsize=3)
def map_surface(kind):
    s=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
    z=cairo.Context(s)
    if kind=='world':
        P=G['Proj'](-23,144,-7,69,box=(100,240,1720,640))
        land=G['WORLD']
    elif kind=='asia':
        P=G['Proj'](58,131,-4,48,box=(95,230,1720,660))
        land=G['WORLD']
    else:
        P=G['Proj'](95,116,20.4,34.5,box=(85,248,1210,615))
        land=G['PROV']
    # Land/water separation is intentionally subtle, reminiscent of an atlas plate.
    for pr,ps in land:
        G['poly_path'](z,P,ps)
        C(z,(.121,.203,.216),.87);z.fill_preserve()
        C(z,(.41,.57,.56),.31);z.set_line_width(1.05);z.stroke()
    return s,P


def grid_geo(c,P,lon_min,lon_max,lat_min,lat_max,step=10):
    for lat in range(math.ceil(lat_min/step)*step,lat_max+1,step):
        a,b=P(lon_min,lat);d,e=P(lon_max,lat)
        line(c,(a,b),(d,e),AQUA,.084,1,[2,11])
    for lon in range(math.ceil(lon_min/step)*step,lon_max+1,step):
        a,b=P(lon,lat_min);d,e=P(lon,lat_max)
        line(c,(a,b),(d,e),AQUA,.084,1,[2,11])


def anim_world(c,t,D):
    bg(c)
    _,P=map_surface('world')
    c.save();c.rectangle(50,234,1820,670);c.clip()
    grid_geo(c,P,-23,145,-7,70,20)
    c.set_source_surface(map_surface('world')[0]);c.paint()
    # Quiet region tint over Europe and SE Asia.
    sx,sy=P(14.7,45.8);cx,cy=P(106,27)
    glow(c,sx,sy,110,GOLD,.20)
    glow(c,cx,cy,220,AQUA,.13*E(t,4,D*.77))
    route=E(t,2.5,6.5)
    C(c,GOLD,.84);c.set_line_width(2.4)
    c.move_to(sx,sy)
    steps=max(1,int(100*route))
    for j in range(steps+1):
        u=j/100
        x=M(sx,cx,u)
        y=M(sy,cy,u)-200*math.sin(math.pi*u)
        c.line_to(x,y)
    c.stroke()
    for j in range(3):
        u=(route*.7-j*.16)%1
        if u>route: continue
        x=M(sx,cx,u);y=M(sy,cy,u)-200*math.sin(math.pi*u)
        glow(c,x,y,20,GOLD,.31)
        C(c,PAPER,.82);c.arc(x,y,2.9,0,math.tau);c.fill()
    c.restore()
    marker(c,sx,sy,'01','斯洛文尼亚 · Kras','46.0° N  /  14.8° E',E(t,1.0,2.3))
    marker(c,cx,cy,'02','中国南方','26.0° N  /  106° E',E(t,6.2,8.9),-1)
    mast(c,'一个名字，两片土地','THE JOURNEY OF A NAME',t,D,'01')
    mono(c,'EUROPE  →  EAST ASIA',1560,835,17,GOLD,E(t,3.0,4.0),'r',1.4)


def anim_china(c,t,D):
    bg(c)
    S,P=map_surface('china')
    c.save();c.rectangle(64,245,1240,655);c.clip()
    grid_geo(c,P,96,116,20,35,5)
    c.set_source_surface(S,0,0);c.paint()
    zones=[('53',2),('52',4.0),('45',5.3),('50',6.5)]
    for pr,ps in G['PROV']:
        for pid,delay in zones:
            if pr.get('id')==pid:
                a=E(t,delay,delay+1.8)
                G['poly_path'](c,P,ps)
                C(c,GOLD,.19*a);c.fill_preserve()
                C(c,GOLD,.87*a);c.set_line_width(2.1);c.stroke()
    # Bespoke leader positions: Guangxi, Guizhou and Chongqing are close enough
    # that labels tied directly to their pins collide at 1080p.
    cities=[('石林',103.32,24.8,6.8,-88,-35),
            ('荔波',107.9,25.4,8.1,-82,77),
            ('武隆',107.76,29.33,10.3,34,-32),
            ('桂林',110.29,25.27,12.0,46,-12)]
    for zh,lo,la,st,dx,dy in cities:
        a=E(t,st,st+.8)
        if a>.01:
            x,y=P(lo,la)
            glow(c,x,y,37,AQUA,.12*a)
            C(c,AQUA,a);c.arc(x,y,4.3,0,math.tau);c.fill()
            lx,ly=x+dx,y+dy
            line(c,(x,y),(lx,ly),AQUA,.67*a,1)
            side=1 if dx>0 else -1
            txt(c,zh,lx+side*7,ly-7,26,PAPER,a,serif=True,align='l' if side==1 else 'r')
    c.restore()
    mast(c,'中国南方喀斯特','AN ATLAS OF SOUTH CHINA',t,D,'02')
    line(c,(1330,315),(1330,850),GOLD,.65,2)
    a=E(t,4.5,6.2)
    mono(c,'SOUTHWEST CHINA',1372,371,18,GOLD,a,track=2)
    txt(c,'云南 · 贵州 · 广西',1370,425,34,PAPER,a,serif=True)
    txt(c,'及周边地区',1370,468,31,PAPER,a,serif=True)
    b=E(t,9.0,10.5)
    line(c,(1370,532),(1784,532),PAPER,.31*b,1)
    txt(c,'> 50',1362,667,118,GOLD,b,serif=True,bold=True)
    txt(c,'万 km²',1604,665,37,PAPER,b)
    mono(c,'EXPOSED KARST  /  APPROX.',1372,710,16,MUTED,b,track=1)
    mono(c,'PROVINCES + SITES SHOWN',1372,835,14,MUTED,E(t,12,13.4),track=.6)
    mono(c,'MAPPED FROM OPEN GEOJSON BOUNDARIES',105,890,13,MUTED,.66,'l',.6)


# ---------------------------------------------------------------- ANCIENT SEA / SEDIMENTS
def coral_branch(c,x,y,length,ang,depth,alpha=.78):
    if depth<=0 or length<5:return
    ex=x+math.cos(ang)*length;ey=y+math.sin(ang)*length
    C(c,RUST,alpha);c.set_line_width(max(1.3,depth*1.25));c.set_line_cap(cairo.LINE_CAP_ROUND)
    c.move_to(x,y);c.curve_to(M(x,ex,.4)+4,y-length*.4,M(x,ex,.7),M(y,ey,.7),ex,ey);c.stroke()
    if depth>1:
        coral_branch(c,ex,ey,length*.71,ang-.48,depth-1,alpha*.94)
        coral_branch(c,ex,ey,length*.64,ang+.51,depth-1,alpha*.92)


def anim_deposit(c,t,D):
    bg(c)
    # Immersive shelf: deep water at the far right, the stratigraphic core at left.
    g=cairo.LinearGradient(0,225,0,935)
    g.add_color_stop_rgba(0,.15,.42,.46,.47)
    g.add_color_stop_rgba(1,.029,.11,.16,.60)
    c.set_source(g);c.rectangle(92,245,1700,665);c.fill()
    for i in range(10):
        x=170+i*170+20*math.sin(t*.23+i)
        C(c,PAPER,.022);c.move_to(x,260);c.line_to(x+46,260)
        c.line_to(x+230,915);c.line_to(x+110,915);c.close_path();c.fill()
    prog=E(t,1.4,D*.90)
    x0,x1=135,1300
    top=874-prog*420
    step=28
    # Layer tops grow organically. Graded bands, thin etched laminations and fossils.
    for j in range(16):
        yy=874-j*step
        if yy<top:break
        upper=max(top,yy-step)
        v=.063*math.sin(j*3.4)
        band=(BONE[0]+v,BONE[1]+v*.8,BONE[2]+v*.7)
        path=[]
        for x in range(x0,x1+1,18):
            u=(x-x0)/(x1-x0)
            path.append((x,upper+3*math.sin(6*u+j*.43)))
        poly(c,path+[(x1,yy),(x0,yy)],band,.95)
        line(c,(x0,yy),(x1,yy),INK,.22,1.1)
        # Not every bed has fossils; signs of life accumulate irregularly.
        r=random.Random(j*19+3)
        for k in range(9):
            fx=r.uniform(x0+20,x1-20);fy=yy-r.uniform(5,22)
            if fy<top+4:continue
            C(c,INK,.24)
            c.set_line_width(1.15)
            c.arc(fx,fy,r.uniform(2,5),.6,3.4);c.stroke()
    # Thin dark base suggests the formation continues below the page.
    gr=cairo.LinearGradient(0,874,0,920)
    gr.add_color_stop_rgb(0,.19,.22,.20);gr.add_color_stop_rgb(1,.08,.12,.14)
    c.set_source(gr);c.rectangle(x0,874,x1-x0,47);c.fill()
    for j in range(11):
        bx=x0+52+j*105
        coral_branch(c,bx,top-2,29+8*(j%3),-math.pi/2+.1*math.sin(j),4,
                     .63*E(t,1,3))
    # Falling calcite specks: light, sparse and deterministic.
    r=random.Random(25)
    for j in range(96):
        px=r.uniform(125,1310); sp=r.uniform(31,81)
        py=250+((t*sp+r.uniform(0,790))%max(80,top-250))
        C(c,PAPER,r.uniform(.22,.62))
        c.arc(px+5*math.sin(t*.45+j),py,r.uniform(1,2.2),0,math.tau);c.fill()
    # Submerged horizontal strata readout.
    line(c,(128,top),(1314,top),PAPER,.56,1.2)
    marker(c,1130,top-62,'01','碳酸盐沉积','MARINE SEDIMENT',E(t,7,9),-1)
    mast(c,'远古海洋的馈赠','MARINE CARBONATE DEPOSITION',t,D,'03')
    a=E(t,2.0,4.0)
    mono(c,'GEOLOGICAL TIME',1380,344,17,GOLD,a,track=2)
    line(c,(1380,367),(1775,367),PAPER,.25*a,1)
    txt(c,f'{M(5.4,2.5,prog):.1f}',1372,510,124,PAPER,a,serif=True,bold=False)
    txt(c,'亿年前',1605,507,33,GOLD,a,serif=True)
    mono(c,'ANCIENT SHALLOW SEA',1380,590,16,MUTED,a,track=1)
    b=E(t,11,13)
    line(c,(1380,639),(1780,639),PAPER,.28*b,1)
    txt(c,'生命的残骸',1380,697,36,PAPER,b,serif=True)
    txt(c,'压实  ·  胶结  ·  成岩',1380,749,28,BONE,b)
    mono(c,'CaCO3  /  CARBONATE ROCK',1380,812,15,AQUA,b,track=1)

# ---------------------------------------------------------------- UPLIFT / FOLDING
def anim_plates(c,t,D):
    bg(c)
    _,P=map_surface('asia')
    c.save();c.rectangle(80,240,1760,670);c.clip()
    grid_geo(c,P,58,132,-4,48,10)
    c.set_source_surface(map_surface('asia')[0]);c.paint()
    # Motion, not a claim about a plate boundary coinciding with a national border.
    travel=E(t,1.1,D*.62)
    ilat=M(-13,0,travel)
    shape=[(67,-5+ilat),(83,-8+ilat),(93,5+ilat),(90,24+ilat),
           (81,31+ilat),(72,23+ilat),(69,14+ilat)]
    pts=[P(*u) for u in shape]
    poly(c,pts,RUST,.21)
    C(c,RUST,.71);c.set_line_width(2.2)
    c.move_to(*pts[0]);[c.line_to(*z) for z in pts[1:]];c.close_path();c.stroke()
    ix,iy=P(77,14+ilat)
    glow(c,ix,iy,130,RUST,.10)
    # Collision seam appears as a hairline of light before the plateau lifts.
    y0=P(80,32)[1]
    a=E(t,D*.35,D*.60)
    C(c,GOLD,.6*a);c.set_line_width(2)
    for j in range(61):
        lon=70+j*.50
        x,y=P(lon,31.1+2.7*math.sin(j*.052)+.30*math.sin(j*.8))
        if j==0:c.move_to(x,y)
        else:c.line_to(x,y)
    c.stroke()
    xg,yg=P(87,31)
    glow(c,xg,yg,310,GOLD,.28*a)
    # A fan of very fine relief lines on the Tibetan Plateau; elevation is symbolic.
    for j in range(7):
        yy=yg-35-j*17
        C(c,PAPER,.11*a);c.set_line_width(.95)
        c.move_to(xg-260,yy+20)
        for xx in range(-240,350,16):
            c.line_to(xg+xx,yy-23*math.sin((xx+240)/590*math.pi)+4*math.sin(xx*.052+j))
        c.stroke()
    k=E(t,D*.65,D*.86)
    ux,uy=P(104,27)
    glow(c,ux,uy,115,GOLD,.24*k)
    marker(c,ux,uy,'02','云贵高原','YUNNAN–GUIZHOU PLATEAU',k,1)
    c.restore()
    mast(c,'大地抬升','TECTONIC UPLIFT',t,D,'04')
    # Map labels deliberately outside the map's busiest points.
    ax,ay=P(79,13+ilat)
    txt(c,'印度板块',ax,ay+135,34,PAPER,E(t,.9,2),serif=True,align='c')
    tx,ty=P(113,39)
    txt(c,'欧亚板块',tx,ty,34,PAPER,.85,serif=True,align='c')
    mono(c,'SCHEMATIC PLATE MOTION   /   NOT TO SCALE',138,871,15,MUTED,.75,track=1)
    mono(c,'NORTHWARD COLLISION',1780,870,16,GOLD,E(t,5,7),'r',1.5)


def anim_fold(c,t,D):
    bg(c)
    rise=E(t,.7,D*.49)
    bend=E(t,2.0,D*.60)
    fracture=E(t,D*.52,D*.91)
    x0,x1=92,1824
    def h(x,depth=0):
        u=(x-x0)/(x1-x0)
        hills=108*math.sin(u*math.pi)+75*math.exp(-((u-.67)/.14)**2)
        hills+=29*math.sin(u*4*math.pi+.4)
        return 771-218*rise-bend*hills+depth*33
    # A receding sea retreats as the strata rises through it.
    sea_y=M(625,888,rise)
    gr=cairo.LinearGradient(0,320,0,940)
    gr.add_color_stop_rgba(0,.19,.47,.51,.32*(1-rise*.5))
    gr.add_color_stop_rgba(1,.05,.19,.25,.65*(1-rise*.5))
    c.set_source(gr);c.rectangle(x0,sea_y,x1-x0,936-sea_y);c.fill()
    line(c,(x0,sea_y),(x1,sea_y),AQUA,.50*(1-rise*.70),1.3)
    # Sedimentary bands with slow oscillating folds and naturally etched boundaries.
    for i in reversed(range(12)):
        pts_top=[(x,h(x,i)) for x in range(x0,x1+1,12)]
        pts_btm=[(x,h(x,i+1)) for x in range(x1,x0-1,-12)]
        v=.058*math.sin(i*2.4)
        color=(.66+v,.63+v*.95,.55+v*.7)
        poly(c,pts_top+pts_btm,color,.94)
        C(c,INK,.25);c.set_line_width(1.0);c.move_to(*pts_top[0])
        [c.line_to(*u) for u in pts_top[1:]];c.stroke()
    # The dark substratum isolates the geological slice from the background.
    pts=[(x,h(x,12)) for x in range(x0,x1+1,14)]
    poly(c,pts+[(x1,916),(x0,916)],(.21,.236,.226),.99)
    # Stratigraphic hatching and bedding dip measurements.
    for j in range(120):
        rr=random.Random(3*j+16)
        x=rr.uniform(x0+18,x1-20)
        d=rr.randint(1,10)
        yy=h(x,d)+rr.uniform(2,22)
        line(c,(x,yy),(x+rr.uniform(8,27),yy-1),INK,.23,rr.uniform(.8,1.2))
    # Hairline joints travel from exposed rock into the body of the limestone.
    for j in range(17):
        rr=random.Random(j*44+10)
        sx=x0+70+j*100+rr.uniform(-28,28)
        uy=frac=E(t,D*.51+j*.085,D*.58+j*.085)
        if frac<=0:continue
        top=h(sx,0)
        dep=(100+rr.uniform(20,180))*frac
        x=sx
        C(c,INK,.80*frac);c.set_line_width(2)
        c.move_to(x,top)
        for k in range(5):
            x+=rr.uniform(-15,15)
            c.line_to(x,top+dep*(k+1)/5)
        c.stroke()
        if j in (5,10):
            glow(c,sx,top+35,34,AQUA,.08*frac)
    mast(c,'挤压 · 弯曲 · 断裂','FOLDING / JOINTING',t,D,'05')
    for i,(word,en,at) in enumerate([('海底','SUBMERGED',0),('抬升','UPLIFT',D*.29),('裂隙','JOINTS',D*.69)]):
        a=E(t,at,at+1.2)
        x=150+i*223
        line(c,(x,833),(x+174,833),GOLD,.46*a,1.5)
        mono(c,f'{i+1:02d} / {en}',x,857,15,GOLD,a,track=.9)
        txt(c,word,x,899,27,PAPER,a,serif=True)
    a=E(t,D*.65,D*.83)
    line(c,(1175,485),(1350,395),GOLD,.70*a,1.2)
    C(c,GOLD,a);c.arc(1175,485,4,0,math.tau);c.fill()
    txt(c,'裂隙为水开辟道路',1366,401,30,PAPER,a,serif=True)
    mono(c,'LIMESTONE / BEDDED CARBONATES',1750,883,14,MUTED,.67,'r',.9)


# ---------------------------------------------------------------- CHEMISTRY / RAIN
CHEM1='H2O + CO2  →  H2CO3'
CHEM2='CaCO3 + H2CO3  →  Ca(HCO3)2'

def anim_chem(c,t,D):
    bg(c)
    x0,x1=110,1025
    y0=440
    # Pale sky above a softly lit root-rich soil.
    gg=cairo.LinearGradient(0,300,0,915)
    gg.add_color_stop_rgba(0,.16,.28,.31,.37)
    gg.add_color_stop_rgba(.3,.09,.19,.22,.46)
    gg.add_color_stop_rgba(1,.08,.11,.12,.56)
    c.set_source(gg);c.rectangle(x0,300,x1-x0,605);c.fill()
    # Groundcover outline is not cartoon trees. Many slender stalks read at a distance.
    r=random.Random(41)
    for i in range(86):
        px=x0+14+i*(x1-x0-32)/86+r.uniform(-5,5)
        ht=r.uniform(12,32)
        C(c,SAGE,.29);c.set_line_width(1.35)
        c.move_to(px,y0);c.curve_to(px-8,y0-ht*.4,px+5,y0-ht*.8,px-3,y0-ht);c.stroke()
    # Soil horizon and a nonuniform limestone face with real bedding texture.
    gr=cairo.LinearGradient(0,440,0,625)
    gr.add_color_stop_rgb(0,.46,.34,.26);gr.add_color_stop_rgb(1,.30,.245,.20)
    c.set_source(gr);c.rectangle(x0,440,x1-x0,170);c.fill()
    gr=cairo.LinearGradient(x0,610,x1,910)
    gr.add_color_stop_rgb(0,.72,.70,.64)
    gr.add_color_stop_rgb(.53,.55,.56,.52)
    gr.add_color_stop_rgb(1,.38,.43,.41)
    c.set_source(gr);c.rectangle(x0,610,x1-x0,304);c.fill()
    # Limestone is laminated; scattered specks and eroded shell arcs are restrained.
    for j in range(11):
        yy=619+j*28
        line(c,(x0,yy+3*math.sin(j)),(x1,yy-2*math.sin(j+.2)),INK,.24,1.05)
    r=random.Random(13)
    for j in range(550):
        x=r.uniform(x0,x1);y=r.uniform(610,908)
        C(c,INK,r.uniform(.055,.19));c.rectangle(x,y,r.uniform(.5,2.2),1);c.fill()
    # Fine roots, into which the water dissolves CO2.
    for j in range(14):
        xx=x0+44+j*67
        C(c,INK,.42);c.set_line_width(1.3)
        c.move_to(xx,y0)
        c.curve_to(xx-15,493,xx+19,558,xx-10,602);c.stroke()
        line(c,(xx+1,532),(xx+32,572),INK,.35,1.0)
    line(c,(x0,440),(x1,440),SAGE,.81,2)
    line(c,(x0,610),(x1,610),INK,.39,1.5)
    # Widening fissures have irregular, shaded edges and discrete flowing packets.
    grow=E(t,D*.33,D*.92)
    for j,(sx,tilt) in enumerate(((310,1),(558,-1),(810,1))):
        gap=4+grow*(7+j*3)
        left=[(sx-gap*.5,y0+120)]
        right=[(sx+gap*.5,y0+120)]
        for h in range(0,9):
            yy=565+h*43
            bx=sx+tilt*math.sin(h*.86+j)*19+2*h
            left.append((bx-gap*(.5+.15*math.sin(h)),yy))
            right.append((bx+gap*(.5+.15*math.sin(h)),yy))
        poly(c,left+right[::-1],INK,.92)
        C(c,AQUA,.43+.25*grow);c.set_line_width(2)
        c.move_to(sx,y0+122)
        for h in range(9):
            yy=565+h*43
            bx=sx+tilt*math.sin(h*.86+j)*19+2*h
            c.line_to(bx,yy)
        c.stroke()
        for m in range(7):
            v=(t*.21+m/7+j*.19)%1
            y=552+v*334
            xx=sx+tilt*math.sin(v*8+j)*19+17*v
            C(c,AQUA,(.24+.5*grow)*(1-v*.4));c.arc(xx,y,1.5+grow,0,math.tau);c.fill()
    # Thin diagonal droplets, not clip-art raindrops.
    r=random.Random(61)
    for j in range(65):
        x=r.uniform(x0+9,x1-9)
        y=285+((r.random()*190+t*r.uniform(120,240))%146)
        line(c,(x,y),(x-3,y+12),AQUA,r.uniform(.22,.6),1.05)
    # The two reactions unfold in order. Large type, white space, no UI cards.
    mast(c,'水的雕刻','CHEMISTRY OF KARST',t,D,'06')
    mono(c,'01 / ABSORB CO2',1110,330,18,GOLD,E(t,1.6,2.8),track=2)
    txt(c,'雨水进入土壤',1110,387,36,PAPER,E(t,2.2,3.5),serif=True)
    a=E(t,3.4,5.0)
    line(c,(1110,407),(1805,407),PAPER,.25*a,1)
    G['chem'](c,CHEM1,1110,495,53,PAPER,a)
    txt(c,'弱酸性 · 碳酸',1110,548,26,AQUA,a)
    mono(c,'02 / DISSOLVE LIMESTONE',1110,637,18,GOLD,E(t,8.0,9.5),track=1.4)
    b=E(t,9.1,11.2)
    line(c,(1110,657),(1805,657),PAPER,.25*b,1)
    G['chem'](c,'CaCO3 + H2CO3',1110,724,47,PAPER,b)
    G['chem'](c,'→ Ca(HCO3)2',1110,789,47,AQUA,b)
    txt(c,'碳酸氢钙随水离去',1110,856,28,BONE,E(t,D*.70,D*.78),serif=True)
    mono(c,'RAIN → SOIL → JOINT → GROUNDWATER',137,884,15,GOLD,.86,track=1.1)


def spark(c,x,y,kind,a,t):
    c.save();c.translate(x,y);C(c,AQUA,.78*a);c.set_line_width(2)
    if kind=='temp':
        c.arc(0,-18,26,0,math.tau);c.stroke()
        for i in range(12):
            th=i*math.tau/12
            line(c,(math.cos(th)*37,math.sin(th)*37-18),(math.cos(th)*47,math.sin(th)*47-18),AQUA,.7*a,1.4)
    elif kind=='rain':
        c.move_to(-35,-21);c.curve_to(-28,-42,-6,-45,5,-30)
        c.curve_to(28,-39,46,-24,43,-4);c.line_to(-35,-4);c.stroke()
        for i in range(5):
            yy=(t*29+i*17)%20
            line(c,(-28+i*15,11+yy),(-34+i*15,24+yy),AQUA,.64*a,1.5)
    else:
        c.move_to(0,39);c.line_to(0,-14);c.stroke()
        for th in (.15,1.1,2.2,3.1,4.1,5.2):
            dx=math.cos(th)*35;dy=math.sin(th)*30-13
            line(c,(0,-1),(dx,dy),AQUA,.72*a,1.8)
            c.arc(dx,dy,5,0,math.tau);c.stroke()
    c.restore()


def anim_rate(c,t,D):
    bg(c)
    mast(c,'慢，是地质的时间尺度','DISSOLUTION / TIME & CLIMATE',t,D,'07')
    a=E(t,.7,1.8)
    mono(c,'1000 YEARS  /  APPROXIMATE',165,344,19,GOLD,a,track=2)
    txt(c,'几十毫米',157,504,111,PAPER,a,serif=True,bold=False)
    txt(c,'岩石被溶蚀的厚度',165,555,30,BONE,a,serif=True)
    # Measured scale advancing toward the right; avoid implying a precise universal rate.
    bx,by=172,666
    line(c,(bx,by),(1092,by),PAPER,.25,2)
    for i in range(41):
        xx=bx+i*23
        ht=20 if i%5==0 else 9
        line(c,(xx,by-ht),(xx,by+ht),PAPER,.39,1)
    q=E(t,1.6,D*.85)
    line(c,(bx,by),(bx+920*q,by),GOLD,.94,3)
    glow(c,bx+920*q,by,46,GOLD,.19)
    mono(c,'0',bx,by+52,16,MUTED,1,track=1)
    mono(c,'~ DECADES OF MILLIMETRES',1092,by+52,14,GOLD,.8,'r',.9)
    # Three sober symbolic keys with explanatory type on a right-hand column.
    a=E(t,D*.29,D*.38)
    line(c,(1195,290),(1195,849),GOLD,.7*a,1.4)
    for i,(name,en,kind) in enumerate([
        ('高温','HEAT','temp'),('丰沛降水','RAIN','rain'),('活跃的生物','BIOTA','bio')]):
        y=390+i*193;b=E(t,D*(.30+i*.15),D*(.38+i*.15))
        spark(c,1280,y,'temp' if kind=='temp' else 'rain' if kind=='rain' else 'bio',b,t)
        txt(c,name,1360,y-13,35,PAPER,b,serif=True)
        mono(c,en,1361,y+22,16,MUTED,b,track=1.5)
        line(c,(1361,y+61),(1775,y+61),PAPER,.14*b,1)
    mono(c,'SOUTH CHINA / HUMID SUBTROPICS',169,836,16,AQUA,E(t,6,7),'l',1.2)

# ---------------------------------------------------------------- EVOLUTION / THE 2.5D LANDSCAPE
@lru_cache(maxsize=16)
def profile_set(stage,z,N=202):
    out=[]
    for k in range(N+1):
        # Successive ridges are laterally offset in depth, so the landscape
        # reads as a terrain volume instead of one five-times-repeated waveform.
        u=k/N+.075*z
        if stage==0:
            h=.13
            for p in range(max(0,int(u*25)-2),min(29,int(u*25)+3)):
                center=(p+.51+.20*math.sin(p*2.7)) / 25
                width=.014+.006*math.sin(p*3.3)**2
                d=(u-center)/(width*(1.25 if u<center else .83))
                peak=(.38+.24*math.sin(p*.71+1.3)**2)*max(0,1-abs(d))**.83
                h=max(h,.13+peak)
        elif stage==1:
            h=.24
            for p,center in enumerate((.015,.167,.298,.456,.625,.780,.942,1.10)):
                width=(.085+.014*math.sin(p*2.3)**2)*(1.13 if u<center else .91)
                d=(u-center)/width
                shape=max(0,1-d*d)**1.36
                h=max(h,.24+(.32+.15*math.sin(p*1.84+1.2)**2)*shape)
        elif stage==2:
            h=.13
            for p,center in enumerate((.082,.253,.424,.588,.751,.910,1.07)):
                width=.075*(1.15 if u<center else .78)
                d=(u-center)/width
                h=max(h,.13+(.45+.11*math.sin(p*2.4+.9)**2)*max(0,1-d*d)**1.85)
        else:
            h=.105
            for p,center in enumerate((.31,.735,1.12)):
                width=.071*(1.12 if u<center else .87)
                d=(u-center)/width
                h=max(h,.105+(.47-.045*p)*max(0,1-d*d)**2.0)
        # Subtle high-frequency weathering keeps the silhouette organic.
        detail=(.004*math.sin(u*146+stage)+.003*math.sin(u*317+stage*2))
        out.append(max(.07,h+detail*min(1,(h-.09)*4)))
    return out


def evolve_level(t,D):
    # Long readable holds; fast, deliberate topological changes between them.
    return (E(t,D*.255,D*.335)+E(t,D*.585,D*.665)+E(t,D*.865,D*.955))


def anim_evolve(c,t,D):
    bg(c)
    s=evolve_level(t,D)
    i=min(3,int(s));j=min(3,i+1);q=s-i
    N=202
    x0,x1=157,1771
    ybase=807
    names=['石林','峰丛','峰林','孤峰']
    ens=['STONE FOREST','PEAK CLUSTER','PEAK FOREST','ISOLATED PEAK']
    # Engraved, pale topographic relief in the distant sky.
    for row in range(7):
        yy=290+row*34
        C(c,PAPER,.050);c.set_line_width(1)
        c.move_to(94,yy)
        for x in range(110,1850,22):
            c.line_to(x,yy+11*math.sin(x*.006+row*.47))
        c.stroke()
    # The relief is built as four offset geological ridges (a floating cutaway),
    # shaded and cross-laminated, not a flat silhouette or stock mountain icon.
    for dep in (1.0,.73,.47,.22,0):
        h0=profile_set(i,dep,N)
        h1=profile_set(j,dep,N)
        elev=[M(h0[k],h1[k],q) for k in range(N+1)]
        offx=dep*103
        offy=dep*117
        pts=[(x0+offx+k*(x1-x0)/N,
              ybase-offy-elev[k]*(345+35*dep)) for k in range(N+1)]
        bottom=890-dep*87
        c.move_to(pts[0][0],bottom)
        [c.line_to(*p) for p in pts]
        c.line_to(pts[-1][0],bottom);c.close_path()
        c.save();c.clip()
        # Light comes from high left. The relief recedes into blue-grey air.
        g=cairo.LinearGradient(x0+offx,330,x1+offx,895)
        f=1-dep*.22
        g.add_color_stop_rgb(0,.85*f,.82*f,.70*f)
        g.add_color_stop_rgb(.48,.62*f,.64*f,.57*f)
        g.add_color_stop_rgb(1,.28*f,.36*f,.35*f)
        c.set_source(g);c.paint()
        if dep==0:
            # Karst is excavated from nearly horizontal carbonate beds. The
            # strata remain level when the surface is deeply dissected; the
            # volume is clipped by the irregular, morphing terrain edge.
            for level in range(13):
                yline=490+level*31
                C(c,INK,.18 if level%3 else .33);c.set_line_width(1.15)
                c.move_to(x0,yline)
                for xx in range(x0+12,x1+1,16):
                    c.line_to(xx,yline+2.4*math.sin(xx*.012+level*.63))
                c.stroke()
            r=random.Random(44)
            for m in range(780):
                x=r.uniform(x0,x1);y=r.uniform(530,905)
                C(c,INK,r.uniform(.045,.20));c.rectangle(x,y,r.uniform(1,3),1.1);c.fill()
            for k in range(12,195,19):
                x,y=pts[k]
                C(c,INK,.18);c.set_line_width(1)
                c.move_to(x,y+5);c.curve_to(x-4,y+24,x+3,y+30,x-7,y+44);c.stroke()
        c.restore()
        C(c,PAPER,.57-dep*.20);c.set_line_width(1.45)
        c.move_to(*pts[0]);[c.line_to(*p) for p in pts[1:]];c.stroke()
        if dep==0:
            front=pts
        else:
            # Pinprick shrubs are sufficient to imply a living highland.
            for k in range(9,N-8,15):
                xx,yy=pts[k]
                C(c,SAGE,.23);c.arc(xx,yy-1,2.8,0,math.tau);c.fill()
    # Continuous aquifer below the rock, subtle enough not to look like a ruler.
    C(c,AQUA,.44);c.set_line_width(2.4)
    c.move_to(x0,857)
    for k in range(1,202):
        xx=x0+(x1-x0)*k/201
        c.line_to(xx,857+2.5*math.sin(k*.16+t*.35))
    c.stroke()
    for m in range(14):
        x=x0+((m*149+t*18)%(x1-x0))
        C(c,AQUA,.13);c.arc(x,854+2.5*math.sin(x*.01+t*.35),2.1,0,math.tau);c.fill()
    # The landscape's four acts as a typographic index, not an animated bar chart.
    mast(c,'石峰的演化','A LANDSCAPE IN FOUR ACTS',t,D,'08')
    for k,name in enumerate(names):
        x=1280+k*169
        alpha=.28+.65*max(0,1-abs(s-k)*1.3)
        C(c,GOLD,alpha);c.arc(x,272,3.5,0,math.tau);c.fill()
        txt(c,name,x,317,27,PAPER,alpha,serif=True,align='c')
        if k<3:line(c,(x+22,272),(x+147,272),PAPER,.19,1)
    # Current stage caption tracks the morph; no labels printed over the relief.
    cur=min(3,round(s));on=max(.20,1-abs(s-cur)*1.8)
    txt(c,names[cur],147,339,65,PAPER,on,serif=True)
    mono(c,ens[cur],149,376,17,GOLD,on,track=1.8)
    mono(c,'EROSION  →  INCISION  →  ISOLATION',148,902,15,MUTED,.8,'l',1.2)
    mono(c,'SCHEMATIC CROSS SECTION / NOT TO SCALE',1765,902,14,MUTED,.64,'r',.8)


# ---------------------------------------------------------------- SUBTERRANEAN SYSTEMS
def ground_y(x):
    return 369+18*math.sin(x*.007)+11*math.sin(x*.019)


def stone(c,x0,x1):
    c.move_to(x0,913)
    for x in range(x0,x1+1,10):c.line_to(x,ground_y(x))
    c.line_to(x1,913);c.close_path()
    g=cairo.LinearGradient(0,300,0,924)
    g.add_color_stop_rgb(0,.69,.68,.60)
    g.add_color_stop_rgb(.47,.54,.55,.50)
    g.add_color_stop_rgb(1,.28,.34,.33)
    c.set_source(g);c.fill()
    c.save()
    c.move_to(x0,913)
    for x in range(x0,x1+1,10):c.line_to(x,ground_y(x))
    c.line_to(x1,913);c.close_path();c.clip()
    for j in range(17):
        yy=395+j*31
        C(c,INK,.16+j*.003);c.set_line_width(1.1)
        c.move_to(x0,yy)
        for x in range(x0+12,x1+1,14):
            c.line_to(x,yy+5*math.sin(x*.010+j*.34))
        c.stroke()
    r=random.Random(173)
    for m in range(1200):
        x=r.randrange(x0,x1);y=r.uniform(360,907)
        C(c,INK,r.uniform(.05,.16));c.rectangle(x,y,r.uniform(.7,2.5),1);c.fill()
    c.restore()
    C(c,SAGE,.74);c.set_line_width(2.0)
    c.move_to(x0,ground_y(x0))
    for x in range(x0+10,x1+1,10):c.line_to(x,ground_y(x))
    c.stroke()
    # Almost invisible grasses/canopy along the skyline.
    for i in range(65):
        xx=x0+i*(x1-x0)/65
        line(c,(xx,ground_y(xx)),(xx+3,ground_y(xx)-5-(i%4)*2),SAGE,.23,1)


def cave_path(c,grow=1,roof=0):
    # Compound irregular vault rather than an oval; roof is moved toward the
    # surface for the separate collapse shot.
    r=.42+.58*grow
    cx=949
    c.save();c.translate(cx,0);c.scale(r,1);c.translate(-cx,0)
    c.new_sub_path()
    c.move_to(439,783)
    c.curve_to(405,712,457,623,564,624)
    c.curve_to(665,615,676,577-roof,786,591-roof*.75)
    c.curve_to(860,605-roof*.83,896,550-roof,986,579-roof)
    c.curve_to(1100,610-roof*.83,1188,566-roof*.71,1307,636)
    c.curve_to(1440,670,1485,735,1487,802)
    c.curve_to(1416,847,1335,814,1268,831)
    c.curve_to(1146,852,1090,816,982,838)
    c.curve_to(838,859,759,817,645,842)
    c.curve_to(532,864,472,843,439,783)
    c.close_path();c.restore()


def speleothem(c,x,y,length,width,hanging=True,alpha=1):
    if length < 1 or alpha<=0: return
    direction=1 if hanging else -1
    end=y+direction*length
    # Flowstone grows in a tapered, subtly asymmetrical calcite fold rather
    # than an isosceles vector triangle. Side lighting reveals volume.
    c.move_to(x-width,y)
    c.curve_to(x-width*.76,y+direction*length*.33,
               x-width*.30,y+direction*length*.73,x+.5,end)
    c.curve_to(x+width*.38,y+direction*length*.65,
               x+width*.93,y+direction*length*.30,x+width*.75,y)
    c.close_path()
    gg=cairo.LinearGradient(x-width,y,x+width,y)
    gg.add_color_stop_rgba(0,.43,.46,.42,.86*alpha)
    gg.add_color_stop_rgba(.29,.91,.85,.71,.93*alpha)
    gg.add_color_stop_rgba(.62,.72,.70,.61,.96*alpha)
    gg.add_color_stop_rgba(1,.33,.39,.38,.91*alpha)
    c.set_source(gg);c.fill()
    C(c,PAPER,.33*alpha);c.set_line_width(.75)
    c.move_to(x-width*.48,y+direction*3)
    c.curve_to(x-width*.28,y+direction*length*.52,x-width*.17,end-direction*5,
               x-.5,end-direction*1.5)
    c.stroke()


def anim_cave(c,t,D,collapse=False):
    bg(c)
    x0,x1=91,1818
    stone(c,x0,x1)
    if not collapse:
        growth=E(t,.5,D*.34)
        lower=E(t,D*.33,D*.56)
        drip=E(t,D*.49,D*.84)
        roof=0
    else:
        growth=1;lower=1;drip=0
        roof=E(t,.4,D*.66)*235
    cave_path(c,growth,roof)
    g=cairo.RadialGradient(940,751,6,940,751,690)
    g.add_color_stop_rgba(0,.037,.068,.076,1)
    g.add_color_stop_rgba(.46,.064,.118,.124,1)
    g.add_color_stop_rgba(1,.09,.13,.14,1)
    c.set_source(g);c.fill()
    cave_path(c,growth,roof)
    C(c,BONE,.23);c.set_line_width(2.2);c.stroke()
    # An actual narrow, moving waterline. Dim reflections replace the flat
    # bright-blue pill that made the previous cross-section cartoonish.
    cave_path(c,growth,roof)
    c.save();c.clip()
    river_y=M(698,815,lower)
    g=cairo.LinearGradient(0,river_y,0,902)
    g.add_color_stop_rgba(0,.085,.31,.36,.93)
    g.add_color_stop_rgba(1,.028,.11,.15,.99)
    c.set_source(g);c.rectangle(380,river_y,1190,170);c.fill()
    for n in range(5):
        yy=river_y+5+n*7
        C(c,AQUA,.23/(1+n*.33));c.set_line_width(.85)
        c.move_to(427,yy)
        for xx in range(440,1516,20):
            c.line_to(xx,yy+2.7*math.sin(xx*.021+t*1.15+n*.87))
        c.stroke()
    for n in range(44):
        xx=433+((n*79+t*38)%1052)
        yy=river_y+7+(n%6)*10
        C(c,PAPER,.25);c.arc(xx,yy,1.4,0,math.tau);c.fill()
    c.restore()
    # Several beautifully thin feeder fissures. A brighter water pulse descends.
    r=random.Random(32)
    for j in range(12):
        sx=310+j*119+r.uniform(-14,14)
        top=ground_y(sx)
        ex=sx+r.uniform(-55,55)
        mid=625+r.uniform(-35,42)
        C(c,INK,.49);c.set_line_width(2.2)
        c.move_to(sx,top)
        c.curve_to(sx-17,top+89,ex+22,mid-45,ex,mid)
        c.stroke()
        C(c,AQUA,.23+.35*growth);c.set_line_width(1.35)
        c.move_to(sx,top)
        c.curve_to(sx-17,top+89,ex+22,mid-45,ex,mid)
        c.stroke()
        pos=(t*.11+j*.27)%1
        px=M(sx,ex,pos)
        py=M(top,mid,pos)
        C(c,AQUA,.74*growth);c.arc(px,py,2.0,0,math.tau);c.fill()
    if not collapse:
        for j in range(19):
            r=random.Random(9+j)
            xx=543+j*44+r.uniform(-10,10)
            yy=604-26*math.cos((xx-940)/505*math.pi)+r.uniform(-13,14)
            LL=drip*r.uniform(25,88)
            if drip>.02:
                speleothem(c,xx,yy,LL,r.uniform(5.5,9.5),True,.86*drip)
                if j%3==0:
                    C(c,AQUA,.88*drip)
                    c.arc(xx,yy+LL+((t*61+j*22)%78),2.4,0,math.tau);c.fill()
            by=838-4*math.sin(j)
            speleothem(c,xx,by,drip*r.uniform(30,76),r.uniform(8,15),False,.76*drip)
        mast(c,'地下世界','CAVES / UNDERGROUND RIVERS',t,D,'09')
        a=E(t,2,4)
        marker(c,501,690,'01','地下河','AQUIFER → UNDERGROUND STREAM',a,-1)
        b=E(t,D*.61,D*.78)
        marker(c,1276,652,'02','钟乳石与石笋','PRECIPITATION / CaCO3',b,1)
        mono(c,'ROCK IS REMOVED, THEN REDEPOSITED',148,892,14,MUTED,.74,track=1)
    else:
        # Deepening shaft joins the collapse cavity to the exposed surface.
        collapse_k=E(t,.5,D*.67)
        yy=ground_y(953)
        # Shape widens downwards. It is revealed using clipped, irregular edges.
        pts=[(948-135*collapse_k,yy-4),(956+135*collapse_k,yy-4),
             (1070+167*collapse_k,550),(1222,675),(723,675),(816-157*collapse_k,550)]
        poly(c,pts,INK,.99*collapse_k)
        glow(c,948,yy,100,GOLD,.14*collapse_k)
        rr=random.Random(23)
        for j in range(50):
            st=rr.uniform(.55,D*.69)
            ph=E(t,st,st+.95)
            x=rr.uniform(809,1092)
            y0=rr.uniform(388,547)
            y=M(y0,837-rr.uniform(0,57),ph**1.5)
            sx=rr.uniform(4,13)
            poly(c,[(x,y),(x+sx,y+sx*.3),(x+sx*.8,y+sx),(x-3,y+sx*.56)],BONE,.82)
        mast(c,'洞顶崩塌','COLLAPSE / TIANKENG',t,D,'10')
        a=E(t,D*.47,D*.79)
        marker(c,1025,553,'','天坑','COLLAPSED CAVE CEILING',a,1)
        txt(c,'600+ 米',1506,792,50,GOLD,E(t,D*.68,D*.82),serif=True,align='r')
        mono(c,'XIAOZHAI TIANKENG / DEPTH',1510,829,15,PAPER,a,'r',1)
        mono(c,'SCHEMATIC CROSS SECTION / NOT TO SCALE',140,887,14,MUTED,.67,track=.7)


# ---------------------------------------------------------------- FRAGILITY / RETROSPECT

def anim_soil(c,t,D):
    bg(c)
    x0,x1=193,899
    k=E(t,1.2,D*.82)
    top=M(402,689,k)
    gg=cairo.LinearGradient(0,top,0,885)
    gg.add_color_stop_rgb(0,.77,.74,.66)
    gg.add_color_stop_rgb(1,.38,.42,.40)
    c.set_source(gg);c.rectangle(x0,top,x1-x0,880-top);c.fill()
    c.save();c.rectangle(x0,top,x1-x0,880-top);c.clip()
    for j in range(17):
        yy=433+j*28
        line(c,(x0,yy),(x1,yy-2*math.sin(j*.52)),INK,.27,1)
    r=random.Random(17)
    for j in range(540):
        px=r.uniform(x0,x1);py=r.uniform(400,879)
        C(c,INK,r.uniform(.04,.16));c.rectangle(px,py,1.8,.8);c.fill()
    c.restore()
    soil_h=3+23*k
    gr=cairo.LinearGradient(0,top-27,0,top+2)
    gr.add_color_stop_rgb(0,.52,.38,.25)
    gr.add_color_stop_rgb(1,.25,.21,.18)
    c.set_source(gr);c.rectangle(x0,top-soil_h,x1-x0,soil_h);c.fill()
    C(c,GOLD,.7);c.set_line_width(1.4)
    c.move_to(x0,top-soil_h);c.line_to(x1,top-soil_h);c.stroke()
    # Stippled, dissolving particles rise away from the vanishing rock.
    r=random.Random(141)
    for j in range(54):
        xx=r.uniform(x0+10,x1-10)
        yy=top-r.uniform(12,98)
        opacity=.15+.47*max(0,1-abs(t-D*.6)/D*.6)
        C(c,BONE,opacity)
        c.arc(xx+3*math.sin(t*.27+j),yy,1.5,0,math.tau);c.fill()
    # Vertical dimension shows the original limestone thickness ghosted behind.
    C(c,PAPER,.25);c.set_dash([5,7]);c.set_line_width(1)
    c.move_to(x0,400);c.line_to(x1,400);c.stroke();c.set_dash([])
    line(c,(166,400),(166,top),GOLD,.8,1.25)
    line(c,(151,400),(180,400),GOLD,.8,1.25)
    line(c,(151,top),(180,top),GOLD,.8,1.25)
    mast(c,'脆弱的土壤','WHAT THE ROCK LEAVES BEHIND',t,D,'11')
    mono(c,'LIMESTONE / DISSOLVED',193,912,15,MUTED,.67,track=1)
    a=E(t,2,3)
    mono(c,'TO FORM',1077,374,17,GOLD,a,track=2)
    txt(c,'1 厘米',1067,505,91,PAPER,a,serif=True)
    txt(c,'厚的土壤',1077,562,42,BONE,a,serif=True)
    line(c,(1077,601),(1790,601),PAPER,.26*a,1.2)
    b=E(t,D*.43,D*.65)
    txt(c,'数千年',1066,754,95,GOLD,b,serif=True)
    txt(c,'的漫长等待',1076,814,34,PAPER,b,serif=True)


def tiny_motif(c,kind,x,y,a):
    C(c,AQUA,.72*a);c.set_line_width(1.5)
    if kind==0:
        for k in range(4):
            yy=y+18*k
            c.move_to(x-80,yy)
            for xx in range(-70,94,10):c.line_to(x+xx,yy+5*math.sin(xx*.053+k*.36))
            c.stroke()
    elif kind==1:
        for k in range(5):
            c.move_to(x-81,y+75+k*7)
            for xx in range(-70,94,10):
                c.line_to(x+xx,y+74+k*7-48*math.exp(-((xx-6)/37)**2))
            c.stroke()
    else:
        for j in range(17):
            dx=(j*37)%163-80
            dy=(j*43)%80
            line(c,(x+dx,y+dy),(x+dx-7,y+dy+15),AQUA,.59*a,1.2)


def anim_timeline(c,t,D):
    bg(c)
    mast(c,'一封来自地球的长信','THREE DEEP-TIME ACTS',t,D,'12')
    p=E(t,1.0,D*.80)
    line(c,(192,730),(1726,730),PAPER,.27,1.2)
    line(c,(192,730),(192+1534*p,730),GOLD,.96,2.5)
    xs=[252,829,1402]
    items=[('数亿年','远古海洋','DEPOSITION'),('数千万年','大地抬升','TECTONIC UPLIFT'),('数百万年','雨水雕刻','DISSOLUTION')]
    for i,(age,zh,en) in enumerate(items):
        x=xs[i]
        a=E(t,.65+i*D*.24,1.75+i*D*.24)
        tiny_motif(c,i,x+94,400,a)
        line(c,(x,296),(x,697),PAPER,.15*a,1)
        mono(c,f'0{i+1}',x,315,17,GOLD,a,track=2)
        txt(c,age,x-5,378,56,PAPER,a,serif=True)
        txt(c,zh,x-4,583,43,BONE,a,serif=True)
        mono(c,en,x,620,16,GOLD,a,track=1.5)
        glow(c,x,730,42,GOLD,.14*a)
        C(c,GOLD,a);c.arc(x,730,5,0,math.tau);c.fill()
    a=E(t,D*.75,D*.93)
    mono(c,'THE PRESENT  /  THIS LANDSCAPE',W/2,844,20,PAPER,a,'c',2)
    mono(c,'OCEAN + UPLIFT + WATER',W/2,884,17,GOLD,a,'c',2.2)


# ---------------------------------------------------------------- TITLES / CARDS / END-CREDITS
def photo_gradient(c,left=.82,right=.05,top=.06,bottom=.25):
    g=cairo.LinearGradient(0,0,W,0)
    g.add_color_stop_rgba(0,*INK,left)
    g.add_color_stop_rgba(.58,*INK,(left+right)*.45)
    g.add_color_stop_rgba(1,*INK,right)
    c.set_source(g);c.paint()
    h=cairo.LinearGradient(0,0,0,H)
    h.add_color_stop_rgba(0,0,0,0,top)
    h.add_color_stop_rgba(.60,0,0,0,0)
    h.add_color_stop_rgba(1,0,0,0,bottom)
    c.set_source(h);c.paint()


def card_title(c,t,D):
    G['draw_photo'](c,'img/ai_aerial.jpg',min(1,t/D),'out',dark=.06)
    photo_gradient(c,.83,.08,.21,.23)
    a=E(t,.15,1.3)*(1-E(t,D-.7,D))
    line(c,(158,181),(304,181),GOLD,.9*a,2)
    mono(c,'FIELD NOTES  /  001',159,217,19,PAPER,a,track=2)
    txt(c,'喀斯特',153,545,170,PAPER,a,serif=True,bold=False,spacing=17)
    ww=665*E(t,.4,2.1)
    line(c,(160,588),(160+ww,588),GOLD,.88*a,2)
    txt(c,'中国南方的石头森林',160,665,48,PAPER,E(t,.7,1.9)*a,serif=True,spacing=3)
    mono(c,'KARST  /  THE STONE FOREST OF SOUTH CHINA',164,713,19,GOLD,E(t,1.2,2.3)*a,track=1.3)
    mono(c,'GEOGRAPHY  ·  DEEP TIME  ·  WATER',164,885,17,PAPER,.78*a,track=1.8)
    mono(c,'ORIGINAL DOCUMENTARY',W-95,885,14,PAPER,.63*a,'r',1)


def make_chapter(num,zh,en,img):
    def f(c,t,D):
        G['draw_photo'](c,img,min(1,t/D),'in',dark=.16)
        photo_gradient(c,.84,.14,.2,.25)
        a=E(t,.15,.85)*(1-E(t,D-.55,D))
        yshift=15*(1-E(t,.15,1.1))
        mono(c,'K A R S T   /   F I E L D  N O T E S',152,158,17,GOLD,.81*a,track=1)
        line(c,(154,187),(1756,187),PAPER,.37*a,1)
        txt(c,num,149,457-yshift,168,GOLD,.65*a,serif=True)
        line(c,(156,485-yshift),(800,485-yshift),GOLD,.66*a,1.8)
        txt(c,zh,152,603-yshift,101,PAPER,a,serif=True,bold=False,spacing=5)
        mono(c,en,159,667-yshift,23,PAPER,.83*a,track=2.2)
        mono(c,f'CHAPTER {num}  /  06',159,900,16,PAPER,.78*a,track=1.4)
    return f


def card_end(c,t,D):
    G['draw_photo'](c,'img/guilin_0.jpg',min(1,t/8),'out',dark=.32+.55*E(t,5.2,9.4))
    photo_gradient(c,.5,.46,.19,.55)
    a=E(t,.5,1.7)*(1-E(t,5.0,7.0))
    txt(c,'这里是喀斯特',W/2,538,113,PAPER,a,serif=True,align='c',spacing=14,shadow=True)
    mono(c,'THIS IS KARST',W/2,613,23,GOLD,a,'c',3.3)
    if t>6.3:
        lines=['素材鸣谢  /  IMAGE & VIDEO CREDITS','']
        for k,(ti,au,lic) in G['CREDITS'].items():
            if k in G['USED']:
                author=au.splitlines()[0]
                lines.append(f'{ti[:53]}   —   {author[:35]}  /  {lic}')
        lines+=['','部分概念画面由 AI 辅助生成 · 动画与图解为原创绘制',
                '地图数据：Natural Earth / China GeoJSON','', '感谢观看']
        y0=H+36-(t-6.3)*94
        for j,s in enumerate(lines):
            yy=y0+j*47
            if -45<yy<H+25:
                big=(j==0 or s=='感谢观看')
                txt(c,s,W/2,yy,36 if big else 23,GOLD if big else PAPER,.94,
                    bold=big,align='c')
