"""Build animated splash assets (Lottie, animated SVG, Android AVD) from pieces.json."""
import json, math, sys, os

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
P = json.load(open(sys.argv[2] if len(sys.argv) > 2 else 'pieces.json'))

FPS = 60
TOTAL = 150  # 2.5 s (animation ends ~1.95 s, then holds)
PAD = 24

xs = [q[0] for p in P for pa in p['paths'] for q in pa['pts']]
ys = [q[1] for p in P for pa in p['paths'] for q in pa['pts']]
OX, OY = math.floor(min(xs)) - PAD, math.floor(min(ys)) - PAD
W, H = math.ceil(max(xs) - OX + PAD), math.ceil(max(ys) - OY + PAD)
W += W % 2; H += H % 2

tiles = [p for p in P if p['kind'] == 'tile']
gx0 = min(p['bbox'][0] for p in tiles); gx1 = max(p['bbox'][0] + p['bbox'][2] for p in tiles)
gy0 = min(p['bbox'][1] for p in tiles); gy1 = max(p['bbox'][1] + p['bbox'][3] for p in tiles)
GCX, GCY = (gx0 + gx1) / 2, (gy0 + gy1) / 2

def r1(v): return round(v, 1)

# ---- timing (frames @60fps) -------------------------------------------------
def timing(p):
    if p['kind'] == 'tile':
        t = 0.78 * (p['cx'] - gx0) / (gx1 - gx0) + 0.22 * (p['cy'] - gy0) / (gy1 - gy0)
        start = round(t * 42)
        dx, dy = (p['cx'] - GCX) * 0.22, (p['cy'] - GCY) * 0.22
        return dict(type='tile', start=start, dur=26, dx=dx, dy=dy)
    if p['word'] == 'berp':
        return dict(type='berp', start=46 + 5 * p['letter'], dur=28, dx=0, dy=46)
    return dict(type='sis', start=70 + 3 * p['letter'], dur=24, dx=-28, dy=0)

for p in P: p['tm'] = timing(p)
END = max(p['tm']['start'] + p['tm']['dur'] for p in P)

# ---- Lottie -----------------------------------------------------------------
EASE_OUT = (0.22, 0.9, 0.32, 1.0)
EASE_IO = (0.45, 0.0, 0.35, 1.0)
LIN = (0.33, 0.33, 0.67, 0.67)

def kfs(points, dims):
    """points: [(frame, value_list, ease_to_next)]"""
    out = []
    for i, (t, v, e) in enumerate(points):
        k = {'t': t, 's': v}
        if i < len(points) - 1:
            k['o'] = {'x': [e[0]] * dims, 'y': [e[1]] * dims}
            k['i'] = {'x': [e[2]] * dims, 'y': [e[3]] * dims}
        out.append(k)
    return {'a': 1, 'k': out}

