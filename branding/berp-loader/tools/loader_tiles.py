"""Per-tile looping loaders built from the globe tiles in pieces.json (Lottie, animated SVG, Android AVD).

  build   - tiles snap in one by one until the globe is complete, then leave in the same order (2.6 s loop)
  twinkle - every tile pulses on its own, each at a different moment (1.6 s loop)
  breathe - the ball compacts (tiles pull in until they touch) and then expands (gaps open wide) (2 s loop)
  whirl   - the ball compacts, spins fast, expands while it slows down, stops in the original shape, then compacts again (2.5 s loop)
  whirl_fast - same as whirl with four turns, quicker (2.4 s loop)

Pass --gray to build grayscale versions (files end in _gray).

Every tile plays the same short timeline (TRACKS), started at its own offset inside the loop.
"""
import json, math, sys, os, random

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

FPS, SIZE, PAD = 60, 512, 8
CX, CY, R = 210.05, 514.41, 251.1   # circle fitted to the globe silhouette
SC = (SIZE / 2 - PAD) / R
def tx(x): return round((x - CX) * SC + SIZE / 2, 1)
def ty(y): return round((y - CY) * SC + SIZE / 2, 1)
for p in P: p['tcx'], p['tcy'] = tx(p['cx']), ty(p['cy'])

# easing: (css/lottie cubic-bezier, android interpolator)
EASE = {
    'lin': ((0.333, 0.333, 0.667, 0.667), 'linear'),
    'back': ((0.34, 1.56, 0.64, 1.0), 'overshoot'),
    'out': ((0.33, 1.0, 0.68, 1.0), 'decelerate_cubic'),
    'in': ((0.32, 0.0, 0.67, 0.0), 'accelerate_cubic'),
    'io': ((0.65, 0.0, 0.35, 1.0), 'accelerate_decelerate'),
}

# tracks: property -> [(frame, value, ease into the next keyframe)]; scale/opacity in %, rotation in degrees
VARIANTS = {
    'build': dict(T=156, rotates=True, tracks={
        'scale':   [(0, 0, 'back'), (22, 100, 'lin'), (84, 100, 'in'), (98, 0, 'lin')],
        'opacity': [(0, 0, 'lin'), (8, 100, 'lin'), (92, 100, 'lin'), (98, 0, 'lin')],
        'rotation': [(0, -30, 'out'), (22, 0, 'lin')],
    }),
    'twinkle': dict(T=96, rotates=False, tracks={
        'scale':   [(0, 100, 'io'), (14, 55, 'out'), (30, 106, 'io'), (36, 100, 'lin')],
        'opacity': [(0, 100, 'io'), (14, 45, 'out'), (30, 100, 'lin')],
    }),
    # spread: distance of each tile from the ball centre, in % (100 = original layout)
    'breathe': dict(T=120, rotates=False, zoom=0.86, tracks={
        'scale':   [(0, 100, 'io'), (40, 72, 'lin'), (50, 72, 'io'), (80, 90, 'io'), (106, 100, 'lin')],
        'spread':  [(0, 100, 'io'), (40, 55, 'lin'), (50, 55, 'io'), (80, 116, 'io'), (106, 100, 'lin')],
        'opacity': [(0, 100, 'lin')],
    }),
    # spin: rotation of the whole ball in degrees (two full turns, so it stops exactly in the original position)
    'whirl': dict(T=150, rotates=False, tracks={
        'scale':   [(0, 100, 'io'), (28, 72, 'lin'), (58, 72, 'out'), (98, 100, 'lin')],
        'spread':  [(0, 100, 'io'), (28, 55, 'lin'), (58, 55, 'out'), (98, 100, 'lin')],
        'opacity': [(0, 100, 'lin')],
    }, spin=[(0, 0, 'lin'), (12, 0, 'in'), (58, 360, 'out'), (106, 720, 'lin')]),
    # four turns: speeds up for 2 turns while compact, slows down over 2 more while it expands
    'whirl_fast': dict(T=144, rotates=False, tracks={
        'scale':   [(0, 100, 'io'), (24, 72, 'lin'), (50, 72, 'out'), (92, 100, 'lin')],
        'spread':  [(0, 100, 'io'), (24, 55, 'lin'), (50, 55, 'out'), (92, 100, 'lin')],
        'opacity': [(0, 100, 'lin')],
    }, spin=[(0, 0, 'lin'), (10, 0, 'in'), (50, 720, 'out'), (92, 1440, 'lin')]),
}
gx0 = min(p['cx'] for p in P); gx1 = max(p['cx'] for p in P)
gy0 = min(p['cy'] for p in P); gy1 = max(p['cy'] for p in P)
def sweep(p): return 0.78 * (p['cx'] - gx0) / (gx1 - gx0) + 0.22 * (p['cy'] - gy0) / (gy1 - gy0)
def dist(p): return min(1.0, math.hypot(p['tcx'] - SIZE / 2, p['tcy'] - SIZE / 2) / (SIZE / 2 - PAD))
rng = random.Random(7)
SHIFTS = {
    'build': lambda p: round(sweep(p) * 46 + rng.uniform(0, 2)),   # left-to-right, slightly irregular
    'twinkle': lambda p: rng.randrange(96),                         # random moment for each tile
    'breathe': lambda p: round(dist(p) * 10),                       # outer tiles follow a little later
    'whirl': lambda p: round(dist(p) * 6),
    'whirl_fast': lambda p: round(dist(p) * 6),
}

