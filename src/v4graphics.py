# -*- coding: utf-8 -*-
"""Karst Field Notes / v4. Original procedural relief & lithic cutaway.

A height-field lithology renderer creates shaded terrain in perspective, with
morphs interpolated in *height space*. The cave is a multi-chamber signed-width
cross-section with illuminated bedding, water, speleothems and rockfall.
Nothing is traced or sampled from somebody else's animation.
"""
import cairo, math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageFilter
import premium as P

W,H=1920,1080
NX,NZ=240,76
BONE=P.BONE; GOLD=P.GOLD; AQUA=P.AQUA; PAPER=P.PAPER; INK=P.INK; SAGE=P.SAGE
G=None

def install(namespace):
    global G
    G=namespace
    namespace['anim_evolve']=anim_evolve
    namespace['anim_cave']=anim_cave


def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)


@lru_cache(maxsize=4)
def heightfield(stage):
    """Reproducible, non-photographic terrain. Extent represents no real site."""
    xx=np.linspace(0,1,NX+1,dtype=np.float32)[None,:]
    zz=np.linspace(0,1,NZ+1,dtype=np.float32)[:,None]
    a=np.broadcast_to(xx,(NZ+1,NX+1))
    b=np.broadcast_to(zz,(NZ+1,NX+1))
    if stage==0:
        # Closely packed, sharply eroded dissolution pillars (Shilin motif).
        h=np.full_like(a,.10)
        for j in range(7):
            for k in range(22):
                cx=(k+.40+.21*math.sin(j*8+k*3.2))/22
                cz=(j+.50+.23*math.cos(k*2.9+j))/7
                sx=.019*(.75+.35*math.sin(j+k*3.7)**2)
                sz=.09*(.7+.40*math.sin(j*.8+k*.6)**2)
                d=np.sqrt(((a-cx)/sx)**2+((b-cz)/sz)**2)
                mound=np.maximum(0,1-d)**.82*(.48+.16*math.sin(k*.66+j*1.93)**2)
                h=np.maximum(h,.10+mound)
    elif stage==1:
        # Conjoined high bases / separate crowns.
        h=np.full_like(a,.22)
        for j in range(3):
            for k in range(8):
                cx=(k+.53+.18*math.sin(j*3.2+k*5.7))/8
                cz=(j+.53+.16*math.sin(k*3.4+j))/3
                sx=.105*(.85+.32*math.sin(k*1.1+j)**2)
                sz=.23*(.8+.2*math.cos(k*.7+j))
                d=((a-cx)/sx)**2+((b-cz)/sz)**2
                h=np.maximum(h,.22+(.42+.10*math.sin(k*2.7+j)**2)*np.maximum(0,1-d)**1.20)
    elif stage==2:
        # Separated fenglin cones rising from a lower floodplain.
        h=np.full_like(a,.105)
        for j in range(2):
            for k in range(6):
                cx=(k+.50+.12*math.sin(j*7+k*1.9))/6
                cz=(j+.46+.12*math.sin(k*3.8+j))/2
                sx=.069*(.9+.2*math.sin(k*1.7+j))
                sz=.17*(.84+.22*math.cos(k*2.1+j))
                d=((a-cx)/sx)**2+((b-cz)/sz)**2
                h=np.maximum(h,.105+(.56+.07*math.sin(k*3+j)**2)*np.maximum(0,1-d)**1.40)
    else:
        h=np.full_like(a,.085)
        for cx,cz,m in ((.28,.37,.60),(.74,.64,.53),(.82,.15,.31)):
            d=((a-cx)/.069)**2+((b-cz)/.145)**2
            h=np.maximum(h,.085+m*np.maximum(0,1-d)**1.52)
    # Fractal weathering. At the foot of a hill it does not invent new peaks.
    micro=(.019*np.sin(53*a+13*b)*np.cos(77*b-3*a)
           +.010*np.sin(137*a-48*b)*np.cos(39*a+23*b)
           +.005*np.sin(291*a+75*b))
    h+=micro*np.minimum(1,np.maximum(0,(h-.08)*5))
    return np.clip(h,.065,.82).astype('f')


def projection(x,z,elevation):
    """Orthographic perspective with horizon, depth compression and height."""
    sx=950+(x-.5)*1510*(1-.23*z)+83*z
    sy=778-205*z-elevation*(355-115*z)
    return sx,sy


