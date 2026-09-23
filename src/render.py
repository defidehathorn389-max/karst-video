# -*- coding: utf-8 -*-
"""喀斯特 —— 原创地理科普视频渲染器 (1920x1080, 24fps)"""
import cairo, math, json, random, subprocess, sys, os, re
import numpy as np
from PIL import Image, ImageFilter
from functools import lru_cache

W, H, FPS = 1920, 1080, 24
FF = '/usr/local/lib/python3.13/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
SERIF, SANS = 'Noto Serif CJK SC', 'Noto Sans CJK SC'
GOLD = (0.91, 0.69, 0.29); WHITE = (1, 1, 1); NAVY = (0.05, 0.09, 0.12)
WATER = (0.31, 0.70, 0.85); LIME = (0.80, 0.77, 0.70)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- utils
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def eio(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def seg(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def lerp(a, b, k): return a + (b - a) * k

def dur_of(f):
    out = subprocess.run([FF, '-i', f], capture_output=True, text=True).stderr
    h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)

def font(c, size, serif=False, bold=False):
    c.select_font_face(SERIF if serif else SANS, cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)

def text(c, s, x, y, size, color=WHITE, alpha=1, serif=False, bold=False, align='l', shadow=False, spacing=0):
    font(c, size, serif, bold)
    if spacing:
        widths = [c.text_extents(ch).x_advance + spacing for ch in s]
        tw = sum(widths) - spacing
    else:
        tw = c.text_extents(s).x_advance
    if align == 'c': x -= tw / 2
    elif align == 'r': x -= tw
    def draw(ox, oy, col, a):
        c.set_source_rgba(*col, a)
        if spacing:
            xx = x + ox
            for ch, w in zip(s, widths):
                c.move_to(xx, y + oy); c.show_text(ch); xx += w
        else:
            c.move_to(x + ox, y + oy); c.show_text(s)
    if shadow:
        c.save()
        c.move_to(x, y); c.text_path(s) if not spacing else None
        c.new_path()
        for d in ((2, 2), (0, 3), (3, 0)): draw(d[0], d[1], (0, 0, 0), alpha * 0.55)
        c.restore()
    draw(0, 0, color, alpha)
    return tw

def chem(c, s, x, y, size, color=WHITE, alpha=1, align='l'):
    """化学式：字母后的数字自动变下标"""
    toks = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isdigit() and i > 0 and (s[i - 1].isalpha() or s[i - 1] == ')'):
            toks.append((ch, True))
        else:
            toks.append((ch, False))
        i += 1
    font(c, size, False, True)
    def wid(tk): font(c, size * (0.62 if tk[1] else 1), False, True); return c.text_extents(tk[0]).x_advance
    tw = sum(wid(t) for t in toks)
    if align == 'c': x -= tw / 2
    xx = x
    c.set_source_rgba(*color, alpha)
    for tk in toks:
        font(c, size * (0.62 if tk[1] else 1), False, True)
        c.move_to(xx, y + (size * 0.22 if tk[1] else 0)); c.show_text(tk[0])
        xx += c.text_extents(tk[0]).x_advance
    return tw

def rrect(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def bg_dark(c, t=0):
    g = cairo.RadialGradient(W / 2, H * 0.45, 100, W / 2, H / 2, W * 0.75)
    g.add_color_stop_rgb(0, 0.09, 0.14, 0.18); g.add_color_stop_rgb(1, 0.02, 0.04, 0.06)
    c.set_source(g); c.paint()
    # 细网格
    c.set_source_rgba(1, 1, 1, 0.035); c.set_line_width(1)
    for x in range(0, W, 80): c.move_to(x, 0); c.line_to(x, H)
    for y in range(0, H, 80): c.move_to(0, y); c.line_to(W, y)
    c.stroke()

def panel_title(c, zh, en, a, x=110, y=130):
    c.set_source_rgba(*GOLD, a); c.rectangle(x, y - 46, 6, 58); c.fill()
    text(c, zh, x + 26, y, 46, WHITE, a, serif=True, bold=True)
    text(c, en, x + 28, y + 40, 20, GOLD, a * 0.9, spacing=3)

def label_line(c, x, y, x2, y2, s, a, size=30, color=WHITE, dot=True):
    c.set_source_rgba(*GOLD, a); c.set_line_width(2)
    c.move_to(x, y); c.line_to(x2, y2); c.stroke()
    if dot: c.arc(x, y, 6, 0, 2 * math.pi); c.fill()
    text(c, s, x2 + (12 if x2 >= x else -12), y2 + size * 0.35, size, color, a, bold=True, align='l' if x2 >= x else 'r', shadow=True)

# ---------------------------------------------------------------- images
@lru_cache(maxsize=3)
def load_surface(path, blur=0):
    im = Image.open(path).convert('RGB')
    s = max(W * 1.18 / im.width, H * 1.18 / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    arr = np.array(im.convert('RGBA'))[:, :, [2, 1, 0, 3]].copy()
    surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, im.width, im.height)
    return surf, arr

def draw_photo(c, path, k, move='in', blur=0, dark=0.0):
    surf, _ = load_surface(path, blur)
    iw, ih = surf.get_width(), surf.get_height()
    base = max(W / iw, H / ih)
    k = ease(k) * 0.6 + k * 0.4
    z0, z1, dx0, dx1, dy0, dy1 = {
        'in': (1.0, 1.12, 0, 0, 0, 0), 'out': (1.12, 1.0, 0, 0, 0, 0),
        'left': (1.08, 1.08, 0.5, -0.5, 0, 0), 'right': (1.08, 1.08, -0.5, 0.5, 0, 0),
        'up': (1.08, 1.1, 0, 0, 0.45, -0.45), 'down': (1.1, 1.08, 0, 0, -0.45, 0.45),
    }[move]
    z = base * lerp(z0, z1, k)
    sw, sh = iw * z, ih * z
    ox = (W - sw) / 2 + lerp(dx0, dx1, k) * max(0, (sw - W) / 2)
    oy = (H - sh) / 2 + lerp(dy0, dy1, k) * max(0, (sh - H) / 2)
    c.save(); c.translate(ox, oy); c.scale(z, z)
    c.set_source_surface(surf, 0, 0); c.get_source().set_filter(cairo.FILTER_BILINEAR)
    c.paint(); c.restore()
    if dark: c.set_source_rgba(0, 0, 0, dark); c.paint()

CREDITS = {}
for line in open('credits.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) >= 4: CREDITS[p[0]] = (p[1].replace('File:', ''), p[2], p[3])

def credit_tag(c, path, a=1):
    if path.startswith('img/ai_'):
        s = 'AI 生成示意图'
    elif path in CREDITS and path.startswith('clips/'):
        ti, au, lic = CREDITS[path]
        s = f'视频 © {au} / {lic} / Wikimedia Commons'
    elif path in CREDITS:
        _, au, lic = CREDITS[path]
        au = au.split('\n')[0][:40]
        s = f'© {au} / {lic} / Wikimedia Commons'
    else:
        return
    text(c, s, W - 40, 50, 17, WHITE, 0.6 * a, align='r', shadow=True)

def loc_tag(c, zh, en, a):
    if a <= 0: return
    x, y = 90, 130
    c.set_source_rgba(*GOLD, a); c.rectangle(x, y - 40, 5, 70); c.fill()
    text(c, zh, x + 22, y, 40, WHITE, a, serif=True, bold=True, shadow=True)
    text(c, en, x + 24, y + 30, 18, WHITE, a * 0.85, spacing=2, shadow=True)

# ---------------------------------------------------------------- maps
def load_geo(fn, key=None):
    d = json.load(open(fn, encoding='utf-8'))
    out = []
    for f in d['features']:
        g = f['geometry']
        if g is None: continue
        polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        out.append((f['properties'], polys))
    return out

WORLD = load_geo('world50.json')
PROV = load_geo('c.json')

class Proj:
    def __init__(s, lon0, lon1, lat0, lat1, box=(0, 0, W, H)):
        s.lon0, s.lon1, s.lat0, s.lat1 = lon0, lon1, lat0, lat1
        x, y, w, h = box
        clat = math.cos(math.radians((lat0 + lat1) / 2))
        sx = w / ((lon1 - lon0) * clat); sy = h / (lat1 - lat0)
        s.k = min(sx, sy); s.clat = clat
        s.cx, s.cy = x + w / 2, y + h / 2
        s.mlon, s.mlat = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    def __call__(s, lon, lat):
        return s.cx + (lon - s.mlon) * s.clat * s.k, s.cy - (lat - s.mlat) * s.k

def poly_path(c, P, polys, dlon=0, dlat=0):
    for poly in polys:
        for ring in poly:
            for i, (lo, la) in enumerate(ring):
                x, y = P(lo + dlon, la + dlat)
                (c.move_to if i == 0 else c.line_to)(x, y)
            c.close_path()

def lerp_proj(p1, p2, k):
    return Proj(lerp(p1[0], p2[0], k), lerp(p1[1], p2[1], k), lerp(p1[2], p2[2], k), lerp(p1[3], p2[3], k))

def draw_world(c, P, fill=(0.16, 0.22, 0.26), stroke=(0.35, 0.45, 0.5), a=1):
    for props, polys in WORLD:
        poly_path(c, P, polys)
    c.set_source_rgba(*fill, a); c.fill_preserve()
    c.set_source_rgba(*stroke, 0.6 * a); c.set_line_width(1); c.stroke()

def find_country(name):
    for props, polys in WORLD:
        if props.get('NAME') == name: return polys

def pulse(c, x, y, t, a=1, col=GOLD):
    for i in range(2):
        ph = (t * 0.8 + i * 0.5) % 1
        c.set_source_rgba(*col, a * (1 - ph)); c.set_line_width(3)
        c.arc(x, y, 10 + ph * 50, 0, 2 * math.pi); c.stroke()
    c.set_source_rgba(*col, a); c.arc(x, y, 9, 0, 2 * math.pi); c.fill()

# ---------------------------------------------------------------- animations
def anim_world(c, t, D):
    bg_dark(c)
    pA = (-15, 150, 5, 68)
    k = seg(t, D * 0.55, D * 0.85)
    P = lerp_proj(pA, (70, 140, 12, 52), k)
    draw_world(c, P)
    slo = find_country('Slovenia'); chn = find_country('China')
    a1 = seg(t, 1, 2.5)
    poly_path(c, P, slo); c.set_source_rgba(*GOLD, a1); c.fill()
    sx, sy = P(14.8, 46.0)
    if a1 > 0 and k < 0.6:
        pulse(c, sx, sy, t, a1 * (1 - k))
        label_line(c, sx, sy, sx - 60, sy - 160, '斯洛文尼亚 · 喀斯特高原 (Kras)', a1 * (1 - k * 1.6), 30)
    a2 = seg(t, D * 0.3, D * 0.5)
    if a2 > 0:
        ex, ey = P(106, 26)
        n = int(60 * a2)
        c.set_source_rgba(*GOLD, 0.9); c.set_line_width(3); c.set_dash([10, 8])
        for i in range(n + 1):
            u = i / 60
            lo = lerp(14.8, 106, u); la = lerp(46, 26, u) + math.sin(u * math.pi) * 14
            x, y = P(lo, la); (c.move_to if i == 0 else c.line_to)(x, y)
        c.stroke(); c.set_dash([])
    a3 = seg(t, D * 0.45, D * 0.6)
    poly_path(c, P, chn); c.set_source_rgba(*GOLD, 0.25 * a3); c.fill_preserve()
    c.set_source_rgba(*GOLD, a3); c.set_line_width(2); c.stroke()
    a4 = seg(t, D * 0.8, D * 0.95)
    if a4 > 0:
        cx, cy = P(106, 26); pulse(c, cx, cy, t, a4)
        label_line(c, cx, cy, cx + 120, cy - 120, '中国南方喀斯特', a4, 34)
    panel_title(c, '“喀斯特”一词的由来', 'KARST  ←  KRAS', seg(t, 0.2, 1.2))

SITES = [('云南石林', 103.32, 24.8, -1), ('贵州荔波', 107.9, 25.4, 1), ('重庆武隆', 107.76, 29.33, -1),
         ('广西桂林', 110.29, 25.27, 1), ('重庆奉节 · 小寨天坑', 109.55, 30.73, 1)]

def anim_china(c, t, D):
    bg_dark(c)
    k = seg(t, 0, D * 0.35)
    P = lerp_proj((73, 136, 16, 54), (97, 116, 20.5, 33), k)
    for props, polys in PROV:
        poly_path(c, P, polys)
    c.set_source_rgb(0.16, 0.22, 0.26); c.fill_preserve()
    c.set_source_rgba(0.4, 0.5, 0.55, 0.7); c.set_line_width(1.2); c.stroke()
    core = {'52': 0, '45': 0.15, '53': 0.3, '50': 0.45}
    names = {'52': ('贵州', 106.7, 26.8), '45': ('广西', 108.8, 23.6), '53': ('云南', 101.5, 24.5), '50': ('重庆', 107.8, 30.0)}
    for props, polys in PROV:
        pid = props['id']
        if pid in core:
            a = seg(t, D * (0.3 + core[pid] * 0.35), D * (0.38 + core[pid] * 0.35))
            poly_path(c, P, polys); c.set_source_rgba(*GOLD, 0.55 * a); c.fill_preserve()
            c.set_source_rgba(*GOLD, a); c.set_line_width(2.5); c.stroke()
            nm, lo, la = names[pid]; x, y = P(lo, la)
            text(c, nm, x, y, 44 * lerp(0.6, 1, k), WHITE, a * 0.9, serif=True, bold=True, align='c', shadow=True)
    for i, (nm, lo, la, side) in enumerate(SITES):
        a = seg(t, D * (0.62 + i * 0.05), D * (0.67 + i * 0.05))
        if a <= 0: continue
        x, y = P(lo, la)
        pulse(c, x, y, t + i * 0.3, a, WATER)
        text(c, nm, x + side * 22, y + 10, 28, WATER, a, bold=True, align='l' if side > 0 else 'r', shadow=True)
    a = seg(t, D * 0.55, D * 0.65)
    if a > 0:
        c.set_source_rgba(0, 0, 0, 0.55 * a); rrect(c, 1330, 700, 500, 250, 16); c.fill()
        text(c, '中国西南裸露喀斯特面积', 1370, 770, 30, WHITE, a)
        text(c, '> 50', 1370, 880, 110, GOLD, a, serif=True, bold=True)
        text(c, '万 km²', 1590, 880, 44, GOLD, a, bold=True)
    panel_title(c, '中国南方喀斯特', 'SOUTH CHINA KARST', seg(t, 0.2, 1.2))

def layer_color(i):
    r = random.Random(i * 7 + 3)
    v = r.uniform(-0.07, 0.07)
    return (0.78 + v, 0.74 + v, 0.64 + v * 0.8)

def anim_deposit(c, t, D):
    bg_dark(c)
    x0, x1, yb, ytop = 260, 1660, 960, 260
    # 海水
    g = cairo.LinearGradient(0, ytop, 0, yb)
    g.add_color_stop_rgb(0, 0.18, 0.55, 0.72); g.add_color_stop_rgb(1, 0.04, 0.2, 0.32)
    c.set_source(g); c.rectangle(x0, ytop, x1 - x0, yb - ytop); c.fill()
    # 光线
    for i in range(6):
        xx = x0 + 150 + i * 240 + math.sin(t * 0.7 + i) * 20
        c.move_to(xx, ytop); c.line_to(xx + 80, ytop); c.line_to(xx + 200, yb); c.line_to(xx + 60, yb); c.close_path()
        c.set_source_rgba(1, 1, 1, 0.04); c.fill()
    nlay = 14
    prog = seg(t, 2, D - 3)
    fill_h = 520 * prog
    lh = 520 / nlay
    top = yb - fill_h
    for i in range(nlay):
        ly = yb - (i + 1) * lh
        if ly + lh < top: break
        y_start = max(ly, top)
        c.set_source_rgb(*layer_color(i))
        # 波纹顶部
        c.move_to(x0, yb - i * lh)
        c.line_to(x0, y_start)
        for xx in range(x0, x1 + 1, 40):
            c.line_to(xx, y_start + math.sin(xx * 0.02 + i) * 3)
        c.line_to(x1, yb - i * lh); c.close_path(); c.fill()
        # 化石点缀
        r = random.Random(i)
        c.set_source_rgba(0.5, 0.45, 0.38, 0.6)
        for _ in range(9):
            fx = r.uniform(x0 + 20, x1 - 20); fy = r.uniform(ly + 6, ly + lh - 6)
            if fy < y_start: continue
            c.arc(fx, fy, r.uniform(3, 7), math.pi, 2 * math.pi); c.fill()
    # 珊瑚与生物（在沉积顶部）
    r = random.Random(5)
    for j in range(16):
        fx = x0 + 60 + j * 85 + r.uniform(-20, 20)
        hh = r.uniform(30, 70)
        col = [(0.95, 0.5, 0.45), (0.98, 0.75, 0.4), (0.8, 0.45, 0.7)][j % 3]
        c.set_source_rgba(*col, 0.9); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.move_to(fx, top); c.line_to(fx, top - hh)
        c.move_to(fx, top - hh * 0.5); c.line_to(fx - 18, top - hh * 0.9)
        c.move_to(fx, top - hh * 0.4); c.line_to(fx + 16, top - hh * 0.8); c.stroke()
    # 下落的钙质颗粒
    r = random.Random(11)
    for j in range(90):
        sx = r.uniform(x0 + 10, x1 - 10); sp = r.uniform(40, 90); ph = r.uniform(0, 20)
        yy = ytop + ((t * sp + ph * 40) % (top - ytop + 1))
        c.set_source_rgba(1, 1, 1, 0.6); c.arc(sx + math.sin(t + j) * 6, yy, 2.5, 0, 2 * math.pi); c.fill()
    c.set_source_rgba(1, 1, 1, 0.5); c.set_line_width(2); c.rectangle(x0, ytop, x1 - x0, yb - ytop); c.stroke()
    # 计时器
    age = lerp(5.4, 2.5, prog)
    c.set_source_rgba(0, 0, 0, 0.5); rrect(c, 1320, 290, 320, 140, 14); c.fill()
    text(c, '距今', 1345, 335, 26, WHITE, 0.9)
    text(c, f'{age:.1f}', 1345, 410, 76, GOLD, 1, serif=True, bold=True)
    text(c, '亿年', 1520, 410, 34, GOLD, 1, bold=True)
    a = seg(t, D * 0.5, D * 0.6)
    if a > 0:
        mid = (top + yb) / 2
        label_line(c, x1 - 40, mid, x1 + 40, mid - 90, '', a, dot=True)
        text(c, '碳酸盐岩', x1 + 50, mid - 105, 32, WHITE, a, bold=True)
        chem(c, 'CaCO3', x1 + 50, mid - 60, 32, GOLD, a)
        text(c, f'厚达数千米', x0 + 30, yb - 30, 28, (0.25, 0.2, 0.15), a, bold=True)
    panel_title(c, '远古海洋的馈赠', 'MARINE CARBONATE DEPOSITION', seg(t, 0.2, 1.2))

def anim_plates(c, t, D):
    bg_dark(c)
    P = Proj(60, 130, -5, 45)
    draw_world(c, P, a=0.8)
    ind = find_country('India')
    k = seg(t, 1, D * 0.55)
    dl = lerp(-18, 0, k)
    # 印度板块示意（移动）
    c.save()
    poly_path(c, P, ind, 0, dl); c.set_source_rgba(0.85, 0.45, 0.3, 0.85); c.fill()
    c.restore()
    ix, iy = P(79, 20 + dl)
    text(c, '印度板块', ix, iy, 36, WHITE, 1, serif=True, bold=True, align='c', shadow=True)
    # 箭头
    for j in range(3):
        ax, ay = P(74 + j * 5, 12 + dl)
        c.set_source_rgba(*GOLD, 0.9); c.set_line_width(5)
        c.move_to(ax, ay + 60); c.line_to(ax, ay); c.stroke()
        c.move_to(ax - 14, ay + 14); c.line_to(ax, ay - 6); c.line_to(ax + 14, ay + 14); c.close_path(); c.fill()
    ex, ey = P(100, 42)
    text(c, '欧亚板块', ex, ey, 36, WHITE, 0.9, serif=True, bold=True, align='c', shadow=True)
    # 高原隆升
    a = seg(t, D * 0.4, D * 0.7)
    if a > 0:
        tx, ty = P(88, 33); rx = 20 * P.k * P.clat; ry = 5 * P.k
        c.save(); c.translate(tx, ty); c.scale(rx, ry)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0.95, 0.9, 0.85, 0.75 * a); g.add_color_stop_rgba(1, 0.6, 0.45, 0.3, 0)
        c.set_source(g); c.arc(0, 0, 1, 0, 2 * math.pi); c.fill(); c.restore()
        text(c, '青藏高原', tx, ty + 12, 38, (0.15, 0.1, 0.05), a, serif=True, bold=True, align='c')
    a = seg(t, D * 0.65, D * 0.85)
    if a > 0:
        yx, yy = P(105, 26); rx = 6 * P.k * P.clat; ry = 3.2 * P.k
        c.save(); c.translate(yx, yy); c.scale(rx, ry)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, *GOLD, 0.7 * a); g.add_color_stop_rgba(1, *GOLD, 0)
        c.set_source(g); c.arc(0, 0, 1, 0, 2 * math.pi); c.fill(); c.restore()
        label_line(c, yx, yy, yx + 110, yy + 110, '云贵高原', a, 36)
    text(c, '距今数千万年以来', 1810, 1000 - 60, 30, WHITE, seg(t, 0.5, 1.5), align='r')
    panel_title(c, '大地抬升', 'TECTONIC UPLIFT', seg(t, 0.2, 1.2))

def anim_fold(c, t, D):
    bg_dark(c)
    x0, x1 = 160, 1760
    rise = seg(t, 1, D * 0.45)
    bend = seg(t, 1.5, D * 0.5)
    sea = lerp(400, 820, rise)
    # 海
    c.set_source_rgba(0.15, 0.45, 0.62, 0.8 * (1 - rise * 0.85)); c.rectangle(x0, sea, x1 - x0, 1000 - sea); c.fill()
    nl = 9; lh = 38
    base = lerp(900, 600, rise)
    def surf_y(x, i):
        u = (x - x0) / (x1 - x0)
        return base + i * lh - bend * (130 * math.sin(u * math.pi) + 50 * math.sin(u * 3 * math.pi))
    for i in range(nl):
        c.set_source_rgb(*layer_color(i + 20))
        pts = [(x, surf_y(x, i)) for x in range(x0, x1 + 1, 20)]
        c.move_to(*pts[0])
        for p in pts[1:]: c.line_to(*p)
        for x in range(x1, x0 - 1, -20): c.line_to(x, surf_y(x, i + 1))
        c.close_path(); c.fill()
    c.set_source_rgb(0.3, 0.26, 0.22)
    c.move_to(x0, surf_y(x0, nl))
    for x in range(x0, x1 + 1, 20): c.line_to(x, surf_y(x, nl))
    c.line_to(x1, 1080); c.line_to(x0, 1080); c.close_path(); c.fill()
    # 挤压箭头
    a = seg(t, 1.5, 3) * (1 - seg(t, D * 0.6, D * 0.7))
    for sx, d in ((x0 - 20, 1), (x1 + 20, -1)):
        yy = base + 150
        c.set_source_rgba(*GOLD, a); c.set_line_width(8)
        c.move_to(sx - d * 90, yy); c.line_to(sx, yy); c.stroke()
        c.move_to(sx + d * 10, yy); c.line_to(sx - d * 20, yy - 22); c.line_to(sx - d * 20, yy + 22); c.close_path(); c.fill()
    # 裂隙
    cr = seg(t, D * 0.55, D * 0.9)
    if cr > 0:
        r = random.Random(3)
        c.set_source_rgba(0.1, 0.08, 0.06, 0.95); c.set_line_width(3)
        for j in range(22):
            x = x0 + 60 + j * 70 + r.uniform(-15, 15)
            if r.random() > cr * 1.3: continue
            y = surf_y(x, 0); L = r.uniform(120, 300) * cr
            c.move_to(x, y); yy = y
            while yy < y + L:
                yy += 25; x += r.uniform(-8, 8); c.line_to(x, yy)
            c.stroke()
        label_line(c, x0 + 60 + 11 * 70, surf_y(x0 + 830, 0) + 60, x0 + 900, surf_y(x0 + 830, 0) - 150, '纵横交错的裂隙', cr, 34)
    text(c, '海平面', x1 - 10, sea - 12, 24, WATER, 0.9 * (1 - rise * 0.5), align='r')
    panel_title(c, '挤压 · 弯曲 · 断裂', 'FOLDING & JOINTING', seg(t, 0.2, 1.2))

def raindrop(c, x, y, a=1, s=1):
    c.set_source_rgba(*WATER, a)
    c.move_to(x, y - 14 * s); c.curve_to(x + 8 * s, y - 2 * s, x + 8 * s, y + 8 * s, x, y + 8 * s)
    c.curve_to(x - 8 * s, y + 8 * s, x - 8 * s, y - 2 * s, x, y - 14 * s); c.fill()

def anim_chem(c, t, D):
    bg_dark(c)
    # 左侧剖面
    L0, L1 = 120, 900
    sky_b, soil_b = 420, 560
    c.set_source_rgba(0.2, 0.3, 0.38, 0.5); c.rectangle(L0, 200, L1 - L0, sky_b - 200); c.fill()
    c.set_source_rgb(0.33, 0.25, 0.17); c.rectangle(L0, sky_b, L1 - L0, soil_b - sky_b); c.fill()
    c.set_source_rgb(*LIME); c.rectangle(L0, soil_b, L1 - L0, 960 - soil_b); c.fill()
    # 植被
    for j in range(9):
        x = L0 + 40 + j * 90
        c.set_source_rgb(0.25, 0.5, 0.25); c.arc(x, sky_b - 40, 32, 0, 2 * math.pi); c.fill()
        c.set_source_rgb(0.3, 0.22, 0.15); c.rectangle(x - 5, sky_b - 20, 10, 20); c.fill()
        c.set_source_rgba(0.55, 0.42, 0.3, 0.8); c.set_line_width(2)
        for d in (-1, 0, 1):
            c.move_to(x, sky_b); c.curve_to(x + d * 20, sky_b + 40, x + d * 40, sky_b + 70, x + d * 45, soil_b - 20); c.stroke()
    # 裂隙扩大
    wid = lerp(4, 46, seg(t, D * 0.45, D * 0.95))
    for x in (330, 620):
        c.set_source_rgb(0.12, 0.14, 0.16)
        c.move_to(x - wid / 2, soil_b); c.line_to(x - wid * 0.3, 960); c.line_to(x + wid * 0.3, 960); c.line_to(x + wid / 2, soil_b); c.close_path(); c.fill()
        # 裂隙中的水
        c.set_source_rgba(*WATER, 0.5); c.rectangle(x - wid * 0.25, soil_b, wid * 0.5, 400); c.fill()
    # 雨滴
    r = random.Random(1)
    for j in range(40):
        x = r.uniform(L0 + 10, L1 - 10); sp = r.uniform(260, 380); ph = r.uniform(0, 1)
        y = 200 + ((t * sp + ph * 600) % 220)
        raindrop(c, x, y, 0.8, 0.7)
    # CO2 气泡
    r = random.Random(2)
    for j in range(14):
        x = r.uniform(L0 + 20, L1 - 20); y = r.uniform(sky_b + 20, soil_b - 20) - (t * 12 + j * 9) % 60
        c.set_source_rgba(1, 1, 1, 0.5); c.arc(x, y, 5, 0, 2 * math.pi); c.fill()
    text(c, '大气', L0 + 20, 240, 26, WHITE, 0.9); text(c, '土壤', L0 + 20, sky_b + 46, 26, WHITE, 0.9)
    text(c, '石灰岩', L0 + 20, soil_b + 50, 26, (0.2, 0.18, 0.15), 0.9, bold=True)
    c.set_source_rgba(1, 1, 1, 0.5); c.set_line_width(2); c.rectangle(L0, 200, L1 - L0, 760); c.stroke()
    # 右侧方程
    X = 1000
    steps = [
        (0.08, '① 雨水溶解大气与土壤中的二氧化碳', ['H2O + CO2 → H2CO3'], '碳酸'),
        (0.40, '② 碳酸与石灰岩反应', ['CaCO3 + H2CO3 → Ca(HCO3)2'], '可溶的碳酸氢钙，被水带走'),
    ]
    y = 330
    for st, title, eqs, note in steps:
        a = seg(t, D * st, D * st + 1.5)
        text(c, title, X, y, 32, WHITE, a, bold=True)
        for e in eqs:
            c.set_source_rgba(0, 0, 0, 0.4 * a); rrect(c, X - 10, y + 30, 820, 100, 12); c.fill()
            chem(c, e, X + 20, y + 100, 50, GOLD, a)
        text(c, note, X + 20, y + 175, 28, WATER, a)
        y += 280
    a = seg(t, D * 0.75, D * 0.85)
    text(c, '溶蚀 · Dissolution', X, 900, 44, WHITE, a, serif=True, bold=True)
    panel_title(c, '水的雕刻', 'CHEMISTRY OF KARST', seg(t, 0.2, 1.2))

def icon_sun(c, x, y, a):
    c.set_source_rgba(0.98, 0.7, 0.25, a); c.arc(x, y, 40, 0, 2 * math.pi); c.fill()
    c.set_line_width(6)
    for i in range(8):
        an = i * math.pi / 4
        c.move_to(x + math.cos(an) * 55, y + math.sin(an) * 55); c.line_to(x + math.cos(an) * 75, y + math.sin(an) * 75)
    c.stroke()
def icon_rain(c, x, y, a, t):
    c.set_source_rgba(0.85, 0.9, 0.95, a)
    for dx, dy, r in ((-30, 0, 30), (10, -15, 38), (45, 5, 26)): c.arc(x + dx, y + dy, r, 0, 2 * math.pi); c.fill()
    c.rectangle(x - 55, y, 125, 30); c.fill()
    for j in range(5): raindrop(c, x - 40 + j * 25, y + 60 + (t * 90 + j * 13) % 40, a, 0.9)
def icon_tree(c, x, y, a):
    c.set_source_rgba(0.45, 0.32, 0.2, a); c.rectangle(x - 8, y + 10, 16, 60); c.fill()
    c.set_source_rgba(0.3, 0.65, 0.35, a)
    for dx, dy, r in ((0, -20, 45), (-30, 10, 32), (30, 10, 32)): c.arc(x + dx, y + dy, r, 0, 2 * math.pi); c.fill()

def anim_rate(c, t, D):
    bg_dark(c)
    a = seg(t, 0.5, 1.8)
    text(c, '溶蚀速度', W / 2, 300, 40, WHITE, a, align='c', bold=True)
    text(c, '每 1000 年 ≈ 几十毫米', W / 2, 420, 84, GOLD, a, serif=True, bold=True, align='c')
    items = [('高温', icon_sun), ('多雨', icon_rain), ('植被茂盛', icon_tree)]
    for i, (nm, fn) in enumerate(items):
        b = seg(t, D * (0.35 + i * 0.13), D * (0.35 + i * 0.13) + 1)
        x = W / 2 + (i - 1) * 420; y = 660
        c.set_source_rgba(1, 1, 1, 0.06 * b); c.arc(x, y, 120, 0, 2 * math.pi); c.fill()
        if fn is icon_rain: fn(c, x, y - 20, b, t)
        else: fn(c, x, y, b)
        text(c, nm, x, y + 190, 40, WHITE, b, bold=True, align='c')
    text(c, '+  季风气候  +  活跃的生物作用', W / 2, 980, 32, WATER, seg(t, D * 0.8, D * 0.9), align='c')

# 地貌演化剖面
def stage_profile(u, st):
    if st == 0:  # 石林：高原被深窄沟分割
        h = 0.62
        f = (u * 34) % 1
        if f < 0.18: h -= 0.32 * (1 - abs(f - 0.09) / 0.09) ** 0.5
        return h + 0.01 * math.sin(u * 90)
    if st == 1:  # 峰丛
        n = 7; f = (u * n) % 1; j = int(u * n)
        hv = [0.30, 0.24, 0.33, 0.27, 0.31, 0.22, 0.29][min(j, 6)]
        d = abs(f - 0.5) * 2
        return 0.34 + hv * max(0, 1 - d ** 1.6) ** 0.8
    if st == 2:  # 峰林
        n = 6; f = (u * n) % 1
        d = abs(f - 0.5)
        return 0.14 + (0.42 * (1 - (d / 0.2) ** 3) if d < 0.2 else 0)
    # 孤峰
    h = 0.1
    for c0 in (0.3, 0.72):
        d = abs(u - c0)
        if d < 0.04: h += 0.3 * (1 - (d / 0.04) ** 3)
    return h

def anim_evolve(c, t, D):
    bg_dark(c)
    names = ['石林', '峰丛', '峰林', '孤峰']
    ens = ['STONE FOREST', 'FENGCONG · PEAK CLUSTER', 'FENGLIN · PEAK FOREST', 'GUFENG · ISOLATED PEAK']
    T = [0.02, 13 / 42, 28 / 42, 41 / 42]
    tr = 4 / 42
    x0, x1, yb, HH = 140, 1780, 900, 900
    # 当前 stage 插值
    s = 0.0
    for i in range(1, 4):
        s += seg(t, D * (T[i] - tr), D * T[i])
    i0 = min(3, int(s)); fr = s - i0; i1 = min(3, i0 + 1)
    # 天空
    g = cairo.LinearGradient(0, 200, 0, yb)
    g.add_color_stop_rgb(0, 0.28, 0.42, 0.55); g.add_color_stop_rgb(1, 0.7, 0.75, 0.75)
    c.set_source(g); c.rectangle(x0, 200, x1 - x0, yb - 200); c.fill()
    N = 400
    pts = []
    for k in range(N + 1):
        u = k / N
        h = lerp(stage_profile(u, i0), stage_profile(u, i1), fr)
        pts.append((x0 + u * (x1 - x0), yb - h * HH))
    # 岩体
    c.move_to(x0, 1000)
    for p in pts: c.line_to(*p)
    c.line_to(x1, 1000); c.close_path()
    g = cairo.LinearGradient(0, 300, 0, 1000)
    g.add_color_stop_rgb(0, 0.78, 0.76, 0.7); g.add_color_stop_rgb(1, 0.45, 0.42, 0.38)
    c.set_source(g); c.fill()
    # 层理线
    c.save(); c.move_to(x0, 1000)
    for p in pts: c.line_to(*p)
    c.line_to(x1, 1000); c.close_path(); c.clip()
    c.set_source_rgba(0.3, 0.27, 0.22, 0.25); c.set_line_width(2)
    for yy in range(300, 1000, 36): c.move_to(x0, yy); c.line_to(x1, yy + 10)
    c.stroke(); c.restore()
    # 植被顶
    c.set_source_rgba(0.28, 0.5, 0.28, 0.9); c.set_line_width(7)
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.stroke()
    # 平原田地 (峰林/孤峰阶段)
    flat = seg(s, 1.4, 2.0)
    if flat > 0:
        for k in range(N):
            if abs(pts[k][1] - pts[k + 1][1]) < 0.5 and pts[k][1] > yb - 0.2 * HH:
                c.set_source_rgba(0.55, 0.7, 0.3, 0.7 * flat); c.rectangle(pts[k][0], pts[k][1] - 3, pts[k + 1][0] - pts[k][0] + 1, 6); c.fill()
    # 雨
    r = random.Random(4)
    for j in range(30):
        x = r.uniform(x0, x1); y = 210 + ((t * 400 + r.uniform(0, 500)) % 300)
        c.set_source_rgba(1, 1, 1, 0.35); c.set_line_width(2); c.move_to(x, y); c.line_to(x - 4, y + 18); c.stroke()
    # 地下水位
    wt = yb - lerp([0.25, 0.2, 0.1, 0.06][i0], [0.25, 0.2, 0.1, 0.06][i1], fr) * HH + 40
    c.set_source_rgba(*WATER, 0.8); c.set_line_width(3); c.set_dash([14, 10]); c.move_to(x0, wt); c.line_to(x1, wt); c.stroke(); c.set_dash([])
    text(c, '地下水位', x1 - 10, wt - 12, 22, WATER, 0.9, align='r')
    c.set_source_rgba(1, 1, 1, 0.5); c.set_line_width(2); c.rectangle(x0, 200, x1 - x0, 800); c.stroke()
    # 阶段条
    cur = int(round(s))
    for k in range(4):
        x = 1060 + k * 200; y = 150
        on = 1 - min(1, abs(s - k))
        text(c, names[k], x, y + 10, 34 + 8 * on, lerp_col(WHITE, GOLD, on), 0.5 + 0.5 * on, serif=True, bold=True, align='c', shadow=True)
        if k < 3: text(c, '→', x + 100, y + 4, 26, WHITE, 0.5, align='c')
    a = 1 - min(1, abs(s - cur) * 3)
    text(c, names[cur], x0 + 30, 290, 56, WHITE, a, serif=True, bold=True, shadow=True)
    text(c, ens[cur], x0 + 32, 330, 20, WHITE, a * 0.9, spacing=2, shadow=True)
    panel_title(c, '石峰的演化', 'KARST LANDFORM EVOLUTION', seg(t, 0.2, 1.2), y=120)

def lerp_col(a, b, k): return tuple(lerp(x, y, k) for x, y in zip(a, b))

def anim_cave(c, t, D, collapse=False):
    bg_dark(c)
    x0, x1 = 120, 1800
    gy = 330
    def ground(x): return gy + 30 * math.sin(x * 0.006) + 18 * math.sin(x * 0.017)
    # 天空
    c.set_source_rgba(0.35, 0.5, 0.6, 0.35); c.rectangle(x0, 180, x1 - x0, 200); c.fill()
    # 岩体
    c.move_to(x0, 1000)
    for x in range(x0, x1 + 1, 10): c.line_to(x, ground(x))
    c.line_to(x1, 1000); c.close_path()
    c.set_source_rgb(*LIME); c.fill()
    c.set_source_rgba(0.3, 0.27, 0.22, 0.2); c.set_line_width(2)
    for yy in range(380, 1000, 40): c.move_to(x0, yy); c.line_to(x1, yy + 6)
    c.stroke()
    c.set_source_rgba(0.28, 0.5, 0.28, 0.9); c.set_line_width(8)
    c.move_to(x0, ground(x0))
    for x in range(x0, x1 + 1, 10): c.line_to(x, ground(x))
    c.stroke()
    cx0, cx1, cyt, cyb = 520, 1400, 560, 820
    if not collapse:
        grow = seg(t, 1, D * 0.35)
        drop = seg(t, D * 0.35, D * 0.5)
        dec = seg(t, D * 0.5, D * 0.95)
        # 管道网络
        r = random.Random(8)
        c.set_source_rgba(*WATER, 0.85); c.set_line_cap(cairo.LINE_CAP_ROUND)
        for j in range(8):
            x = 300 + j * 190 + r.uniform(-30, 30); y = ground(x)
            c.set_line_width(3 + 6 * grow)
            c.move_to(x, y); n = int(grow * 12)
            for k in range(n):
                y += 38; x += r.uniform(-25, 25); c.line_to(x, min(y, 760))
            c.stroke()
        # 洞穴
        cav = grow
        c.save()
        c.translate((cx0 + cx1) / 2, (cyt + cyb) / 2); c.scale((cx1 - cx0) / 2 * (0.3 + 0.7 * cav), (cyb - cyt) / 2 * (0.3 + 0.7 * cav))
        c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
        c.set_source_rgb(0.1, 0.12, 0.14); c.fill()
        # 洞内水
        wl = lerp(560, 800, drop)
        c.save(); c.translate((cx0 + cx1) / 2, (cyt + cyb) / 2); c.scale((cx1 - cx0) / 2 * (0.3 + 0.7 * cav), (cyb - cyt) / 2 * (0.3 + 0.7 * cav)); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
        c.save(); c.clip(); c.set_source_rgba(*WATER, 0.75); c.rectangle(0, wl, W, 400); c.fill(); c.restore()
        # 地下水位线
        c.set_source_rgba(*WATER, 0.9); c.set_line_width(3); c.set_dash([14, 10])
        c.move_to(x0, wl); c.line_to(x1, wl); c.stroke(); c.set_dash([])
        text(c, '地下水位', x1 - 10, wl - 12, 22, WATER, 0.9, align='r')
        if grow > 0.3: text(c, '暗河', 960, 790, 34, WHITE, (1 - drop) * seg(t, D * 0.2, D * 0.3), bold=True, align='c', shadow=True)
        # 钟乳石 & 石笋
        if dec > 0:
            r = random.Random(9)
            for j in range(11):
                x = 600 + j * 72 + r.uniform(-10, 10)
                u = (x - 960) / 440
                top = 690 - 130 * math.sqrt(max(0, 1 - u * u)); bot = 690 + 130 * math.sqrt(max(0, 1 - u * u))
                L = r.uniform(20, 60) * dec
                c.set_source_rgb(0.92, 0.88, 0.8)
                c.move_to(x - 10, top - 4); c.line_to(x + 10, top - 4); c.line_to(x, top + L); c.close_path(); c.fill()
                L2 = r.uniform(15, 45) * dec
                c.move_to(x - 13, bot + 4); c.line_to(x + 13, bot + 4); c.line_to(x, bot - L2); c.close_path(); c.fill()
                # 水滴
                ph = (t * 0.8 + j * 0.37) % 1
                yy = lerp(top + L, bot - L2, ph)
                raindrop(c, x, yy, 0.9 * dec, 0.5)
            label_line(c, 672, 600, 520, 470, '钟乳石', dec, 30)
            label_line(c, 1250, 790, 1450, 900, '石笋', dec, 30)
            b = seg(t, D * 0.6, D * 0.7)
            c.set_source_rgba(0, 0, 0, 0.55 * b); rrect(c, 1160, 390, 640, 150, 12); c.fill()
            chem(c, 'Ca(HCO3)2 → CaCO3 + H2O + CO2↑', 1180, 450, 32, GOLD, b)
            text(c, '每长高 1 厘米 ≈ 上百年', 1180, 510, 28, WHITE, b)
        panel_title(c, '地下世界', 'CAVES & UNDERGROUND RIVERS', seg(t, 0.2, 1.2), y=120)
    else:
        k = seg(t, 1, D * 0.7)
        # 洞穴扩大并向上
        top_y = lerp(560, ground(960) - 5, k)
        c.set_source_rgb(0.1, 0.12, 0.14)
        c.move_to(cx0 + 40 * k, 900)
        c.curve_to(cx0, 700, lerp(cx0, 700, k), top_y + 60, 960 - lerp(300, 220, k), top_y)
        c.line_to(960 + lerp(300, 220, k), top_y)
        c.curve_to(lerp(cx1, 1220, k), top_y + 60, cx1, 700, cx1 - 40 * k, 900)
        c.close_path(); c.fill()
        if k >= 0.98:
            c.set_source_rgba(0.35, 0.5, 0.6, 0.35); c.rectangle(960 - 220, ground(960) - 40, 440, 60); c.fill()
        # 崩落岩块
        r = random.Random(12)
        for j in range(26):
            st = r.uniform(0.1, 0.8) * D; fall = seg(t, st, st + 1.2)
            x = r.uniform(760, 1160); y0 = lerp(560, top_y, r.random()); y = lerp(y0, 880 - r.uniform(0, 60), fall ** 2)
            sz = r.uniform(12, 30)
            c.set_source_rgb(0.7, 0.66, 0.6); c.rectangle(x, y, sz, sz * 0.7); c.fill()
        a = seg(t, D * 0.7, D * 0.8)
        label_line(c, 960, 600, 1300, 480, '天坑 Tiankeng', a, 40)
        panel_title(c, '洞顶崩塌', 'COLLAPSE → TIANKENG', seg(t, 0.2, 1.2), y=120)
        c.set_source_rgba(0, 0, 0, 0.55 * a); rrect(c, 1340, 820, 460, 140, 12); c.fill()
        text(c, '小寨天坑 深度', 1370, 870, 28, WHITE, a)
        text(c, '600+ 米', 1370, 940, 56, GOLD, a, serif=True, bold=True)

def anim_soil(c, t, D):
    bg_dark(c)
    a = seg(t, 0.3, 1.5)
    X = 560
    k = seg(t, 1.5, D * 0.8)
    # 石灰岩块逐渐溶解
    hb = lerp(560, 120, k)
    c.set_source_rgb(*LIME); c.rectangle(X - 200, 900 - hb, 400, hb); c.fill()
    c.set_source_rgba(0.3, 0.27, 0.22, 0.25); c.set_line_width(2)
    for yy in range(int(900 - hb), 900, 30): c.move_to(X - 200, yy); c.line_to(X + 200, yy)
    c.stroke()
    # 雨
    r = random.Random(6)
    for j in range(24):
        x = r.uniform(X - 200, X + 200); y = 200 + ((t * 300 + r.uniform(0, 400)) % (700 - hb))
        raindrop(c, x, y, 0.6, 0.6)
    # 残留土壤
    c.set_source_rgb(0.45, 0.3, 0.18); c.rectangle(X - 200, 900 - hb - 14 * k, 400, 14 * k); c.fill()
    c.set_source_rgba(1, 1, 1, 0.4); c.set_line_width(2); c.rectangle(X - 200, 340, 400, 560); c.stroke(); 
    label_line(c, X + 200, 900 - hb - 7 * k, X + 330, 900 - hb - 100, '残留土壤', k, 30)
    text(c, '溶蚀掉的岩石', X, 320, 26, WHITE, 0.7 * a, align='c')
    X2 = 1350
    text(c, '形成', X2, 420, 44, WHITE, a, align='c', bold=True)
    text(c, '1 厘米 土壤', X2, 560, 90, GOLD, a, serif=True, bold=True, align='c')
    text(c, '往往需要', X2, 680, 44, WHITE, seg(t, 2, 3), align='c', bold=True)
    text(c, '数千年', X2, 820, 110, WATER, seg(t, 3, 4), serif=True, bold=True, align='c')
    panel_title(c, '脆弱的土壤', 'FRAGILE SOIL', seg(t, 0.2, 1.2), y=120)

def anim_timeline(c, t, D):
    bg_dark(c)
    y = 560
    k = seg(t, 0.5, D * 0.8)
    c.set_source_rgba(1, 1, 1, 0.5); c.set_line_width(3); c.move_to(160, y); c.line_to(160 + 1600 * k, y); c.stroke()
    items = [('数亿年', '海洋沉积', 'DEPOSITION', 400, (0.31, 0.62, 0.8)), ('数千万年', '大地抬升', 'UPLIFT', 960, (0.85, 0.5, 0.35)),
             ('数百万年', '雨水雕刻', 'DISSOLUTION', 1520, GOLD)]
    for i, (n, d, en, x, col) in enumerate(items):
        a = seg(t, D * (0.1 + i * 0.25), D * (0.1 + i * 0.25) + 1.2)
        c.set_source_rgba(*col, a); c.arc(x, y, 22, 0, 2 * math.pi); c.fill()
        c.set_source_rgba(*col, a * 0.4); c.set_line_width(3); c.arc(x, y, 34 + 6 * math.sin(t * 3), 0, 2 * math.pi); c.stroke()
        text(c, n, x, y - 90, 72, col, a, serif=True, bold=True, align='c')
        text(c, d, x, y + 110, 48, WHITE, a, serif=True, bold=True, align='c')
        text(c, en, x, y + 160, 20, WHITE, a * 0.7, align='c', spacing=3)
    text(c, '→', 680, y + 16, 46, WHITE, seg(t, D * 0.3, D * 0.4), align='c')
    text(c, '→', 1240, y + 16, 46, WHITE, seg(t, D * 0.55, D * 0.65), align='c')
    a = seg(t, D * 0.82, D * 0.95)
    text(c, '今天的石峰与洞穴', W / 2, 900, 50, WHITE, a, serif=True, bold=True, align='c')

# ---------------------------------------------------------------- cards
def card_title(c, t, D):
    draw_photo(c, 'img/ai_aerial.jpg', t / D, 'out', dark=0.45)
    a = seg(t, 0.3, 1.6) * (1 - seg(t, D - 0.8, D))
    text(c, '喀斯特', W / 2, 560, 200, WHITE, a, serif=True, bold=True, align='c', shadow=True, spacing=40)
    w = 560 * seg(t, 0.8, 2)
    c.set_source_rgba(*GOLD, a); c.rectangle(W / 2 - w / 2, 620, w, 3); c.fill()
    text(c, '中 国 南 方 的 石 头 森 林', W / 2, 690, 40, WHITE, a * seg(t, 1.2, 2.2), serif=True, align='c', shadow=True)
    text(c, 'KARST  ·  THE STONE FOREST OF SOUTH CHINA', W / 2, 745, 22, GOLD, a * seg(t, 1.5, 2.5), align='c', spacing=2)

def make_chapter(num, zh, en, img):
    def f(c, t, D):
        draw_photo(c, img, t / D, 'in', blur=0, dark=0.6)
        a = seg(t, 0.2, 1.0) * (1 - seg(t, D - 0.6, D))
        text(c, num, W / 2, 470, 120, GOLD, a, serif=True, bold=True, align='c', shadow=True)
        w = 120 * seg(t, 0.4, 1.2); c.set_source_rgba(1, 1, 1, a); c.rectangle(W / 2 - w / 2, 510, w, 2); c.fill()
        text(c, zh, W / 2, 620, 84, WHITE, a, serif=True, bold=True, align='c', shadow=True, spacing=16)
        text(c, en, W / 2, 680, 24, WHITE, a * 0.85, align='c', spacing=4, shadow=True)
    return f

def card_end(c, t, D):
    draw_photo(c, 'img/guilin_0.jpg', min(1, t / 8), 'out', dark=0.35 + 0.4 * seg(t, 6, 8))
    a = seg(t, 0.5, 2) * (1 - seg(t, 5.5, 7))
    text(c, '这里是喀斯特', W / 2, 560, 120, WHITE, a, serif=True, bold=True, align='c', shadow=True, spacing=20)
    text(c, 'THIS IS KARST', W / 2, 640, 26, GOLD, a, align='c', spacing=6)
    # 滚动鸣谢
    if t > 6.5:
        lines = ['素材鸣谢 · Image & Video Credits', '']
        for k, (ti, au, lic) in CREDITS.items():
            if k in USED:
                lines.append(f'{ti[:60]}  —  {au.splitlines()[0][:40]}  ({lic})')
        lines += ['', '部分示意画面由 AI 生成 · 动画与图解为原创绘制', '地图数据：Natural Earth（公有领域）', '', '感谢观看']
        y0 = H + 40 - (t - 6.5) * 95
        for i, l in enumerate(lines):
            yy = y0 + i * 48
            if -40 < yy < H + 40:
                big = i == 0 or l == '感谢观看'
                text(c, l, W / 2, yy, 36 if big else 24, GOLD if big else WHITE, 0.95, align='c', bold=big)


# ---------------------------------------------------------------- video clips
VCRED = {
 'clips/halong.mp4': ('Ha Long Bay, Vietnam - Dec 2024', 'പയ്യൻ', 'CC BY-SA 4.0'),
 'clips/halong_boat.mp4': ('Halong Bay 20220801', 'L. Shyamal', 'CC BY-SA 4.0'),
 'clips/janicja_a.mp4': ('Janicja Jama (Slovenia)', 'caveman0043', 'CC BY 3.0'),
 'clips/rak.mp4': ('River Rak going underground', 'Malenki', 'CC BY-SA 3.0'),
 'clips/planina.mp4': ('Planina Cave, Slovenia', 'allergyforsun', 'CC BY 3.0'),
 'clips/coral.mp4': ('Chesterfield-Bellona reef', 'Dominique Pelletier', 'CC BY 4.0'),
 'clips/redsea.mp4': ('Das Rote Meer. Unterwasserwelt', 'Kora27', 'CC BY-SA 4.0'),
 'clips/rain.mp4': ('Rain drops - Japan', 'Nesnad', 'CC BY 4.0'),
 'clips/seep.mp4': ('Grand Canyon NP - Seep Spring', 'Grand Canyon NPS', 'Public domain'),
 'clips/monsoon.mp4': ('Timelapse 2025 Kinnaur Monsoon', 'Dfromhimalayas', 'CC BY 4.0'),
 'clips/drip.mp4': ('Tropfsteine als Indikatoren für den Klimawandel', 'ZDF/Terra X', 'CC BY 4.0'),
 'clips/forest.mp4': ('From the mountain high, the forest stretches...', 'Mathanprasath K', 'CC BY 4.0'),
 'clips/kostivere.mp4': ('Kostivere karst area, spring 2021', 'Sillerkiil', 'CC0'),
 'clips/clouds.mp4': ('Time Lapse Clouds above Steens Mountain', 'BLM Oregon & Washington', 'Public domain'),
}
CREDITS.update(VCRED)

class VideoSrc:
    def __init__(s, path):
        s.path = path; s.proc = None; s.next = 0; s.buf = None; s.surf = None
        s.n = int(dur_of(path) * FPS) - 1
    def _start(s, idx):
        if s.proc: s.proc.kill(); s.proc.wait()
        s.proc = subprocess.Popen([FF, '-loglevel', 'quiet', '-threads', '1', '-ss', f'{idx / FPS:.4f}', '-i', s.path, '-f', 'rawvideo',
                                   '-pix_fmt', 'bgra', '-'], stdout=subprocess.PIPE)
        s.next = idx
    def close(s):
        if s.proc: s.proc.kill(); s.proc.wait(); s.proc = None
        s.buf = None; s.surf = None
    def frame(s, idx):
        idx = max(0, min(idx, s.n))
        if s.buf is not None and idx == s.next - 1: return s.surf
        if s.proc is None or idx < s.next or idx > s.next + 48: s._start(idx)
        while s.next <= idx:
            data = s.proc.stdout.read(W * H * 4)
            if len(data) < W * H * 4:
                s.n = s.next - 1; break
            s.buf = bytearray(data); s.next += 1
        if s.buf is None: s.buf = bytearray(W * H * 4)
        s.surf = cairo.ImageSurface.create_for_data(s.buf, cairo.FORMAT_ARGB32, W, H, W * 4)
        return s.surf

_VS = {}
def V_(path, tag=None, zoom='in'):
    def f(c, t, D):
        if path not in _VS: _VS[path] = VideoSrc(path)
        surf = _VS[path].frame(int(t * FPS))
        k = min(1, max(0, t / D))
        z = lerp(1.0, 1.05, k) if zoom == 'in' else lerp(1.05, 1.0, k)
        c.save(); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
        c.set_source_surface(surf, 0, 0); c.get_source().set_filter(cairo.FILTER_BILINEAR); c.paint(); c.restore()
        if tag:
            loc_tag(c, tag[0], tag[1], seg(t, 0.4, 1.2) * (1 - seg(t, D - 0.6, D)))
        credit_tag(c, path, seg(t, 0.2, 0.8))
    f.path = path
    return f

# ---------------------------------------------------------------- timeline
def P_(path, move='in', tag=None):
    def f(c, t, D):
        draw_photo(c, path, t / D, move)
        if tag:
            loc_tag(c, tag[0], tag[1], seg(t, 0.4, 1.2) * (1 - seg(t, D - 0.6, D)))
        credit_tag(c, path, seg(t, 0.2, 0.8))
    f.path = path
    return f

# v3: original premium cartography, stratigraphy and 2.5D motion-graphics system.
# The shot schedule, licensed footage, narration and subtitles remain unchanged.
import premium
premium.install(globals())
# v4: shaded-relief terrain morph and layered subsurface cutaway.
import v4graphics
v4graphics.install(globals())

A = lambda fn: fn
AUD = {i: dur_of(f'audio/s{i}.mp3') for i in range(1, 9)}
R = 'rest'
BLOCKS = [
    # (audio, lead, tail, [(dur, fn)])
    (1, 1.2, 0.8, [(5, P_('img/ai_aerial.jpg', 'in')),
                   (4, V_('clips/halong.mp4', ('越南 · 下龙湾', 'HA LONG BAY · SAME KARST BELT'))),
                   (4, P_('img/guilin_0.jpg', 'right', ('广西 · 漓江', 'LI RIVER, GUANGXI'))),
                   (4, P_('img/stoneforest_1.jpg', 'left', ('云南 · 石林', 'SHILIN, YUNNAN'))),
                   (3.5, V_('clips/janicja_a.mp4', ('溶洞', 'KARST CAVE'))),
                   (4, V_('clips/rak.mp4', ('暗河', 'UNDERGROUND RIVER'))),
                   (4.5, P_('img/xiaozhai_0.jpg', 'down', ('重庆 · 小寨天坑', 'XIAOZHAI TIANKENG'))),
                   (R, P_('img/fengcong2_0.jpg', 'right', ('贵州 · 万峰林', 'WANFENGLIN, GUIZHOU')))]),
    (None, 0, 6, [(6, card_title)]),
    (2, 0.5, 0.8, [(9.5, anim_world), (3.5, V_('clips/planina.mp4', ('斯洛文尼亚 · 喀斯特', 'KRAS, SLOVENIA'))),
                   (17, anim_china), (4.5, P_('img/stoneforest_2.jpg', 'in', ('云南 · 石林', 'SHILIN, YUNNAN'))),
                   (4.5, P_('img/libo2_1.jpg', 'up', ('贵州 · 荔波小七孔', 'XIAOQIKONG, LIBO'))), (R, P_('img/guilin_1.jpg', 'left', ('广西 · 阳朔', 'YANGSHUO, GUANGXI')))]),
    (None, 0, 3.5, [(3.5, make_chapter('01', '远古海洋', 'THE ANCIENT SEA', 'img/ai_sea.jpg'))]),
    (3, 0.3, 0.8, [(5, P_('img/ai_sea.jpg', 'in')), (7, V_('clips/coral.mp4', ('今天的珊瑚礁', 'MODERN CORAL REEF'))),
                   (6, V_('clips/redsea.mp4')), (21, anim_deposit),
                   (6, P_('img/limestone_0.jpg', 'in', ('石灰岩中的化石', 'FOSSILS IN LIMESTONE'))), (R, P_('img/limestone_1.jpg', 'out'))]),
    (None, 0, 3.5, [(3.5, make_chapter('02', '大地抬升', 'THE RISE OF THE LAND', 'img/fengcong2_1.jpg'))]),
    (4, 0.3, 0.8, [(19, anim_plates), (16, anim_fold), (R, P_('img/fengcong2_1.jpg', 'right', ('贵州 · 兴义', 'XINGYI, GUIZHOU')))]),
    (None, 0, 3.5, [(3.5, make_chapter('03', '水的雕刻', 'CARVED BY WATER', 'img/yangshuo_2.jpg'))]),
    (5, 0.3, 0.8, [(6, V_('clips/rain.mp4')), (23, anim_chem), (4.8, V_('clips/seep.mp4', ('渗流', 'SEEPAGE'))),
                   (10, anim_rate), (R, V_('clips/monsoon.mp4', ('季风降水', 'MONSOON RAIN')))]),
    (None, 0, 3.5, [(3.5, make_chapter('04', '石峰的演化', 'FROM PILLARS TO PEAKS', 'img/stoneforest_0.jpg'))]),
    (6, 0.3, 0.8, [(7.8, P_('img/stoneforest_0.jpg', 'right', ('云南 · 石林', 'SHILIN, YUNNAN'))), (42, anim_evolve),
                   (R, P_('img/yangshuo_0.jpg', 'in', ('孤峰 · 阳朔月亮山', 'MOON HILL, YANGSHUO')))]),
    (None, 0, 3.5, [(3.5, make_chapter('05', '地下世界', 'THE UNDERWORLD', 'img/ai_river.jpg'))]),
    (7, 0.3, 0.8, [(3.5, V_('clips/planina.mp4', ('地下河出口', 'RESURGENCE'))), (3.5, P_('img/ai_river.jpg', 'in')), (18, anim_cave),
                   (5, V_('clips/drip.mp4', ('钟乳石与石笋', 'STALACTITES'))),
                   (7, lambda c, t, D: anim_cave(c, t, D, True)),
                   (6.5, P_('img/xiaozhai_0.jpg', 'in', ('重庆奉节 · 小寨天坑', 'XIAOZHAI TIANKENG, FENGJIE'))),
                   (R, P_('img/xiaozhai_1.jpg', 'down'))]),
    (None, 0, 3.5, [(3.5, make_chapter('06', '脆弱与守护', 'FRAGILITY & CARE', 'img/ai_desert.jpg'))]),
    (8, 0.3, 1.5, [(11, anim_soil), (5, V_('clips/kostivere.mp4', ('裸露的石灰岩', 'BARE LIMESTONE'))),
                   (6, P_('img/ai_desert.jpg', 'right', ('石漠化', 'ROCKY DESERTIFICATION'))),
                   (5, P_('img/ai_green.jpg', 'in', ('重披绿装', 'REFORESTATION'))), (4.6, V_('clips/forest.mp4')),
                   (5, V_('clips/clouds.mp4')), (17, anim_timeline),
                   (5, V_('clips/halong_boat.mp4')), (R, P_('img/guilin_2.jpg', 'out'))]),
    (None, 0, 30, [(30, card_end)]),
]

USED = set()
SHOTS = []   # (start, dur, fn)
SUBS = []    # (start, end, text)
AUDIO_AT = []
TEXT = {}
for i in range(1, 9):
    TEXT[i] = open(f'script/s{i}.txt', encoding='utf-8').read().strip()

def split_subs(s):
    parts = re.split(r'(?<=[。，？；：！])', s)
    out = []
    for p in parts:
        p = p.strip()
        if not p: continue
        while len(p) > 24:
            out.append(p[:20]); p = p[20:]
        out.append(p)
    # 合并过短
    merged = []
    for p in out:
        if merged and len(merged[-1]) + len(p) <= 16: merged[-1] += p
        else: merged.append(p)
    return merged

T0 = 0.0
for aud, lead, tail, shots in BLOCKS:
    total = lead + (AUD[aud] if aud else 0) + tail
    fixed = sum(d for d, _ in shots if d != R)
    for d, fn in shots:
        d = total - fixed if d == R else d
        SHOTS.append((T0, d, fn))
        if hasattr(fn, 'path'): USED.add(fn.path)
        T0 += d
    T0 = SHOTS[-1][0] + SHOTS[-1][1]
    if aud:
        st = T0 - total + lead
        AUDIO_AT.append((aud, st))
        chunks = split_subs(TEXT[aud])
        wts = [len(re.sub(r'[，。？；：！、]', '', ch)) + (2.5 if ch[-1] in '。？！' else 1.2 if ch[-1] in '，；：' else 0) for ch in chunks]
        tot = sum(wts); d = AUD[aud] - 0.2; cur = st
        for ch, w in zip(chunks, wts):
            e = cur + d * w / tot
            SUBS.append((cur, e - 0.05, ch.rstrip('，。；：、')))
            cur = e
TOTAL = T0

def draw_subs(c, t):
    for s, e, tx in SUBS:
        if s <= t < e:
            a = min(1, (t - s) / 0.12, (e - t) / 0.12)
            font(c, 46)
            tw = c.text_extents(tx).x_advance
            c.set_source_rgba(0, 0, 0, 0.0)
            x = W / 2 - tw / 2; y = 1010
            c.move_to(x, y); c.text_path(tx)
            c.set_source_rgba(0, 0, 0, 0.75 * a); c.set_line_width(6); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
            c.set_source_rgba(1, 1, 1, a); c.fill()
            break

# 暗角
VIG = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
_c = cairo.Context(VIG)
g = cairo.RadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, W * 0.62)
g.add_color_stop_rgba(0, 0, 0, 0, 0); g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
_c.set_source(g); _c.paint()