def path_d(p):
    return ''.join('M' + ' '.join(f'{tx(x)} {ty(y)}' for x, y in pa['pts']) + 'Z' for pa in p['paths'])

def rgb(hexc):
    h = hexc.lstrip('#'); return [round(int(h[i:i + 2], 16) / 255, 4) for i in (0, 2, 4)] + [1]

def lottie_prop(track, dims, fn=None):
    """Keyframes in the layer's own time (start = 0)."""
    if len(track) == 1:
        v = track[0][1]; return {'a': 0, 'k': fn(v) if fn else v if dims == 1 else [v, v, 100]}
    ks = []
    for j, (t, v, e) in enumerate(track):
        val = fn(v) if fn else [v] * dims if dims != 3 else [v, v, 100]
        k = {'t': t, 's': val}
        if j < len(track) - 1:
            b = EASE[e][0]
            k['o'] = {'x': [b[0]] * dims, 'y': [b[1]] * dims}; k['i'] = {'x': [b[2]] * dims, 'y': [b[3]] * dims}
        ks.append(k)
    return {'a': 1, 'k': ks}

def build(name, T, rotates, tracks, zoom=1.0, spin=None):
    shift = SHIFTS[name.removesuffix('_gray')]
    spread = 'spread' in tracks
    C = SIZE / 2
    zs = round(zoom * 100, 2)
    dur = round(T * 1000 / FPS)
    layers, assets, svg_paths, groups, targets = [], [], [], [], []
    for i, p in enumerate(P):
        s = shift(p) % T
        vx, vy = round(p['tcx'] - C, 2), round(p['tcy'] - C, 2)   # tile offset from the ball centre
        shapes = [{'ty': 'sh', 'ks': {'a': 0, 'k': {'c': True, 'v': [[tx(x), ty(y)] for x, y in pa['pts']],
                   'i': [[0, 0]] * len(pa['pts']), 'o': [[0, 0]] * len(pa['pts'])}}} for pa in p['paths']]
        shapes += [{'ty': 'fl', 'c': {'a': 0, 'k': rgb(p['color'])}, 'o': {'a': 0, 'k': 100}, 'r': 1},
                   {'ty': 'tr', 'p': {'a': 0, 'k': [0, 0]}, 'a': {'a': 0, 'k': [0, 0]}, 's': {'a': 0, 'k': [100, 100]},
                    'r': {'a': 0, 'k': 0}, 'o': {'a': 0, 'k': 100}}]
        ks = {'o': lottie_prop(tracks['opacity'], 1),
              'r': lottie_prop(tracks['rotation'], 1) if rotates else {'a': 0, 'k': 0},
              'p': (lottie_prop(tracks['spread'], 3, lambda v: [round(C + vx * v / 100, 2), round(C + vy * v / 100, 2), 0])
                    if spread else {'a': 0, 'k': [p['tcx'], p['tcy'], 0]}),
              'a': {'a': 0, 'k': [p['tcx'], p['tcy'], 0]},
              's': lottie_prop(tracks['scale'], 3)}
        # The tile is drawn once in a precomp; its timeline starts at s and wraps around the loop:
        # one instance covers [s, T), a second started one loop earlier covers [0, s). Exact and seamless.
        assets.append({'id': f't{i}', 'layers': [{'ddd': 0, 'ind': 1, 'ty': 4, 'nm': f'tile_{i}', 'sr': 1, 'ao': 0,
                       'ip': 0, 'op': T, 'st': 0, 'bm': 0, 'ks': ks, 'shapes': [{'ty': 'gr', 'nm': 'g', 'it': shapes}]}]})
        for st, ip, op in [(s, s, T), (s - T, 0, s)]:
            if op > ip:
                layers.append({'ddd': 0, 'ind': len(layers) + 1, 'ty': 0, 'nm': f'tile_{i}', 'refId': f't{i}',
                               'sr': 1, 'ao': 0, 'w': SIZE, 'h': SIZE, 'ip': ip, 'op': op, 'st': st, 'bm': 0,
                               **({'parent': 9999} if spin else {}),
                               'ks': {'o': {'a': 0, 'k': 100}, 'r': {'a': 0, 'k': 0}, 'p': {'a': 0, 'k': [C, C, 0]},
                                      'a': {'a': 0, 'k': [C, C, 0]}, 's': {'a': 0, 'k': [zs, zs, 100]}}})
        # SVG: a negative delay makes the tile's timeline start s frames into the loop, already running
        delay = round(s * 1000 / FPS) - dur
        svg_paths.append(f'<path class="t" style="transform-origin:{p["tcx"]}px {p["tcy"]}px;animation-delay:{delay}ms'
                         + (f';--vx:{vx}px;--vy:{vy}px' if spread else '') + '" '
                         f'fill="{p["color"]}" d="{path_d(p)}"/>')
        # AVD: startOffset puts each tile at its moment; repeats then follow back to back
        def anim(prop, track, scale_by):
            kf = ''.join(f'\n                        <keyframe android:fraction="{round(t / T, 4)}" android:value="{round(v * scale_by, 3)}"'
                         + ('' if j == 0 else f' android:interpolator="@android:interpolator/{EASE[track[j - 1][2]][1]}"') + '/>'
                         for j, (t, v, e) in enumerate(track + [(T, track[-1][1], 'lin')]))
            return (f'\n                <objectAnimator android:duration="{dur}" android:startOffset="{round(s * 1000 / FPS)}" '
                    f'android:repeatCount="infinite" android:interpolator="@android:interpolator/linear">'
                    f'\n                    <propertyValuesHolder android:propertyName="{prop}" android:valueType="floatType">{kf}'
                    f'\n                    </propertyValuesHolder>\n                </objectAnimator>')
        end = {k: v[-1][1] for k, v in tracks.items()}   # resting state before a tile's first start
        groups.append(f'''        <group android:name="g{i}" android:pivotX="{p["tcx"]}" android:pivotY="{p["tcy"]}" android:scaleX="{end['scale'] / 100}" android:scaleY="{end['scale'] / 100}">
            <path android:name="p{i}" android:fillColor="{p["color"]}" android:fillAlpha="{end['opacity'] / 100}" android:pathData="{path_d(p)}"/>
        </group>''')
        gset = anim('scaleX', tracks['scale'], 0.01) + anim('scaleY', tracks['scale'], 0.01)
        if rotates: gset += anim('rotation', tracks['rotation'], 1)
        if spread:
            for prop, v in (('translateX', vx), ('translateY', vy)):
                gset += anim(prop, [(t, k - 100, e) for t, k, e in tracks['spread']], v / 100)
        targets.append(f'''    <target android:name="g{i}">
        <aapt:attr name="android:animation">
            <set>{gset}
            </set>
        </aapt:attr>
    </target>
    <target android:name="p{i}">
        <aapt:attr name="android:animation">{anim('fillAlpha', tracks['opacity'], 0.01)}
        </aapt:attr>
    </target>''')

    if spin:   # null layer that turns the whole ball; every tile instance is parented to it
        layers.append({'ddd': 0, 'ind': 9999, 'ty': 3, 'nm': 'ball', 'sr': 1, 'ao': 0, 'ip': 0, 'op': T, 'st': 0, 'bm': 0,
                       'ks': {'o': {'a': 0, 'k': 100}, 'r': lottie_prop(spin, 1), 'p': {'a': 0, 'k': [C, C, 0]},
                              'a': {'a': 0, 'k': [C, C, 0]}, 's': {'a': 0, 'k': [100, 100, 100]}}})
    json.dump({'v': '5.7.4', 'fr': FPS, 'ip': 0, 'op': T, 'w': SIZE, 'h': SIZE, 'nm': f'Berp loader {name}', 'ddd': 0,
               'assets': assets, 'layers': layers, 'markers': []},
              open(f'{OUT}/berp_loader_{name}.json', 'w'), separators=(',', ':'))

    def css_track(kname, prop, track, fmt):
        frames = ''.join(f'{round(t / T * 100, 2)}%{{{prop}:{fmt(v)};animation-timing-function:cubic-bezier{EASE[e][0]}}}'
                         for t, v, e in track)
        return f'@keyframes {kname}{{{frames}100%{{{prop}:{fmt(track[-1][1])}}}}}'
    anims = [('ks', 'scale', tracks['scale'], lambda v: round(v / 100, 3)),
             ('ko', 'opacity', tracks['opacity'], lambda v: round(v / 100, 3))]
    if rotates: anims.append(('kr', 'rotate', tracks['rotation'], lambda v: f'{v}deg'))
    if spread:
        anims.append(('kt', 'translate', tracks['spread'],
                      lambda v: f'calc(var(--vx)*{round(v / 100 - 1, 3)}) calc(var(--vy)*{round(v / 100 - 1, 3)})'))
    css = ('<style>.t{transform-box:view-box;animation-name:' + ','.join(a[0] for a in anims)
           + f';animation-duration:{dur}ms;animation-iteration-count:infinite;animation-timing-function:linear}}'
           + ''.join(css_track(*a) for a in anims)
           + (f'.b{{transform-box:view-box;transform-origin:{C}px {C}px;animation:kspin {dur}ms linear infinite}}'
              + css_track('kspin', 'rotate', spin, lambda v: f'{v}deg') if spin else '')
           + f'@media (prefers-reduced-motion:reduce){{.t{{animation-duration:{dur * 3}ms}}.b{{animation:none}}}}</style>')
    open(f'{OUT}/berp_loader_{name}.svg', 'w').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" role="img">'
        f'<title>Carregando</title>{css}'
        + (f'<g transform="translate({C} {C}) scale({zoom}) translate({-C} {-C})">' if zoom != 1 else '<g>')
        + ('<g class="b">' if spin else '<g>') + f'{"".join(svg_paths)}</g></g></svg>')

    spin_target = ''
    if spin:
        kf = ''.join(f'\n                        <keyframe android:fraction="{round(t / T, 4)}" android:value="{v}"'
                     + ('' if j == 0 else f' android:interpolator="@android:interpolator/{EASE[spin[j - 1][2]][1]}"') + '/>'
                     for j, (t, v, e) in enumerate(spin + [(T, spin[-1][1], 'lin')]))
        spin_target = f'''    <target android:name="ball">
        <aapt:attr name="android:animation">
            <objectAnimator android:duration="{dur}" android:repeatCount="infinite" android:interpolator="@android:interpolator/linear">
                <propertyValuesHolder android:propertyName="rotation" android:valueType="floatType">{kf}
                </propertyValuesHolder>
            </objectAnimator>
        </aapt:attr>
    </target>
'''
    open(f'{OUT}/avd_berp_loader_{name}.xml', 'w').write(f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Berp Sistemas globe loading spinner ({name}). Call start() on the drawable; it loops until stop().
     Uses keyframes: native on Android 6.0+ (API 23); on older versions load it with AnimatedVectorDrawableCompat. -->
<animated-vector xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:aapt="http://schemas.android.com/aapt">
    <aapt:attr name="android:drawable">
        <vector android:width="64dp" android:height="64dp"
            android:viewportWidth="{SIZE}" android:viewportHeight="{SIZE}">
        <group android:name="ball" android:pivotX="{C}" android:pivotY="{C}" android:scaleX="{zoom}" android:scaleY="{zoom}">
{chr(10).join(groups)}
        </group>
        </vector>
    </aapt:attr>
{spin_target}{chr(10).join(targets)}
</animated-vector>
''')
    print(name, 'period', T, 'layers', len(layers))

for n, v in VARIANTS.items():
    if len(sys.argv) <= 3 or n in sys.argv[3].split(','): build(n + SUF, **v)
