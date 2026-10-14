"""Build looping loading-spinner assets (Lottie, animated SVG, Android AVD) from the globe tiles in pieces.json.

Two variants:
  spin  - the globe turns continuously while a wave of light runs around its tiles (1 turn / 2 s)
  pulse - the globe stays still and the wave sweeps around the tiles (1.5 s)
"""
import json, math, sys, os

GRAY = '--gray' in sys.argv          # --gray: grayscale version, files get a _gray suffix
if GRAY: sys.argv.remove('--gray')
SUF = '_gray' if GRAY else ''
OUT = sys.argv[1]
P = [p for p in json.load(open(sys.argv[2] if len(sys.argv) > 2 else 'pieces.json')) if p['kind'] == 'tile']
if GRAY:
    for p in P:
        r, g, b = (int(p['color'][i:i + 2], 16) for i in (1, 3, 5))
        y = round(0.299 * r + 0.587 * g + 0.114 * b)   # perceived brightness keeps blue and orange distinguishable
        p['color'] = '#%02x%02x%02x' % (y, y, y)
os.makedirs(OUT, exist_ok=True)

FPS = 60
CX, CY, R = 210.05, 514.41, 251.1   # circle fitted to the globe silhouette
SIZE = 512                          # output canvas (square)
PAD = 8
SC = (SIZE / 2 - PAD) / R

def tx(x): return round((x - CX) * SC + SIZE / 2, 1)
def ty(y): return round((y - CY) * SC + SIZE / 2, 1)

def wave(u):
    """Brightness 0..1 of a tile at phase u in [0,1): a soft bump that peaks at u=0."""
    return ((1 + math.cos(2 * math.pi * u)) / 2) ** 2

for p in P:
    # angle around the globe centre; the wave travels clockwise (increasing screen angle)
    p['phase'] = (math.atan2(p['cy'] - CY, p['cx'] - CX) / (2 * math.pi)) % 1.0
    p['tcx'], p['tcy'] = tx(p['cx']), ty(p['cy'])

VARIANTS = {
    'spin': dict(period=120, rotate=True, smin=0.86, omin=72),
    'pulse': dict(period=90, rotate=False, smin=0.62, omin=30),
}
STEP = 5  # keyframe every 5 frames, linear between them (exact seamless loop)

def lin(dims):
    return {'o': {'x': [0.333] * dims, 'y': [0.333] * dims}, 'i': {'x': [0.667] * dims, 'y': [0.667] * dims}}

def sampled(T, f, dims):
    ks = []
    for t in range(0, T + 1, STEP):
        k = {'t': t, 's': f(t)}
        if t < T: k.update(lin(dims))
        ks.append(k)
    return {'a': 1, 'k': ks}

def path_d(p):
    return ''.join('M' + ' '.join(f'{tx(x)} {ty(y)}' for x, y in pa['pts']) + 'Z' for pa in p['paths'])

def rgb(hexc):
    h = hexc.lstrip('#'); return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]

def static_tr():
    return {'ty': 'tr', 'p': {'a': 0, 'k': [0, 0]}, 'a': {'a': 0, 'k': [0, 0]}, 's': {'a': 0, 'k': [100, 100]},
            'r': {'a': 0, 'k': 0}, 'o': {'a': 0, 'k': 100}}