def draw_specimen(c,A,B,alpha):
    """At most 18,240 lamina-shaded top-surface cells; run once per keyframe."""
    hh=(1-alpha)*heightfield(A)+alpha*heightfield(B)
    r=cairo.LinearGradient(0,740,0,924)
    r.add_color_stop_rgba(0,.03,.07,.076,.20)
    r.add_color_stop_rgba(1,.01,.03,.035,.56)
    c.set_source(r);c.rectangle(110,730,1700,200);c.fill()
    # Raster-clean mesh edges; the silhouette is outlined with antialiasing
    # afterwards. This avoids a visible grid of hairline seams on the plain.
    c.save(); c.set_antialias(cairo.ANTIALIAS_NONE)
    for row in range(NZ-1,-1,-1):
        z1=row/NZ;z2=(row+1)/NZ
        for k in range(NX):
            x1=k/NX;x2=(k+1)/NX
            h11=hh[row,k];h21=hh[row,k+1]
            h12=hh[row+1,k];h22=hh[row+1,k+1]
            du=(h21+h22-h11-h12)*.5*NX
            dv=(h12+h22-h11-h21)*.5*NZ
            sunny=np.clip(.79- .092*du + .052*dv,.37,1.03)
            # Continuous, low-frequency mineral tint rather than cell-by-cell
            # grain (the latter looked like a computer mesh at 1080p).
            grain=.012*math.sin(k*.070+row*.16)+.007*math.sin(k*.15-row*.095)
            v=np.clip(sunny+grain,.27,1.08)
            low=np.clip((.27-(h11+h21+h12+h22)/4)*3,0,1)
            # Lowland surface is damp and lightly vegetated, exposed summits
            # are luminous beige grey; rear rows are blue due to atmosphere.
            atmo=z1*.17
            col=((.73-.18*low)*v-atmo*.39,
                 (.718-.10*low)*v-atmo*.17,
                 (.655-.22*low)*v+atmo*.17)
            c.set_source_rgb(*(min(1,max(0,q)) for q in col))
            p1=projection(x1,z1,h11);p2=projection(x2,z1,h21)
            p3=projection(x2,z2,h22);p4=projection(x1,z2,h12)
            c.move_to(*p1);c.line_to(*p2);c.line_to(*p3);c.line_to(*p4)
            c.close_path();c.fill()
    c.restore()
    # Height contours, one pixel. They are calculated from the surface itself.
    for level in (.23,.36,.52,.64):
        for row in range(0,NZ,2):
            for k in range(0,NX,2):
                points=[]
                v=[hh[row,k],hh[row,k+2],hh[row+2,k+2],hh[row+2,k]]
                xy=[(k/NX,row/NZ),((k+2)/NX,row/NZ),((k+2)/NX,(row+2)/NZ),(k/NX,(row+2)/NZ)]
                for side in range(4):
                    l=(side+1)%4
                    if (v[side]-level)*(v[l]-level)<0:
                        mix=(level-v[side])/(v[l]-v[side])
                        x=xy[side][0]+mix*(xy[l][0]-xy[side][0])
                        z=xy[side][1]+mix*(xy[l][1]-xy[side][1])
                        points.append(projection(x,z,level))
                if len(points)>=2:
                    P.line(c,points[0],points[1],PAPER,.07+.05*level,.9)
    # Geological front face with predominantly level beds, not terrain-shaped
    # U-curves. Its top rim exactly follows the projected nearest terrain row.
    front=[projection(k/NX,0,hh[0,k]) for k in range(NX+1)]
    c.move_to(front[0][0],912)
    for p in front:c.line_to(*p)
    c.line_to(front[-1][0],912);c.close_path()
    c.save();c.clip()
    gr=cairo.LinearGradient(0,495,0,912)
    gr.add_color_stop_rgb(0,.72,.686,.604)
    gr.add_color_stop_rgb(.48,.52,.538,.473)
    gr.add_color_stop_rgb(1,.245,.325,.315)
    c.set_source(gr);c.paint()
    for bed in range(13):
        y=540+bed*27
        c.set_source_rgba(.08,.14,.145,.23 if bed%3 else .41)
        c.set_line_width(1.05)
        c.move_to(136,y)
        for x in range(154,1795,14):c.line_to(x,y+3*math.sin(x*.009+bed*.42))
        c.stroke()
    rr=random.Random(541)
    for n in range(1000):
        x=rr.uniform(170,1730);y=rr.uniform(470,911)
        c.set_source_rgba(.06,.11,.12,rr.uniform(.055,.24))
        c.rectangle(x,y,rr.uniform(.5,2.8),rr.uniform(.4,1.2));c.fill()
    c.restore()
    c.set_source_rgba(*PAPER,.71);c.set_line_width(2)
    c.move_to(*front[0]);[c.line_to(*p) for p in front[1:]];c.stroke()
    # Aquifer tucked into the strata, with muted surface light.
    P.line(c,(195,861),(1721,861),AQUA,.51,2.3)
    for m in range(12):
        x=220+m*132
        c.set_source_rgba(*AQUA,.18)
        c.arc(x,858+2*math.sin(m*5),2.4,0,math.tau);c.fill()