XF = 0.5
def render_frame(c, t):
    idx = 0
    for i, (s, d, fn) in enumerate(SHOTS):
        if s <= t < s + d: idx = i; break
    else: idx = len(SHOTS) - 1
    s, d, fn = SHOTS[idx]
    keep = {getattr(fn, 'path', None)}
    # The previous shot is decoded only for the 0.5 s crossfade; otherwise
    # retaining two 1080p video decoders for the whole shot may exhaust RAM.
    if idx > 0 and t - s < XF:
        keep.add(getattr(SHOTS[idx - 1][2], 'path', None))
    for pth in list(_VS):
        if pth not in keep: _VS.pop(pth).close()
    c.set_source_rgb(0, 0, 0); c.paint()
    fn(c, t - s, d)
    if idx > 0 and t - s < XF:
        ps, pd, pfn = SHOTS[idx - 1]
        c.push_group(); pfn(c, min(t - ps, pd + XF), pd); pat = c.pop_group()
        c.set_source(pat); c.paint_with_alpha(1 - ease((t - s) / XF))
    c.set_source_surface(VIG); c.paint()
    # 全局淡入淡出
    if t < 1.0: c.set_source_rgba(0, 0, 0, 1 - t); c.paint()
    if t > TOTAL - 2: c.set_source_rgba(0, 0, 0, min(1, (t - (TOTAL - 2)) / 2)); c.paint()
    draw_subs(c, t)

def render(f0, f1, out):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    c = cairo.Context(surf)
    p = subprocess.Popen([FF, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-x264-params', 'rc-lookahead=10:threads=1', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        render_frame(c, fi / FPS)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
        if fi % 240 == 0: print(out, fi, f1, flush=True)
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'info':
        print('TOTAL', TOTAL, 'frames', int(TOTAL * FPS))
        for s, d, fn in SHOTS: print(f'{s:7.2f} {d:6.2f} {getattr(fn, "path", fn.__name__)}')
        print(AUDIO_AT)
    elif cmd == 'still':
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
        for ts in sys.argv[2:]:
            render_frame(c, float(ts)); surf.write_to_png(f'preview/f_{float(ts):07.1f}.png')
    elif cmd == 'render':
        N = int(TOTAL * FPS); parts = int(sys.argv[2]); k = int(sys.argv[3])
        f0 = N * k // parts; f1 = N * (k + 1) // parts
        render(f0, f1, f'parts/p{k}.mp4')
    elif cmd == 'audio':
        json.dump({'total': TOTAL, 'audio': AUDIO_AT}, open('audio_map.json', 'w'))