def build(name, period, rotate, smin, omin):
    T = period
    val = lambda p, t: wave(((t / T) - p['phase']) % 1.0)
    # ---- Lottie: one null-free precomp-free file; rotation sits on a parent null layer
    layers = []
    root = {'ddd': 0, 'ind': 1, 'ty': 3, 'nm': 'globe', 'sr': 1, 'ao': 0, 'ip': 0, 'op': T, 'st': 0, 'bm': 0,
            'ks': {'o': {'a': 0, 'k': 100}, 'p': {'a': 0, 'k': [SIZE / 2, SIZE / 2, 0]}, 'a': {'a': 0, 'k': [SIZE / 2, SIZE / 2, 0]},
                   's': {'a': 0, 'k': [100, 100, 100]},
                   'r': ({'a': 1, 'k': [{'t': 0, 's': [0], **lin(1)}, {'t': T, 's': [360]}]} if rotate else {'a': 0, 'k': 0})}}
    layers.append(root)
    for i, p in enumerate(P):
        shapes = [{'ty': 'sh', 'ks': {'a': 0, 'k': {'c': True, 'v': [[tx(x), ty(y)] for x, y in pa['pts']],
                                                   'i': [[0, 0]] * len(pa['pts']), 'o': [[0, 0]] * len(pa['pts'])}}}
                  for pa in p['paths']]
        shapes += [{'ty': 'fl', 'c': {'a': 0, 'k': rgb(p['color'])}, 'o': {'a': 0, 'k': 100}, 'r': 1}, static_tr()]
        sc = lambda t, p=p: [round(100 * (smin + (1 - smin) * val(p, t)), 2)] * 2 + [100]
        op = lambda t, p=p: [round(omin + (100 - omin) * val(p, t), 2)]
        layers.append({'ddd': 0, 'ind': i + 2, 'ty': 4, 'nm': f'tile_{i}', 'sr': 1, 'ao': 0, 'parent': 1,
                       'ip': 0, 'op': T, 'st': 0, 'bm': 0,
                       'ks': {'o': sampled(T, op, 1), 'r': {'a': 0, 'k': 0},
                              'p': {'a': 0, 'k': [p['tcx'], p['tcy'], 0]}, 'a': {'a': 0, 'k': [p['tcx'], p['tcy'], 0]},
                              's': sampled(T, sc, 3)},
                       'shapes': [{'ty': 'gr', 'nm': 'g', 'it': shapes}]})
    lottie = {'v': '5.7.4', 'fr': FPS, 'ip': 0, 'op': T, 'w': SIZE, 'h': SIZE, 'nm': f'Berp loader {name}',
              'ddd': 0, 'assets': [], 'layers': layers, 'markers': []}
    json.dump(lottie, open(f'{OUT}/berp_loader_{name}.json', 'w'), separators=(',', ':'))

    # ---- SVG with CSS animation (infinite). Negative delays put every tile at its phase from the first frame.
    dur = round(T * 1000 / FPS)
    css = (f'<style>'
           f'.t{{transform-box:view-box;animation:w {dur}ms linear infinite;animation-delay:var(--d)}}'
           f'@keyframes w{{' + ''.join(
               f'{round(u * 100, 1)}%{{opacity:{round((omin + (100 - omin) * wave(u)) / 100, 3)};transform:scale({round(smin + (1 - smin) * wave(u), 3)})}}'
               for u in [k / 20 for k in range(21)]) + '}'
           + (f'.g{{transform-origin:{SIZE / 2}px {SIZE / 2}px;animation:r {dur}ms linear infinite}}'
              f'@keyframes r{{to{{transform:rotate(360deg)}}}}' if rotate else '')
           + '@media (prefers-reduced-motion:reduce){.t{animation-duration:%dms}.g{animation:none}}' % (dur * 3)
           + '</style>')
    paths = ''.join(f'<path class="t" style="transform-origin:{p["tcx"]}px {p["tcy"]}px;--d:-{round(p["phase"] * dur)}ms" '
                    f'fill="{p["color"]}" d="{path_d(p)}"/>' for p in P)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" role="img">'
           f'<title>Carregando</title>{css}<g class="g">{paths}</g></svg>')
    open(f'{OUT}/berp_loader_{name}.svg', 'w').write(svg)

    # ---- Android AnimatedVectorDrawable (API 21+). Each tile starts at its phase via startOffset, then loops forever.
    half = dur // 2
    groups, targets = [], []
    for i, p in enumerate(P):
        off = round(p['phase'] * dur)  # tile is at full brightness when the wave reaches its angle
        groups.append(f'''            <group android:name="g{i}" android:pivotX="{p["tcx"]}" android:pivotY="{p["tcy"]}">
                <path android:name="p{i}" android:fillColor="{p["color"]}" android:pathData="{path_d(p)}"/>
            </group>''')
        anim = lambda prop, a, b: (f'<objectAnimator android:propertyName="{prop}" android:valueFrom="{a}" android:valueTo="{b}" '
                                   f'android:duration="{half}" android:startOffset="{off}" android:repeatCount="infinite" '
                                   f'android:repeatMode="reverse" android:interpolator="@android:interpolator/accelerate_decelerate"/>')
        targets.append(f'''    <target android:name="g{i}">
        <aapt:attr name="android:animation">
            <set>
                {anim("scaleX", 1, smin)}
                {anim("scaleY", 1, smin)}
            </set>
        </aapt:attr>
    </target>
    <target android:name="p{i}">
        <aapt:attr name="android:animation">
            {anim("fillAlpha", 1, round(omin / 100, 2))}
        </aapt:attr>
    </target>''')
    rot = f'''    <target android:name="globe">
        <aapt:attr name="android:animation">
            <objectAnimator android:propertyName="rotation" android:valueFrom="0" android:valueTo="360"
                android:duration="{dur}" android:repeatCount="infinite" android:interpolator="@android:interpolator/linear"/>
        </aapt:attr>
    </target>
''' if rotate else ''
    avd = f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Berp Sistemas globe loading spinner ({name}). Call start() on the drawable; it loops until stop(). -->
<animated-vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt">
    <aapt:attr name="android:drawable">
        <vector android:width="64dp" android:height="64dp"
            android:viewportWidth="{SIZE}" android:viewportHeight="{SIZE}">
            <group android:name="globe" android:pivotX="{SIZE / 2}" android:pivotY="{SIZE / 2}">
{chr(10).join(groups)}
            </group>
        </vector>
    </aapt:attr>
{rot}{chr(10).join(targets)}
</animated-vector>
'''
    open(f'{OUT}/avd_berp_loader_{name}.xml', 'w').write(avd)
    print(name, 'period', T, 'frames')

for n, v in VARIANTS.items(): build(n + SUF, **v)