@lru_cache(maxsize=12)
def relief_surface(stage_a,stage_b,key):
    surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
    c=cairo.Context(surf)
    draw_specimen(c,stage_a,stage_b,key/10)
    return surf


def anim_evolve(c,t,D):
    P.bg(c)
    s=P.E(t,D*.255,D*.335)+P.E(t,D*.585,D*.665)+P.E(t,D*.865,D*.955)
    stage=min(3,int(s));next_stage=min(3,stage+1)
    q=s-stage
    key=min(10,int(q*10));r=q*10-key
    # A slow documentary dolly: near rock travels farther than the backdrop.
    c.save()
    scale=1.013+.045*t/D
    c.translate(W/2,H/2);c.scale(scale,scale)
    c.translate(-W/2-7*math.sin(t*.11),-H/2-5*math.sin(t*.17))
    c.set_source_surface(relief_surface(stage,next_stage,key),0,0);c.paint()
    if key<10 and r>.001:
        c.set_source_surface(relief_surface(stage,next_stage,key+1),0,0)
        c.paint_with_alpha(r)
    # Small drainage threads wind through low-lying valleys in stages 2–4.
    if s>.8:
        a=min(.49,(s-.8)*.25)
        C=lambda a1:c.set_source_rgba(*AQUA,a1)
        C(a);c.set_line_width(1.9)
        c.move_to(195,778)
        for x in range(215,1730,14):
            u=(x-190)/1540
            # River crosses the exposed floodplain only where relief is low.
            h=heightfield(min(3,round(s)))[int((.34+.07*math.sin(u*8))*NZ),min(NX,int(u*NX))]
            if h < .30:
                c.line_to(x,771+20*math.sin(u*16+t*.11))
            else:
                c.move_to(x,771+20*math.sin(u*16+t*.11))
        c.stroke()
    c.restore()
    names=['石林','峰丛','峰林','孤峰']
    en=['STONE FOREST','PEAK CLUSTER','PEAK FOREST','ISOLATED PEAK']
    P.mast(c,'石峰的演化','A LANDSCAPE IN FOUR ACTS',t,D,'08')
    for i,n in enumerate(names):
        x=1280+i*169
        a=.31+.63*max(0,1-abs(s-i)*1.5)
        c.set_source_rgba(*GOLD,a);c.arc(x,270,3.5,0,math.tau);c.fill()
        P.txt(c,n,x,316,27,PAPER,a,serif=True,align='c')
        if i<3:P.line(c,(x+24,270),(x+145,270),PAPER,.16,1)
    near=min(3,round(s));alpha=max(.18,1-abs(s-near)*1.8)
    P.txt(c,names[near],144,347,66,PAPER,alpha,serif=True)
    P.mono(c,en[near],147,381,17,GOLD,alpha,track=1.8)
    P.mono(c,'SURFACE RELIEF  /  RAINWATER EROSION',150,904,15,MUTED,.79,track=1)
    P.mono(c,'SCHEMATIC TERRAIN, NOT A GEOGRAPHIC MODEL',1761,904,14,MUTED,.76,'r',.8)

MUTED=P.MUTED


def terrain_y(x):
    return 376+18*math.sin(x*.0061)+9*math.sin(x*.0187)