def lottie_layer(idx, p):
    tm = p['tm']; s, d = tm['start'], tm['dur']
    cx, cy = p['cx'] - OX, p['cy'] - OY
    if tm['type'] == 'tile':
        scale = kfs([(s, [0, 0, 100], EASE_OUT), (s + round(d * .62), [112, 112, 100], EASE_IO), (s + d, [100, 100, 100], LIN)], 3)
        rot = kfs([(s, [-28], EASE_OUT), (s + round(d * .8), [0], LIN)], 1)
        op = kfs([(s, [0], LIN), (s + round(d * .35), [100], LIN)], 1)
        pos = kfs([(s, [cx + tm['dx'], cy + tm['dy'], 0], EASE_OUT), (s + round(d * .7), [cx, cy, 0], LIN)], 3)
    else:
        over = 1.0 if tm['type'] == 'berp' else 0.0
        scale = {'a': 0, 'k': [100, 100, 100]}
        rot = {'a': 0, 'k': 0}
        op = kfs([(s, [0], LIN), (s + round(d * .45), [100], LIN)], 1)
        pts = [(s, [cx + tm['dx'], cy + tm['dy'], 0], EASE_OUT)]
        if over:
            pts.append((s + round(d * .65), [cx, cy - 6, 0], EASE_IO))
        pts.append((s + d, [cx, cy, 0], LIN))
        pos = kfs(pts, 3)
    shapes = []
    for pa in p['paths']:
        v = [[r1(x - OX), r1(y - OY)] for x, y in pa['pts']]
        z = [[0, 0]] * len(v)
        shapes.append({'ty': 'sh', 'ks': {'a': 0, 'k': {'c': True, 'v': v, 'i': z, 'o': z}}})
    hexc = p['color'].lstrip('#')
    rgb = [round(int(hexc[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]
    shapes.append({'ty': 'fl', 'c': {'a': 0, 'k': rgb}, 'o': {'a': 0, 'k': 100}, 'r': 2})
    shapes.append({'ty': 'tr', 'p': {'a': 0, 'k': [0, 0]}, 'a': {'a': 0, 'k': [0, 0]}, 's': {'a': 0, 'k': [100, 100]},
                   'r': {'a': 0, 'k': 0}, 'o': {'a': 0, 'k': 100}})
    return {'ddd': 0, 'ind': idx, 'ty': 4, 'nm': f"{p['kind']}_{idx}", 'sr': 1,
            'ks': {'o': op, 'r': rot, 'p': pos, 'a': {'a': 0, 'k': [cx, cy, 0]}, 's': scale},
            'ao': 0, 'shapes': [{'ty': 'gr', 'nm': 'g', 'it': shapes}], 'ip': 0, 'op': TOTAL, 'st': 0, 'bm': 0}

order = sorted(P, key=lambda p: (p['kind'] != 'text', p['cls'] != 'b'))
lottie = {'v': '5.7.4', 'fr': FPS, 'ip': 0, 'op': TOTAL, 'w': W, 'h': H, 'nm': 'Berp Sistemas splash', 'ddd': 0,
          'assets': [], 'layers': [lottie_layer(i + 1, p) for i, p in enumerate(order)], 'markers': []}
json.dump(lottie, open(f'{OUT}/berp_splash.json', 'w'), separators=(',', ':'))

# ---- SVG (static + CSS-animated) ----------------------------------------------
def svg_d(p, ox=OX, oy=OY, sc=1.0):
    d = []
    for pa in p['paths']:
        pts = [(r1((x - ox) * sc), r1((y - oy) * sc)) for x, y in pa['pts']]
        d.append('M' + ' '.join(f'{x} {y}' for x, y in pts) + 'Z')
    return ''.join(d)

def svg(animated):
    css = ''
    if animated:
        css = f"""<style>
.p{{transform-box:view-box;animation-fill-mode:both;animation-duration:var(--d);animation-delay:var(--s)}}
.tile{{animation-name:tile;animation-timing-function:cubic-bezier(.22,.9,.32,1)}}
.berp{{animation-name:berp;animation-timing-function:cubic-bezier(.22,.9,.32,1)}}
.sis{{animation-name:sis;animation-timing-function:cubic-bezier(.22,.9,.32,1)}}
@keyframes tile{{0%{{opacity:0;transform:translate(var(--dx),var(--dy)) rotate(-28deg) scale(0)}}35%{{opacity:1}}62%{{transform:translate(0,0) rotate(-4deg) scale(1.12)}}100%{{opacity:1;transform:none}}}}
@keyframes berp{{0%{{opacity:0;transform:translate(0,var(--dy))}}45%{{opacity:1}}65%{{transform:translate(0,-6px)}}100%{{opacity:1;transform:none}}}}
@keyframes sis{{0%{{opacity:0;transform:translate(var(--dx),0)}}45%{{opacity:1}}100%{{opacity:1;transform:none}}}}
@media (prefers-reduced-motion:reduce){{.p{{animation:none}}}}
</style>"""
    els = []
    for p in order:
        attrs = f'd="{svg_d(p)}" fill="{p["color"]}" fill-rule="evenodd"'
        if animated:
            tm = p['tm']
            st = (f"transform-origin:{r1(p['cx'] - OX)}px {r1(p['cy'] - OY)}px;--s:{round(tm['start'] * 1000 / FPS)}ms;"
                  f"--d:{round(tm['dur'] * 1000 / FPS)}ms;--dx:{r1(tm['dx'])}px;--dy:{r1(tm['dy'])}px")
            attrs = f'class="p {tm["type"]}" style="{st}" ' + attrs
        els.append(f'<path {attrs}/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>Berp Sistemas</title>{css}' + ''.join(els) + '</svg>')

open(f'{OUT}/berp_logo.svg', 'w').write(svg(False))
open(f'{OUT}/berp_splash_animated.svg', 'w').write(svg(True))

# ---- Android Animated Vector Drawable (globe only, for the Android 12+ SplashScreen API) ----
# 288dp viewport; Android masks the icon to a 192dp circle, so the globe sits inside it. Max 1000 ms.
V = 288
gw, gh = gx1 - gx0, gy1 - gy0
sc = 150 / max(gw, gh)
ox, oy = gx0 - (V / sc - gw) / 2, gy0 - (V / sc - gh) / 2
TSCALE = 1000 / ((42 + 26) * 1000 / FPS)  # compress tile timeline into 1000 ms
groups, targets = [], []
for i, p in enumerate(t for t in order if t['kind'] == 'tile'):
    tm = p['tm']
    s = round(tm['start'] * 1000 / FPS * TSCALE); d = round(tm['dur'] * 1000 / FPS * TSCALE)
    px, py = r1((p['cx'] - ox) * sc), r1((p['cy'] - oy) * sc)
    groups.append(f'''        <group android:name="t{i}" android:pivotX="{px}" android:pivotY="{py}" android:scaleX="0" android:scaleY="0">
            <path android:fillColor="{p["color"]}" android:pathData="{svg_d(p, ox, oy, sc)}"/>
        </group>''')
    targets.append(f'''    <target android:name="t{i}">
        <aapt:attr name="android:animation">
            <set>
                <objectAnimator android:propertyName="scaleX" android:valueFrom="0" android:valueTo="1"
                    android:startOffset="{s}" android:duration="{d}" android:interpolator="@android:interpolator/overshoot"/>
                <objectAnimator android:propertyName="scaleY" android:valueFrom="0" android:valueTo="1"
                    android:startOffset="{s}" android:duration="{d}" android:interpolator="@android:interpolator/overshoot"/>
                <objectAnimator android:propertyName="rotation" android:valueFrom="-28" android:valueTo="0"
                    android:startOffset="{s}" android:duration="{d}" android:interpolator="@android:interpolator/decelerate_cubic"/>
            </set>
        </aapt:attr>
    </target>''')
avd = f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Berp Sistemas globe: animated icon for the Android 12+ SplashScreen API (1000 ms). -->
<animated-vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt">
    <aapt:attr name="android:drawable">
        <vector android:width="288dp" android:height="288dp"
            android:viewportWidth="{V}" android:viewportHeight="{V}">
{chr(10).join(groups)}
        </vector>
    </aapt:attr>
{chr(10).join(targets)}
</animated-vector>
'''
open(f'{OUT}/avd_berp_splash_globe.xml', 'w').write(avd)
print('canvas', W, H, 'end frame', END, 'total', TOTAL)

# Static fallback of the same globe (pre-Android 12 / core-splashscreen on API < 31 shows icons without animating)
static = f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Berp Sistemas globe: static splash icon (fallback for API < 31). -->
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="288dp" android:height="288dp"
    android:viewportWidth="{V}" android:viewportHeight="{V}">
''' + '\n'.join(f'    <path android:fillColor="{p["color"]}" android:pathData="{svg_d(p, ox, oy, sc)}"/>'
               for p in order if p['kind'] == 'tile') + '\n</vector>\n'
open(f'{OUT}/ic_berp_splash_globe.xml', 'w').write(static)
