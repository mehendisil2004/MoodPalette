"""MoodPalette ML engine: K-means profiling, content-based colour retrieval,
CIELAB distances and colour-harmony rules."""
import colorsys, math, random
import numpy as np, pandas as pd
from sklearn.cluster import KMeans

TRAITS = ["introversion", "creativity", "adventurousness", "calmness", "romanticism"]
FEATS = ["warmth", "energy", "softness", "depth", "vividness", "romance"]
MOODS = {  # mood -> desired colour-feature vector
    "happy": [.8, .8, .5, .1, .7, .4], "dreamy": [.3, .2, .9, .2, .3, .7],
    "calm": [.2, .1, .8, .3, .2, .2], "romantic": [.8, .4, .7, .2, .5, 1],
    "energetic": [.9, 1, .2, .2, 1, .3], "melancholic": [.1, .1, .4, .8, .2, .3],
    "mysterious": [.2, .3, .2, 1, .5, .4]}
# trait -> colour-feature influence matrix (5 x 6)
W = np.array([[-.2, -.6, .4, .5, -.5, 0], [.1, .3, 0, 0, .6, .2], [.5, .8, -.3, 0, .5, -.2],
              [-.3, -.7, .6, 0, -.6, .1], [.4, -.1, .4, -.2, 0, .9]])
ARCH = {"The Dreamy Romantic": [.4, .6, .3, .7, .95], "The Quiet Soul": [.9, .5, .2, .8, .4],
        "The Free Spirit": [.2, .8, .95, .3, .5], "The Creative Muse": [.5, .95, .6, .4, .6],
        "The Zen Minimalist": [.7, .3, .3, .95, .3]}
HUES = ["Rose", "Apricot", "Butter", "Pistachio", "Sage", "Mint", "Aqua", "Sky", "Periwinkle", "Lavender", "Orchid", "Peony"]
TONES = {.93: "Cream", .88: "Milky", .78: "Powder", .65: "Soft", .5: "Rich", .35: "Velvet", .22: "Midnight"}
ADJ = {"happy": ["Sunlit", "Giggly"], "dreamy": ["Hazy", "Cloudborn"], "calm": ["Quiet", "Still"],
       "romantic": ["Blushing", "Love-struck"], "energetic": ["Electric", "Spark"],
       "melancholic": ["Rainy", "Faded"], "mysterious": ["Moonlit", "Veiled"]}
NOUN = ["Reverie", "Bouquet", "Whisper", "Daydream", "Ribbon", "Haze", "Diary"]
PHRASE = {"warmth": "its warm undertone echoes the glow of your {m} mood",
          "energy": "its lively intensity matches your {m} spark",
          "softness": "its gentle softness suits your {m} state and a tender personality",
          "depth": "its deep, rich tone gives {m} feelings room to breathe",
          "vividness": "its saturated pop reflects your expressive side",
          "romance": "its rosy-lavender character speaks to your romantic heart"}

def _g(h, c, w=40):
    d = min(abs(h - c), 360 - abs(h - c)); return math.exp(-d * d / (2 * w * w))

def _build():
    rows = []
    for h in range(0, 360, 12):
        for s, l in [(.55, .88), (.45, .78), (.6, .65), (.7, .5), (.5, .35), (.45, .22), (.15, .93)]:
            r, g, b = colorsys.hls_to_rgb(h / 360, l, s)
            soft = min(1, l * (1.2 - s))
            f = dict(warmth=(1 + math.cos(math.radians(h - 30))) / 2,
                     energy=min(1, s * 1.2 * max(0, 1 - abs(l - .55) * 1.2)), softness=soft, depth=1 - l,
                     vividness=s * (1 - abs(l - .5) * .8),
                     romance=min(1, (.3 * soft + .7 * max(_g(h, 335), _g(h, 290))) * (.4 + s)))
            rows.append(dict(hex="#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255)),
                             name=f"{TONES[l]} {HUES[h // 30]}", h=h, s=s, l=l, **f))
    return pd.DataFrame(rows)

def to_lab(hexc):
    c = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    x, y, z = np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]) @ c
    f = lambda t: t ** (1 / 3) if t > .008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x / .95047), f(y), f(z / 1.08883)
    return np.array([116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)])

def delta_e(a, b): return float(np.linalg.norm(a - b))  # CIE76

DF = _build()
DF["lab"] = DF.hex.map(to_lab)
F = DF[FEATS].values