def cave_bounds(x,expand=1,roof=0):
    a=math.exp(-((x-634)/190)**2)
    b=math.exp(-((x-960)/285)**2)
    d=math.exp(-((x-1266)/180)**2)
    chamber=max(.55*a,1.00*b,.64*d)
    # Irregular connected chambers of differing scales, plus a narrow channel.
    high=735-expand*(29+153*chamber)+7*math.sin(x*.022+.5)
    low=747+expand*(17+101*chamber)+6*math.sin(x*.024-1)
    lift=roof*math.exp(-((x-960)/185)**2)
    return high-lift,low


def cave_cutout(c,expand=1,roof=0):
    scale=.23+.77*expand
    x0=960-(960-433)*scale
    x1=960+(1466-960)*scale
    pts_top=[];pts_bottom=[]
    for j in range(95):
        xx=x0+(x1-x0)*j/94
        u=960+(xx-960)/scale
        hi,lo=cave_bounds(u,expand,roof)
        v=max(0,min(1,(u-433)/115,(1466-u)/115))
        feather=v*v*(3-2*v)
        mid=(hi+lo)/2;half=(lo-hi)*.5*max(.003,feather)
        pts_top.append((xx,mid-half));pts_bottom.append((xx,mid+half))
    c.new_sub_path()
    c.move_to(*pts_top[0]);[c.line_to(*p) for p in pts_top[1:]]
    for p in reversed(pts_bottom):c.line_to(*p)
    c.close_path()
    return pts_top,pts_bottom


@lru_cache(maxsize=1)
def limestone_texture():
    """A seamless-looking faceted mineral grain, procedural and reusable."""
    rng=np.random.default_rng(5282)
    ah,aw=540,960
    l=np.zeros((ah,aw),np.float32)
    for w,h,weight in ((12,7,.48),(36,20,.23),(125,71,.15),(480,270,.08)):
        data=(rng.random((h,w))*255).astype('uint8')
        img=Image.fromarray(data,'L').resize((aw,ah),Image.Resampling.BICUBIC)
        l+=(np.asarray(img,dtype=np.float32)-128)/128*weight
    yy,xx=np.mgrid[0:ah,0:aw]
    laminate=np.sin(yy*.23+9*l+3*np.sin(xx*.034))*.025
    grain=np.clip(l+laminate,-.52,.52)
    col=np.zeros((ah,aw,3),dtype='uint8')
    for k,base in enumerate((165,163,147)):
        col[:,:,k]=np.clip(base+grain*57,0,255).astype('uint8')
    im=Image.fromarray(col,'RGB').resize((W,H),Image.Resampling.BICUBIC)
    rgba=np.array(im.convert('RGBA'))[:,:,[2,1,0,3]].copy()
    surf=cairo.ImageSurface.create_for_data(memoryview(rgba),cairo.FORMAT_ARGB32,W,H)
    return surf,rgba


def rock_path(c):
    c.new_sub_path();c.move_to(85,922)
    for x in range(85,1844,9):c.line_to(x,terrain_y(x))
    c.line_to(1845,922);c.close_path()


def rock_mass(c):
    rock_path(c)
    grd=cairo.LinearGradient(0,363,0,950)
    grd.add_color_stop_rgb(0,.71,.71,.65)
    grd.add_color_stop_rgb(.5,.51,.53,.49)
    grd.add_color_stop_rgb(1,.27,.33,.33)
    c.set_source(grd);c.fill()
    c.save();rock_path(c);c.clip()
    c.set_source_surface(limestone_texture()[0],0,0);c.paint_with_alpha(.42)
    for n in range(18):
        y=402+29*n
        c.set_line_width(1.3 if n%4 else 2.2)
        c.set_source_rgba(.10,.15,.15,.17 if n%4 else .31)
        c.move_to(86,y)
        for x in range(100,1840,15):
            c.line_to(x,y+5*math.sin(x*.009+n*.26))
        c.stroke()
    c.restore()
    c.set_source_rgba(*SAGE,.59);c.set_line_width(1.5)
    c.move_to(85,terrain_y(85))
    for x in range(94,1844,9):c.line_to(x,terrain_y(x))
    c.stroke()


def calcite(c,x,y,length,width,hang=True,a=1):
    if length<=0 or a<.03:return
    P.speleothem(c,x,y,length,width,hang,a)
    # A second thin pendant accent introduces micro-texture, not an icon.
    direction=1 if hang else -1
    c.set_source_rgba(.98,.90,.73,.12*a)
    c.set_line_width(.8)
    c.move_to(x-1,y)
    c.curve_to(x-5,y+direction*length*.41,x-3,y+direction*length*.69,
               x,y+direction*length*.93)
    c.stroke()


