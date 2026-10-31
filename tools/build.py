"""Gera todo o site: PT na raiz, EN em /en/. Rode: python tools/build.py"""
import json, os, re, shutil, sys, html
from urllib.parse import quote_plus

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import genres_1, genres_2, genres_3, genres_4
from genres_3 import EXT, CLADES
from content import CONCEPTS, TIERS, DECADES, UI, PRIVACY

SITE = "https://typesofrock.biblioverse.org"
LISTS = json.load(open(os.path.join(HERE, "lists.json"), encoding="utf8"))
GENRES = genres_1.GENRES + genres_2.GENRES + genres_3.GENRES + genres_4.GENRES
BY = {g["id"]: g for g in GENRES}
for gid, extra in genres_4.ADD_PARENTS.items():
    BY[gid]["parents"] += extra
SHORT = {"rnb": "R&B", "beat": "Beat", "nwobhm": "NWOBHM", "brazilian-rock": "BRock", "arena-rock": "Arena Rock",
         "shoegaze": "Shoegaze", "rap-rock": "Rap Rock", "rock-n-roll": "Rock'n'Roll", "street-punk": "Oi!", "visual-kei": "Visual Kei", "jazz-rock": "Fusion", "folk-punk": "Folk Punk", "madchester": "Madchester", "melodic-death-metal": "Melodeath", "neue-deutsche-harte": "NDH", "post-punk-revival": "PP Revival"}
LISTKEY = {"rockabilly": "rockabilly", "rock-classico": "classic-rock"}
FIX = {"Tokyo Hotel": "Tokio Hotel"}

for g in GENRES:
    g["children"] = [c["id"] for c in GENRES if g["id"] in c["parents"]]
    for p in g["parents"] + g["similar"]:
        assert p in BY, (g["id"], p)
    for p in g["parents"]:
        assert BY[p]["year"] <= g["year"], (g["id"], p)
    assert len(g["genome"]) == 8, g["id"]
    if isinstance(g["names"], str):
        L = LISTS["genres"][g["names"]]
        g["artists"], g["top"] = [FIX.get(x, x) for x in L["names"]], L["top"]
    else:
        g["artists"], g["top"] = g["names"], min(10, len(g["names"]))
    assert len(set(a.lower() for a in g["artists"])) == len(g["artists"]), (g["id"], [a for a in g["artists"] if g["artists"].count(a) > 1])
ORDER = sorted(GENRES, key=lambda g: (g["year"], g["name"]["pt"]))
CLADE_IDS = list(CLADES)

PATHS = {"pt": dict(home="index.html", dir="generos", genres="generos.html", evo="evolucao.html", lab="laboratorio.html", songs="musicas.html", bands="bandas.html", about="sobre.html"),
         "en": dict(home="index.html", dir="genres", genres="genres.html", evo="evolution.html", lab="lab.html", songs="songs.html", bands="bands.html", about="about.html")}


def norm(s):
    s = s.lower().replace("’", "'").strip()
    s = re.sub(r"^the ", "", s)
    s = re.sub(r"[^\w]+", "", s)
    return s


ALIAS = {"jimihendrixexperience": "jimihendrix", "frankzappamothersofinvention": "frankzappa", "paulmccartneywings": "paulmccartney",
         "joanjettblackhearts": "joanjett", "billhaleyhiscomets": "billhaley", "tomyhotel": "tokiohotel", "tokyohotel": "tokiohotel",
         "derekanddominos": "ericclapton", "guns": "gunsnroses", "pod": "pod"}


def akey(s):
    k = norm(s)
    return ALIAS.get(k, k)


ARTIST = {}
for g in ORDER:
    for a in g["artists"]:
        ARTIST.setdefault(akey(a), []).append(g["id"])


def artist_genres(name):
    out = []
    for part in re.split(r"[;,]| & | feat\.? ", name):
        for gid in ARTIST.get(akey(part), []):
            if gid not in out:
                out.append(gid)
    return out if out else ARTIST.get(akey(name), [])


def e(s):
    return html.escape(str(s), quote=True)