# --- K-means personality profiling on a synthetic persona dataset ---
_rng = np.random.RandomState(0)
_X = np.vstack([np.clip(np.array(c) + _rng.normal(0, .12, (60, 5)), 0, 1) for c in ARCH.values()])
KM = KMeans(5, n_init=10, random_state=0).fit(_X)
_names = list(ARCH)
CLUSTER = {i: _names[int(np.argmin([np.linalg.norm(KM.cluster_centers_[i] - np.array(v)) for v in ARCH.values()]))] for i in range(5)}

def profile(traits):
    t = np.array([float(traits.get(k, .5)) for k in TRAITS])
    cl = int(KM.predict([t])[0])
    return t, CLUSTER[cl], .7 * t + .3 * KM.cluster_centers_[cl]

def _sims(traits, mood):
    t, arch, prof = profile(traits)
    P = np.clip(.5 + (prof - .5) @ W, 0, 1)
    target = .55 * np.array(MOODS[mood]) + .45 * P
    a, b = F - .5, target - .5   # content-based: cosine similarity of centred feature vectors
    sims = (a @ b) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b) + 1e-9)
    return t, arch, target, sims

def _pick(target_lab, idx, sims, chosen, w=40, min_de=12):
    best, bs = None, 1e9
    for i in idx:
        lab = DF.lab[i]
        if any(delta_e(lab, c) < min_de for c in chosen): continue
        sc = delta_e(lab, target_lab) + w * (1 - sims[i])
        if sc < bs: best, bs = i, sc
    return best

def _why(i, role, target, mood):
    r = DF.iloc[i]; k = max(range(6), key=lambda j: r[FEATS[j]] * (1 - abs(r[FEATS[j]] - target[j])))
    return f"{role}: {PHRASE[FEATS[k]].format(m=mood)}."

def recommend(traits, mood, n=6, seed=None):
    rng = random.Random(seed)
    t, arch, target, sims = _sims(traits, mood)
    top = list(np.argsort(-sims)[:8]); anchor = rng.choices(top, weights=[8 - k for k in range(8)])[0]
    pool = list(np.argsort(-sims)[:90])
    tr = dict(zip(TRAITS, t))
    scheme, offs = (("analogous", [-30, 30, 15, -15]) if tr["calmness"] > .65 else
                    ("triadic", [120, 240, 60, 180]) if tr["adventurousness"] > .65 else
                    ("split-complementary", [150, 210, 30, -30]) if tr["creativity"] > .65 else
                    ("complementary", [180, 30, -30, 150]))
    a = DF.iloc[anchor]; chosen = [anchor]; roles = {anchor: "Your heart colour"}
    labs = lambda: [DF.lab[i] for i in chosen]
    # complementary accent via CIELAB inversion (a*, b* negated)
    la = DF.lab[anchor]; comp = _pick(np.array([la[0], -la[1], -la[2]]), pool, sims, labs(), 25, 20)
    if comp is not None: chosen.append(comp); roles[comp] = "Complementary accent"
    for off in offs:   # harmony-rule hue targets, resolved to nearest in-pool colour
        if len(chosen) >= n - 1: break
        r, g, b = colorsys.hls_to_rgb(((a.h + off) % 360) / 360, a.l, a.s)
        i = _pick(to_lab("#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))), pool, sims, labs())
        if i is not None: chosen.append(i); roles[i] = f"{scheme.title()} harmony"
    light = [i for i in np.argsort(-sims) if DF.l[i] >= .88 and all(delta_e(DF.lab[i], c) > 8 for c in labs())]
    if light: chosen.append(light[0]); roles[light[0]] = "Soft neutral base"
    chosen = sorted(chosen[:7], key=lambda i: -DF.l[i])
    name = f"{rng.choice(ADJ[mood])} {HUES[int(a.h) // 30]} {rng.choice(NOUN)}"
    return dict(name=name, archetype=arch, scheme=scheme, mood=mood, traits=tr,
                colors=[dict(hex=DF.hex[i], name=DF.name[i], role=roles[i], why=_why(i, roles[i], target, mood)) for i in chosen])

def replace_colour(hexes, idx, traits, mood, seed=None):
    rng = random.Random(seed)
    _, _, target, sims = _sims(traits, mood)
    old = to_lab(hexes[idx]); others = [to_lab(h) for k, h in enumerate(hexes) if k != idx]
    cands = []
    for i in np.argsort(-sims)[:100]:
        if DF.hex[i] in hexes: continue
        lab = DF.lab[i]
        if delta_e(lab, old) < 8 or any(delta_e(lab, o) < 12 for o in others): continue
        cands.append((delta_e(lab, old) + 40 * (1 - sims[i]), i))
    i = rng.choice(sorted(cands)[:3])[1]
    return dict(hex=DF.hex[i], name=DF.name[i], why=_why(i, "Swapped in", target, mood))