def cave_wall(c,top,bottom,grow,roof,t):
    """Inset mineral ribbons and occlusion convert a flat black hole into a
    three-dimensional chamber; everything is clipped to its true outline."""
    cave_cutout(c,grow,roof);c.save();c.clip()
    # The left wall is wet and warmer, while the rear falls into cool shadow.
    gg=cairo.RadialGradient(690,617,20,690,617,555)
    gg.add_color_stop_rgba(0,.54,.45,.32,.17)
    gg.add_color_stop_rgba(.45,.27,.31,.26,.075)
    gg.add_color_stop_rgba(1,.07,.16,.18,0)
    c.set_source(gg);c.paint()
    for i in range(6):
        ds=5+i*(9+1.8*i)
        # Erosion lines have discontinuities at the chamber junctions.
        C=P.BONE if i%2==0 else P.SAGE
        c.set_source_rgba(*C,(.38 if i<2 else .24)/(1+i*.25))
        c.set_line_width(3.8 if i<2 else 2.3)
        c.move_to(top[0][0],top[0][1]+ds)
        for j,(x,y) in enumerate(top[1:],1):
            c.line_to(x,y+ds+3.5*math.sin(j*.23+i*1.1))
        c.stroke()
    for i in range(4):
        c.set_source_rgba(*P.BONE,.16/(1+i*.19));c.set_line_width(2.6)
        ds=7+i*12
        c.move_to(bottom[0][0],bottom[0][1]-ds)
        for j,(x,y) in enumerate(bottom[1:],1):
            c.line_to(x,y-ds+2.5*math.sin(j*.31+i))
        c.stroke()
    # A handful of distant columns recede into the second layer of the cave.
    for x in (685,812,1079,1350):
        hi,lo=cave_bounds(x,1,roof)
        r=cairo.LinearGradient(x-22,0,x+24,0)
        r.add_color_stop_rgba(0,.30,.36,.32,.27)
        r.add_color_stop_rgba(.48,.62,.61,.52,.20)
        r.add_color_stop_rgba(1,.22,.30,.32,.24)
        c.set_source(r)
        c.move_to(x-19,hi+21)
        c.curve_to(x-26,(hi+lo)*.55,x-13,lo-50,x-27,lo-8)
        c.line_to(x+17,lo-6)
        c.curve_to(x+11,lo-60,x+17,(hi+lo)*.55,x+13,hi+29)
        c.close_path();c.fill()
    # Moving motes: a very restrained parallax layer in front of the wall.
    rr=random.Random(63)
    for k in range(86):
        x=rr.uniform(490,1430);y=rr.uniform(570,823)
        a=.025+.075*(.5+.5*math.sin(k*3.3+t*.63))
        c.set_source_rgba(*PAPER,a)
        c.arc(x+4*math.sin(t*.19+k),y-3*math.cos(t*.2+k),rr.uniform(.6,1.5),0,math.tau)
        c.fill()
    c.restore()