def radar(v, color, size=320, labels=None):
    c, r = size / 2, size * (.33 if labels else .46)
    import math

    def pts(vals):
        out = []
        for i, x in enumerate(vals):
            a = -math.pi / 2 + i * math.pi / 4
            q = r * x / 10
            out.append(f"{c + q * math.cos(a):.1f},{c + q * math.sin(a):.1f}")
        return " ".join(out)
    pad = 50 if labels else 0
    s = f'<svg viewBox="{-pad} 0 {size + 2 * pad} {size}" role="img" aria-hidden="true">'
    for level in ([2.5, 5, 7.5, 10] if labels else [5, 10]):
        s += f'<polygon class="radar-grid" points="{pts([level] * 8)}"/>'
    if labels:
        for i, n in enumerate(labels):
            a = -math.pi / 2 + i * math.pi / 4
            x, y, cs = c + (r + 9) * math.cos(a), c + (r + 9) * math.sin(a), math.cos(a)
            anc = "start" if cs > .3 else "end" if cs < -.3 else "middle"
            s += f'<text x="{x:.1f}" y="{y + 4:.1f}" font-size="10.5" fill="currentColor" text-anchor="{anc}">{e(n)}</text>'
    s += f'<polygon points="{pts(v)}" fill="{color}" fill-opacity=".4" stroke="{color}" stroke-width="{2 if labels else 1.6}"/>'
    return s + "</svg>"


LOGO = '<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 3C44 3 55 6 59 14C62 21 56 33 48 45C42 54 37 61 32 61C27 61 22 54 16 45C8 33 2 21 5 14C9 6 20 3 32 3Z" fill="currentColor"/></svg>'