def draw_subsurface(c,t,D,collapse=False):
    grow=1 if collapse else P.E(t,.7,D*.39)
    withdrawal=1 if collapse else P.E(t,D*.36,D*.57)
    spele=0 if collapse else P.E(t,D*.51,D*.93)
    fall=P.E(t,.50,D*.78) if collapse else 0
    roof=fall*185
    rock_mass(c)
    top,bot=cave_cutout(c,grow,roof)
    gr=cairo.RadialGradient(1010,713,24,1010,713,720)
    gr.add_color_stop_rgb(0,.023,.058,.069)
    gr.add_color_stop_rgb(.47,.048,.094,.107)
    gr.add_color_stop_rgb(1,.095,.146,.151)
    c.set_source(gr);c.fill()
    cave_wall(c,top,bot,grow,roof,t)
    # Layered erosion edge: shadow, ochre calcite, then one thin wet highlight.
    cave_cutout(c,grow,roof)
    c.set_source_rgba(.07,.11,.12,.42);c.set_line_width(12);c.stroke()
    cave_cutout(c,grow,roof)
    c.set_source_rgba(.91,.77,.54,.38);c.set_line_width(2.4);c.stroke()
    # Subtle suspended sediment and glints give the chamber internal depth.
    cave_cutout(c,grow,roof);c.save();c.clip()
    rr=random.Random(338)
    for k in range(140):
        x=rr.uniform(470,1440);y=rr.uniform(490,855)
        alpha=.06+ .12*(.5+.5*math.sin(k*7.3+t*.8))
        c.set_source_rgba(*PAPER,alpha)
        c.arc(x+3*math.sin(t*.24+k),y-2*math.sin(t*.18+k),rr.uniform(.5,1.8),0,math.tau)
        c.fill()
    # Moving underwater relief, a perspective receding into the darkness.
    water_y=P.M(728,817,withdrawal)
    c.move_to(400,922);c.line_to(400,water_y)
    for x in range(405,1540,14):
        c.line_to(x,water_y+3*math.sin(x*.018+t*.96)+2*math.sin(x*.035-t*.57))
    c.line_to(1540,922);c.close_path()
    gr=cairo.LinearGradient(0,water_y,0,880)
    gr.add_color_stop_rgba(0,.24,.52,.53,.72)
    gr.add_color_stop_rgba(1,.018,.12,.17,.95)
    c.set_source(gr);c.fill()
    for n in range(6):
        c.set_source_rgba(*AQUA,.26/(1+n*.23))
        c.set_line_width(.7+.15*n)
        c.move_to(493,water_y+4+n*6)
        for x in range(507,1510,16):
            c.line_to(x,water_y+4+n*6+2.3*math.sin(x*.027+t*(.53+n*.19)))
        c.stroke()
    c.restore()
    # Channels lit from within, with packets descending at different speeds.
    rr=random.Random(92)
    for k in range(12):
        xx=311+123*k+rr.uniform(-14,14)
        yy=terrain_y(xx)
        ex=xx+rr.uniform(-41,41)
        cy=603+rr.uniform(-29,40)
        c.set_source_rgba(.15,.26,.28,.40);c.set_line_width(4.5)
        c.move_to(xx,yy)
        c.curve_to(xx-18,yy+103,ex+23,cy-75,ex,cy);c.stroke()
        c.set_source_rgba(*AQUA,.32+.32*grow);c.set_line_width(1.6)
        c.move_to(xx,yy)
        c.curve_to(xx-18,yy+103,ex+23,cy-75,ex,cy);c.stroke()
        ph=(k*.24+t*.15)%1
        c.set_source_rgba(*AQUA,.75*grow)
        c.arc(P.M(xx,ex,ph),P.M(yy,cy,ph),2.2,0,math.tau);c.fill()
    if not collapse:
        rr=random.Random(45)
        for k in range(12):
            x=579+k*67+rr.uniform(-20,17)
            ceiling,floor=cave_bounds(x)
            length=spele*rr.uniform(27,109)
            calcite(c,x,ceiling+5,length,rr.uniform(6,17),True,.68*spele)
            if k%2==0:
                sy=ceiling+length+((t*61+k*19)%72)
                c.set_source_rgba(*AQUA,.69*spele)
                c.arc(x,sy,2.5,0,math.tau);c.fill()
            if k%2==0 or k in (5,9):
                calcite(c,x+7,floor-5,spele*rr.uniform(23,71),rr.uniform(8,19),False,.64*spele)
    else:
        # A roof section gives way. The negative-space shaft joins the chamber
        # to the surface; pieces fall on easing trajectories, dust hangs behind.
        cy=terrain_y(960)
        if fall>.02:
            lx=960-151*fall;rx=960+151*fall
            # Fractured, almost vertical sides; no large black triangle.
            c.move_to(lx,terrain_y(lx)-3)
            c.line_to(rx,terrain_y(rx)-3)
            c.curve_to(rx+9,459,rx+22,542,rx+49,676)
            c.line_to(lx-48,676)
            c.curve_to(lx-26,534,lx-12,468,lx,terrain_y(lx)-3)
            c.close_path()
            gr=cairo.LinearGradient(lx,385,rx+45,645)
            gr.add_color_stop_rgb(0,.047,.078,.083)
            gr.add_color_stop_rgb(.56,.021,.055,.068)
            gr.add_color_stop_rgb(1,.040,.067,.071)
            c.set_source(gr);c.fill()
            # Volumetric skylight loses energy with depth. Tiers carved into
            # the shaft wall catch the same warm light at successively lower
            # intensities, making the pit read as volume rather than a polygon.
            light=cairo.LinearGradient(0,cy,0,692)
            light.add_color_stop_rgba(0,.88,.78,.56,.23*fall)
            light.add_color_stop_rgba(.44,.49,.57,.51,.065*fall)
            light.add_color_stop_rgba(1,.12,.23,.25,0)
            c.move_to(lx+15,terrain_y(lx)+2);c.line_to(rx-15,terrain_y(rx)+2)
            c.line_to(rx-24,674);c.line_to(lx+24,674);c.close_path()
            c.set_source(light);c.fill()
            for idx in range(5):
                yy=cy+35+idx*52
                if yy>673:break
                strength=(.34-.045*idx)*fall
                for sx,side in ((lx,1),(rx,-1)):
                    inside=sx+side*(11+idx*7)
                    P.line(c,(inside,yy),(inside+side*(24+idx*4),yy+8),
                           BONE,strength,1.4)
                    P.line(c,(inside+side*(24+idx*4),yy+8),
                           (inside+side*(14+idx*4),yy+25),SAGE,strength*.6,1)
            # A fractured lime edge survives at both lips of the opening.
            for sx,direction in ((lx,-1),(rx,1)):
                rim=[(sx-19*direction,terrain_y(sx)-3),
                     (sx,terrain_y(sx)-7),
                     (sx+10*direction,terrain_y(sx)+7),
                     (sx+21*direction,terrain_y(sx)+17)]
                c.set_source_rgba(*BONE,.67*fall)
                c.set_line_width(2.1);c.move_to(*rim[0]);
                for pt in rim[1:]:c.line_to(*pt)
                c.stroke()
        gl=cairo.RadialGradient(955,cy,9,955,cy,150)
        gl.add_color_stop_rgba(0,.81,.67,.45,.20*fall)
        gl.add_color_stop_rgba(1,.81,.67,.45,0)
        c.set_source(gl);c.arc(955,cy,150,0,math.tau);c.fill()
        for n in range(36):
            r=random.Random(n*83+4)
            st=r.uniform(.22,D*.75)
            ph=P.E(t,st,st+.92)
            x=830+r.uniform(-32,286)
            y=P.M(r.uniform(355,588),755+r.uniform(-16,76),ph**1.4)
            radius=r.uniform(4,16)
            col=(.58+.08*r.random(),.59+.05*r.random(),.51+.07*r.random())
            P.poly(c,[(x-radius,y),(x+radius*.5,y-radius*.4),
                      (x+radius,y+radius*.5),(x,y+radius)],col,.8)


def anim_cave(c,t,D,collapse=False):
    P.bg(c)
    c.save();sc=1.0+.045*(t/max(D,.01))
    c.translate(960,600);c.scale(sc,sc)
    c.translate(-960-6*math.sin(t*.24),-600-3*math.cos(t*.2))
    draw_subsurface(c,t,D,collapse)
    c.restore()
    if not collapse:
        P.mast(c,'地下世界','CAVES / UNDERGROUND RIVERS',t,D,'09')
        P.marker(c,569,702,'01','地下河','SUBTERRANEAN STREAM',P.E(t,2.2,4.2),-1)
        a=P.E(t,D*.64,D*.78)
        P.marker(c,1268,613,'02','钟乳石与石笋','MINERAL PRECIPITATION',a,1)
        P.mono(c,'WATER  /  LIMESTONE  /  TIME',143,893,15,MUTED,.81,track=1.2)
    else:
        P.mast(c,'洞顶崩塌','COLLAPSE / TIANKENG',t,D,'10')
        a=P.E(t,D*.47,D*.79)
        P.marker(c,1049,570,'','天坑','ROOF COLLAPSE',a,1)
        P.txt(c,'600+ 米',1512,786,53,GOLD,P.E(t,D*.68,D*.83),serif=True,align='r')
        P.mono(c,'XIAOZHAI TIANKENG / DEPTH',1511,822,14,PAPER,a,'r',.9)
        P.mono(c,'SCHEMATIC CROSS SECTION / NOT TO SCALE',142,893,14,MUTED,.76,track=.8)