class Page:
    def __init__(self, lang):
        self.lang, self.t, self.p = lang, UI[lang], PATHS[lang]

    def href(self, depth, target):
        return "../" * depth + target

    def genre_url(self, depth, gid):
        return self.href(depth, f"{self.p['dir']}/{gid}.html")

    def write(self, rel, other, depth, title, desc, body, cur="", og_alt=None):
        lang, t, p = self.lang, self.t, self.p
        prefix = "" if lang == "pt" else "en/"
        canonical = f"{SITE}/{prefix}{rel}".replace("index.html", "")
        other_url = f"{SITE}/{'en/' if lang == 'pt' else ''}{other}".replace("index.html", "")
        pt_url, en_url = (canonical, other_url) if lang == "pt" else (other_url, canonical)
        assets = "../" * (depth + (1 if lang == "en" else 0))
        other_href = ("../" * depth + "en/" + other) if lang == "pt" else ("../" * (depth + 1) + other)
        nav = "".join(f'<a href="{self.href(depth, p[k])}"{" aria-current=page" if cur == k else ""}>{e(t["nav"][k])}</a>' for k in ["home", "genres", "evo", "lab", "songs", "bands", "about"])
        og = f"{SITE}/og-image{'-en' if lang == 'en' else ''}.png"
        ld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": title, "description": desc, "url": canonical, "inLanguage": t["locale"].replace("_", "-"),
                         "isPartOf": {"@type": "WebSite", "name": t["site"], "url": SITE + "/"}, "author": {"@type": "Person", "name": "Julio Cesar Prava"}}, ensure_ascii=False)
        full_title = title if title.startswith(t["site"]) else f"{title} · {t['site']}"
        doc = f"""<!doctype html>
<html lang="{t['html']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="author" content="Julio Cesar Prava">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="pt-BR" href="{pt_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="x-default" href="{pt_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(t['site'])}">
<meta property="og:locale" content="{t['locale']}">
<meta property="og:url" content="{canonical}">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og}">
<meta name="theme-color" content="#f6f0e4">
<link rel="icon" href="{assets}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{assets}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{assets}apple-touch-icon.png">
<link rel="manifest" href="{assets}site.webmanifest">
<script type="application/ld+json">{ld}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Germania+One&family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{assets}assets/style.css">
<script src="https://biblioverse.org/superbar.js" defer></script>
</head>
<body>
<nav id="bvbar" class="bvbar" data-current="typesofrock" aria-label="BiblioVerse" style="position:fixed;top:0;left:0;right:0;height:44px;z-index:9000;background:linear-gradient(90deg,#4f7cff,#7a5cff)"><a href="https://biblioverse.org" style="color:#fff;line-height:44px;padding:0 14px;font-weight:700;text-decoration:none">BiblioVerse</a></nav>
<a class="skip" href="#main">{e(t['skip'])}</a>
<header class="top"><div class="wrap">
<a class="logo" href="{self.href(depth, p['home'])}">{LOGO}{e(t['site'])}</a>
<nav class="nav" aria-label="{e(t['menu'])}">{nav}<a class="lang" href="{other_href}" hreflang="{'en' if lang == 'pt' else 'pt-BR'}" lang="{'en' if lang == 'pt' else 'pt-BR'}">{t['switch']}</a></nav>
</div></header>
<main id="main">
{body}
</main>
{t.get('promo', '')}
<footer><div class="wrap"><span>{e(t['footer'])}</span><span><a href="{self.href(depth, p['about'])}">{e(t['nav']['about'])}</a> · <a href="{self.href(depth, p['about'])}#privacy">{e(PRIVACY[lang]['h'])}</a> · <a href="https://biblioverse.org">BiblioVerse</a></span></div></footer>
<script src="{assets}assets/data-{lang}.js"></script>
<script src="{assets}assets/rock.js"></script>
</body>
</html>
"""
        path = os.path.join(ROOT, prefix, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf8", newline="\n") as f:
            f.write(doc)
        URLS.append((canonical, pt_url, en_url))


URLS = []
TOTAL_ARTISTS = len(ARTIST)
TOTAL_SONGS = sum(len(v) for v in LISTS["decades"].values())


def yt(q):
    return "https://www.youtube.com/results?search_query=" + quote_plus(q)


def clink(pg, depth, ids):
    if not ids:
        return f'<p class="none">{e(pg.t["none"])}</p>'
    return '<div class="chips">' + "".join(f'<a href="{pg.genre_url(depth, i)}">{e(BY[i]["name"][pg.lang])}</a>' for i in ids) + "</div>"


def main_lineage(g):
    chain = [g]
    while chain[0]["parents"]:
        chain.insert(0, BY[chain[0]["parents"][0]])
    return chain


def page_home(pg):
    t, L = pg.t, pg.lang
    legend = "".join(f'<button type="button" data-clade="{c}" aria-pressed="false"><i class="swatch" style="background:{CLADES[c][2]}"></i>{e(CLADES[c][0 if L == "pt" else 1])}</button>' for c in CLADE_IDS)
    doors = "".join(f'<a class="door" href="{pg.p[k]}"><span class="mono">{e(m)}</span><h3>{e(h.format(n=len(GENRES)))}</h3><p>{e(d)}</p></a>' for k, m, h, d in t["doors"])
    clades = "".join(
        f'<div class="door" style="border-left:3px solid {CLADES[c][2]}"><span class="mono">{sum(1 for g in GENRES if g["clade"] == c)} {e(t["spp"])}</span><h3>{e(CLADES[c][0 if L == "pt" else 1])}</h3><p>{e(CLADES[c][3 if L == "pt" else 4])}</p></div>'
        for c in CLADE_IDS)
    body = f"""<section class="stage" aria-label="{e(t['treeLabel'])}">
<svg id="tree" role="group" aria-label="{e(t['treeLabel'])}"></svg>
<div class="hero"><h1>{t['heroH']}</h1><p>{e(t['heroP'].format(n=len(GENRES)))}</p></div>
<div class="tools"><input id="find" list="gl" type="search" placeholder="{e(t['find'])}" aria-label="{e(t['find'])}"><datalist id="gl">{''.join(f'<option value="{e(g["name"][L])}">' for g in ORDER)}</datalist>
<button class="btn" id="zout" aria-label="{e(t['zoomOut'])}">−</button><button class="btn" id="zin" aria-label="{e(t['zoomIn'])}">+</button><button class="btn" id="zfit" aria-label="{e(t['zoomFit'])}">⤢</button></div>
<div class="legend" role="group" aria-label="{e(t['clades'])}">{legend}</div>
<aside class="panel" id="panel" aria-live="polite"></aside>
<div class="hint">{e(t['hint'])}</div>
<div class="clock"><button class="btn pri" id="playClock" type="button">▶ {e(t['evolve'])}</button><input id="year" type="range" min="1900" max="2026" value="2026" aria-label="{e(t['clock'])}"><span class="mono" id="yearCount" style="white-space:nowrap"></span></div>
</section>
<noscript><div class="wrap"><p>{e(t['noscript'])} <a href="{pg.p['genres']}">{e(t['nav']['genres'])}</a></p></div></noscript>
<section class="sec"><div class="wrap"><h2>{e(t['homeH'])}</h2><p class="lead">{e(t['homeP'])}</p><div class="grid3">{doors}</div></div></section>
<section class="sec"><div class="wrap"><h2>{e(t['cladesH'])}</h2><p class="lead">{e(t['cladesP'])}</p><div class="grid3">{clades}</div></div></section>"""
    pg.write("index.html", "index.html", 0, t["site"] + " · " + t["homeTitle"], t["homeDesc"].format(n=len(GENRES)), body, "home")


def page_genres(pg):
    t, L = pg.t, pg.lang
    cards = ""
    for g in ORDER:
        n = g["name"][L]
        c = CLADES[g["clade"]]
        search = e((n + " " + " ".join(g["artists"])).lower())
        cards += f'<a class="card" style="--c:{c[2]}" href="{pg.p["dir"]}/{g["id"]}.html" data-clade="{g["clade"]}" data-name="{e(n)}" data-year="{g["year"]}" data-kids="{len(g["children"])}" data-search="{search}">{radar(g["genome"], c[2], 100)}<div><h3>{e(n)}</h3><div class="mono">{g["year"]} · {e(c[0 if L == "pt" else 1])}</div></div></a>'
    tabs = f'<button aria-pressed="true" data-clade="all">{e(t["all"])}</button>' + "".join(f'<button aria-pressed="false" data-clade="{c}">{e(CLADES[c][0 if L == "pt" else 1])}</button>' for c in CLADE_IDS)
    body = f"""<div class="wrap"><div class="page-head"><span class="mono">{len(GENRES)} {e(t['spp'])}</span><h1>{e(t['genresH'])}</h1><p class="lead">{e(t['genresP'])}</p></div>
<div class="tabs" id="cladeTabs">{tabs}</div>
<div class="filters"><input id="q" type="search" placeholder="{e(t['genreSearch'])}" aria-label="{e(t['genreSearch'])}"><select id="sort" aria-label="{e(t['sortBy'])}"><option value="year">{e(t['sortYear'])}</option><option value="name">{e(t['sortName'])}</option><option value="kids">{e(t['sortKids'])}</option></select><span class="mono"><span id="qcount"></span> {e(t['spp'])}</span></div>
<div class="cards" id="cards">{cards}</div><div style="height:60px"></div></div>"""
    other = PATHS["en" if L == "pt" else "pt"]["genres"]
    pg.write(pg.p["genres"], other, 0, t["genresH"], t["genresDesc"].format(n=len(GENRES)), body, "genres")


def song_rows(g):
    keys = set(akey(a) for a in g["artists"])
    rows = []
    for d in LISTS["decades"].values():
        for y, s, a in d:
            if any(akey(p) in keys for p in re.split(r"[;,]", a)) or akey(a) in keys:
                rows.append((y, s, a))
    rows.sort()
    if len(rows) > 12:
        step = len(rows) / 12
        rows = [rows[int(i * step)] for i in range(12)]
    return rows


def page_genre(pg, g, i):
    t, L = pg.t, pg.lang
    other_dir = PATHS["en" if L == "pt" else "pt"]["dir"]
    n, c = g["name"][L], CLADES[g["clade"]]
    tx = g["text"][L]
    crumbs = ' <span aria-hidden="true">→</span> '.join(f'<a href="{x["id"]}.html">{e(x["name"][L])}</a>' if x is not g else f'<b>{e(x["name"][L])}</b>' for x in main_lineage(g))
    if len(main_lineage(g)) == 1:
        crumbs = e(t["rootLine"])
    ext = "".join(f'<span class="chip ext">{e(EXT[x][0 if L == "pt" else 1])}</span>' for x in g["ext"])
    ext_block = f'<h3 style="margin-top:14px">{e(t["ext"])}</h3><div class="chips">{ext}</div>' if ext else ""
    greats = "".join(f'<li class="{"top" if j < g["top"] else ""}"><a href="{yt(a)}" target="_blank" rel="noopener">{e(a)}</a></li>' for j, a in enumerate(g["artists"]))
    rows = song_rows(g)
    songs = ""
    if rows:
        items = "".join(f'<li><span class="y">{y}</span><span><a href="{yt(a + " " + s)}" target="_blank" rel="noopener">{e(s)}</a><small>{e(a)}</small></span></li>' for y, s, a in rows)
        songs = f'<section class="sec"><h2>{e(t["genreSongs"])}</h2><p class="lead">{e(t["genreSongsP"])}</p><ul class="songs">{items}</ul></section>'
    table = "".join(f"<tr><td>{e(tr)}</td><td>{v}/10</td></tr>" for tr, v in zip(t["traits"], g["genome"]))
    prev, nxt = ORDER[i - 1] if i else None, ORDER[i + 1] if i + 1 < len(ORDER) else None
    pager = '<div class="pager">' + (f'<a class="btn" href="{prev["id"]}.html">← {e(prev["name"][L])}</a>' if prev else "<span></span>") + (f'<a class="btn" href="{nxt["id"]}.html">{e(nxt["name"][L])} →</a>' if nxt else "<span></span>") + "</div>"
    body = f"""<div class="spec-head" style="--c:{c[2]}"><div class="wrap">
<a class="mono" href="../{pg.p['genres']}">← {e(t['nav']['genres'])}</a>
<h1>{e(n)}</h1>
<div class="facts"><span>{e(t['born'])} <b>{g['year']}</b></span><span>{e(t['habitat'])} <b>{e(g['place'][L])}</b></span><span>{e(t['clade'])} <b>{e(c[0 if L == 'pt' else 1])}</b></span></div>
<div class="crumbs">{crumbs}</div></div></div>
<div class="wrap"><div class="spec"><div>
<div class="trait"><span class="mono">{e(t['ctxTag'])}</span><h2>{e(t['ctx'])}</h2><p>{e(tx[0])}</p></div>
<div class="trait"><span class="mono">{e(t['sndTag'])}</span><h2>{e(t['snd'])}</h2><p>{e(tx[1])}</p></div>
<div class="trait"><span class="mono">{e(t['difTag'])}</span><h2>{e(t['dif'])}</h2><p>{e(tx[2])}</p></div>
</div>
<aside class="genome"><span class="mono">{e(t['genome'])}</span>{radar(g['genome'], c[2], 320, t['traits'])}
<table>{table}</table><button class="btn" data-play="{g['id']}">▶ {e(t['listen'])}</button><small>{e(t['synthNote'])}</small></aside></div>
<section class="sec" style="padding-top:44px"><h2>{e(t['family'])}</h2><div class="family">
<div><h3>{e(t['parents'])}</h3>{clink(pg, 1, g['parents'])}{ext_block}</div>
<div><h3>{e(t['children'])}</h3>{clink(pg, 1, g['children'])}</div>
<div><h3>{e(t['similar'])}</h3>{clink(pg, 1, g['similar'])}</div>
</div><a class="btn" href="../{pg.p['home']}#{g['id']}">{e(t['seeTree'])} →</a> <a class="btn" href="../{pg.p['lab']}">{e(t['compareBtn'])} →</a></section>
<section class="sec"><h2>{e(t['greatsH'].format(n=n))}</h2><ol class="greats">{greats}</ol></section>
{songs}{pager}</div>"""
    pg.write(f"{pg.p['dir']}/{g['id']}.html", f"{other_dir}/{g['id']}.html", 1, n, t["genreDesc"].format(n=n, y=g["year"]), body, "genres")


def page_evo(pg):
    t, L = pg.t, pg.lang
    cs = ""
    for c in CONCEPTS:
        cs += f'<article class="concept"><span class="mono">{e(c["bio"][L])}</span><h3>{e(c["name"][L])}</h3><p>{e(c["text"][L])}</p>{clink(pg, 0, c["links"])}</article>'
    decs = {}
    for g in GENRES:
        d = g["year"] // 10 * 10 if g["year"] >= 1950 else 1940
        decs[d] = decs.get(d, 0) + 1
    mx = max(decs.values())
    bars = "".join(f'<div title="{d}"><span>{n}</span><i style="height:{int(n / mx * 165)}px"></i><span>{(t["pre50"] if d == 1940 else str(d) + "s")}</span></div>' for d, n in sorted(decs.items()))
    parags = "".join(f"<p>{e(x)}</p>" for x in t["evoIntro"])
    limits = "".join(f"<li>{e(x)}</li>" for x in t["limits"])
    body = f"""<div class="wrap"><div class="page-head"><span class="mono">{e(t['evoTag'])}</span><h1>{e(t['evoH'])}</h1><div class="lead">{parags}</div></div>
<section class="sec"><h2>{e(t['mech'])}</h2><div class="concepts">{cs}</div></section>
<section class="sec"><h2>{e(t['rate'])}</h2><p class="lead">{e(t['rateP'])}</p><div class="bars" role="img" aria-label="{e(t['rate'])}">{bars}</div></section>
<section class="sec prose"><h2 style="font-size:clamp(2rem,4.6vw,3.4rem)">{e(t['limitsH'])}</h2><ul>{limits}</ul></section></div>"""
    pg.write(pg.p["evo"], PATHS["en" if L == "pt" else "pt"]["evo"], 0, t["evoH"], t["evoDesc"], body, "evo")


def page_lab(pg):
    t, L = pg.t, pg.lang
    opts = lambda sel: "".join(f'<option value="{g["id"]}"{" selected" if g["id"] == sel else ""}>{e(g["name"][L])} ({g["year"]})</option>' for g in sorted(GENRES, key=lambda g: g["name"][L]))
    sliders = "".join(f'<label class="slider"><span>{e(n)}</span><input type="range" min="0" max="10" value="{v}" aria-label="{e(n)}"><output>{v}</output></label>' for n, v in zip(t["traits"], [8, 6, 7, 5, 7, 4, 5, 5]))
    body = f"""<div class="wrap"><div class="page-head"><span class="mono">{e(t['labTag'])}</span><h1>{e(t['labH'])}</h1><p class="lead">{e(t['labP'])}</p></div>
<section style="margin-bottom:60px"><h2 style="font-size:2.2rem;margin-bottom:14px">{e(t['cmpH'])}</h2>
<div class="pick2"><select id="gA" aria-label="A">{opts('blues')}</select><button class="btn" id="swap" type="button" aria-label="{e(t['swap'])}">⇄</button><select id="gB" aria-label="B">{opts('djent')}</select><button class="btn" id="rand" type="button">{e(t['random'])}</button></div>
<div class="lab"><div class="box" id="radarBox"></div><div class="box" id="kin"></div></div></section>
<section style="margin-bottom:70px"><h2 style="font-size:2.2rem;margin-bottom:8px">{e(t['buildH'])}</h2><p class="lead" style="margin-bottom:18px">{e(t['buildP'])}</p>
<div class="lab"><div class="box" id="sliders" style="display:grid;gap:10px">{sliders}</div><div class="box" id="matchOut" aria-live="polite"></div></div></section></div>"""
    pg.write(pg.p["lab"], PATHS["en" if L == "pt" else "pt"]["lab"], 0, t["labH"], t["labDesc"], body, "lab")


def page_songs(pg):
    t, L = pg.t, pg.lang
    tabs = f'<button aria-pressed="true" data-dec="all">{e(t["allD"])}</button>'
    secs = ""
    for d, rows in LISTS["decades"].items():
        lab = t["decade"].format(d=d)
        tabs += f'<button aria-pressed="false" data-dec="{d}">{e(lab)}</button>'
        items = ""
        for y, s, a in sorted(rows, key=lambda r: r[0]):
            items += f'<li data-s="{e((s + " " + a + " " + str(y)).lower())}"><span class="y">{y}</span><span><a href="{yt(a + " " + s)}" target="_blank" rel="noopener">{e(s)}</a><small>{e(a.replace(";", ","))}</small></span></li>'
        secs += f'<section class="decade" data-dec="{d}"><h2>{e(lab)}</h2><p>{e(DECADES[d][L])}</p><ul class="songs">{items}</ul></section>'
    body = f"""<div class="wrap"><div class="page-head"><span class="mono">{TOTAL_SONGS} {e(t['songsN'])}</span><h1>{e(t['songsH'])}</h1><p class="lead">{e(t['songsP'])}</p></div>
<div class="tabs" id="decTabs">{tabs}</div>
<div class="filters"><input id="songq" type="search" placeholder="{e(t['songSearch'])}" aria-label="{e(t['songSearch'])}"><button class="btn pri" id="jukebox" type="button">{e(t['jukebox'])}</button><span class="mono"><span id="songcount"></span> {e(t['songsN'])}</span></div>
<div id="decades">{secs}</div></div>"""
    pg.write(pg.p["songs"], PATHS["en" if L == "pt" else "pt"]["songs"], 0, t["songsH"], t["songsDesc"].format(n=TOTAL_SONGS), body, "songs")


def page_bands(pg):
    t, L = pg.t, pg.lang
    table = {akey(r[0]): r for r in LISTS["table"]}
    rows, count = "", 0
    for k in "SABC":
        for name in LISTS["tiers"][k]:
            name = FIX.get(name, name)
            r = table.get(akey(name), [name, "", "", ""])
            genres = artist_genres(name)[:3]
            count += 1
            gl = '<div class="chips">' + "".join(f'<a href="{pg.p["dir"]}/{i}.html">{e(BY[i]["name"][L])}</a>' for i in genres) + "</div>" if genres else ""
            rows += (f'<tr data-tier="{k}" data-name="{e(name.lower())}" data-t="{"SABC".index(k) + 1}" data-imp="{r[1]}" data-pop="{r[2]}" data-avg="{r[3]}">'
                     f'<td><span class="tb {k}">{k}</span></td><td><a href="{yt(name)}" target="_blank" rel="noopener">{e(name)}</a></td><td class="n">{r[1] or "–"}</td><td class="n">{r[2] or "–"}</td><td class="n">{r[3] or "–"}</td><td>{gl}</td></tr>')
    tiers = "".join(f'<div class="door"><span class="tb {k}">{k}</span><h3>{e(TIERS[k][L][0])}</h3><p>{e(TIERS[k][L][1])}</p></div>' for k in "SABC")
    tabs = f'<button aria-pressed="true" data-tier="all">{e(t["all"])}</button>' + "".join(f'<button aria-pressed="false" data-tier="{k}">{k} · {e(TIERS[k][L][0])}</button>' for k in "SABC")
    th = lambda k, label, cl="": f'<th class="{cl}"><button data-k="{k}" type="button">{e(label)}</button></th>'
    body = f"""<div class="wrap"><div class="page-head"><span class="mono">{count} {e(t['bandsN'])}</span><h1>{e(t['bandsH'])}</h1><p class="lead">{e(t['bandsP'])}</p></div>
<div class="grid3" style="margin:0 0 36px">{tiers}</div>
<div class="tabs" id="tierTabs">{tabs}</div>
<div class="filters"><input id="bandq" type="search" placeholder="{e(t['bandSearch'])}" aria-label="{e(t['bandSearch'])}"><span class="mono"><span id="bandcount"></span> {e(t['bandsN'])}</span></div>
<p class="mono" style="margin-bottom:10px">{e(t['sortHint'])}</p>
<div class="tbl-wrap"><table class="bands"><thead><tr>{th('t', 'Tier')}{th('name', t['band'])}{th('imp', t['imp'], 'n')}{th('pop', t['pop'], 'n')}{th('avg', t['avg'], 'n')}<th>{e(t['nav']['genres'])}</th></tr></thead><tbody id="bandsBody">{rows}</tbody></table></div><div style="height:60px"></div></div>"""
    pg.write(pg.p["bands"], PATHS["en" if L == "pt" else "pt"]["bands"], 0, t["bandsH"], t["bandsDesc"].format(n=count), body, "bands")


def page_about(pg):
    t, L = pg.t, pg.lang
    secs = "".join(f"<h2>{e(h)}</h2><p>{e(p)}</p>" for h, p in t["about"])
    pv = PRIVACY[L]
    secs += f'<section id="privacy" class="privacy"><h2>{e(pv["h"])}</h2><p class="lead">{e(pv["lead"])}</p>'
    secs += "".join(f"<h3>{e(h)}</h3><p>{e(p)}</p>" for h, p in pv["items"])
    secs += f'<p>{e(pv["contact"])} <a href="{PRIVACY["link"]}" target="_blank" rel="noopener">LinkedIn</a>.</p><p class="mono">{e(pv["updated"])}</p></section>'
    body = f"""<div class="wrap"><div class="page-head"><h1>{e(t['aboutH'])}</h1></div><div class="prose" style="padding-bottom:60px">{secs}</div></div>"""
    pg.write(pg.p["about"], PATHS["en" if L == "pt" else "pt"]["about"], 0, t["aboutH"], t["aboutDesc"], body, "about")


def data_js(lang):
    t = UI[lang]
    payload = dict(
        dir=PATHS[lang]["dir"], t=t["js"],
        clades=[dict(id=c) for c in CLADE_IDS], cladeColor={c: CLADES[c][2] for c in CLADE_IDS},
        genres=[dict(id=g["id"], name=g["name"][lang], short=SHORT.get(g["id"], g["name"][lang]), year=g["year"], clade=g["clade"], parents=g["parents"], children=g["children"],
                     place=g["place"][lang], blurb=g["text"][lang][1], genome=g["genome"], sound=g["sound"], artists=g["artists"]) for g in GENRES])
    payload["t"]["traits"] = t["traits"]
    payload["t"]["genome"] = t["genome"]
    js = "window.ROCK=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    js += "window.ROCK.base=(function(){var p=location.pathname,d=window.ROCK.dir;return p.indexOf('/'+d+'/')>=0?'../':'';})();\n"
    with open(os.path.join(ROOT, "assets", f"data-{lang}.js"), "w", encoding="utf8", newline="\n") as f:
        f.write(js)


def main():
    for d in ["generos", "en"]:
        shutil.rmtree(os.path.join(ROOT, d), ignore_errors=True)
    for lang in ("pt", "en"):
        pg = Page(lang)
        data_js(lang)
        page_home(pg); page_genres(pg); page_evo(pg); page_lab(pg); page_songs(pg); page_bands(pg); page_about(pg)
        for i, g in enumerate(ORDER):
            page_genre(pg, g, i)
    # 404, sitemap, robots
    notfound = open(os.path.join(HERE, "404.tpl"), encoding="utf8").read()
    open(os.path.join(ROOT, "404.html"), "w", encoding="utf8", newline="\n").write(notfound)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for u, pt, en in URLS:
        sm.append(f'<url><loc>{u}</loc><xhtml:link rel="alternate" hreflang="pt-BR" href="{pt}"/><xhtml:link rel="alternate" hreflang="en" href="{en}"/></url>')
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf8", newline="\n").write("\n".join(sm))
    open(os.path.join(ROOT, "robots.txt"), "w", newline="\n").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    open(os.path.join(ROOT, "CNAME"), "w", newline="\n").write("typesofrock.biblioverse.org\n")
    open(os.path.join(ROOT, ".gitignore"), "w", newline="\n").write("__pycache__/\n")
    print(len(GENRES), "gêneros;", len(URLS), "páginas;", TOTAL_ARTISTS, "artistas;", TOTAL_SONGS, "canções")


if __name__ == "__main__":
    main()
