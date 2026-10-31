"""Gera favicons e imagens de compartilhamento. Precisa do Pillow: python tools/icons.py"""
import json, math, os, re, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import genres_1, genres_2, genres_3, genres_4
from genres_3 import CLADES

SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#f6f0e4"/><path d="M32 3C44 3 55 6 59 14C62 21 56 33 48 45C42 54 37 61 32 61C27 61 22 54 16 45C8 33 2 21 5 14C9 6 20 3 32 3Z" fill="#17161a"/></svg>'
open(os.path.join(ROOT, "favicon.svg"), "w", newline="\n").write(SVG)

PICK = "M32 3C44 3 55 6 59 14C62 21 56 33 48 45C42 54 37 61 32 61C27 61 22 54 16 45C8 33 2 21 5 14C9 6 20 3 32 3Z"


def path_points(d):
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", d.replace("V", " V ").replace("L", " L "))]
    pts, cur, out = [], None, []
    for cmd, args in re.findall(r"([MCLHV])([^MCLHVZ]*)", d):
        v = [float(x) for x in re.findall(r"-?\d+\.?\d*", args)]
        if cmd in "ML":
            cur = (v[0], v[1]); out.append(cur)
        elif cmd == "V":
            cur = (cur[0], v[0]); out.append(cur)
        elif cmd == "C":
            for j in range(0, len(v), 6):
                p0, p1, p2, p3 = cur, (v[j], v[j + 1]), (v[j + 2], v[j + 3]), (v[j + 4], v[j + 5])
                for n in range(1, 17):
                    t = n / 16
                    u = 1 - t
                    out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0], u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
                cur = p3
    return out


def icon(s):
    k = 4
    im = Image.new("RGB", (s * k, s * k), "#f6f0e4")
    d = ImageDraw.Draw(im)
    u = s * k / 64
    d.polygon([(x * u, y * u) for x, y in path_points(PICK)], fill="#17161a")
    return im.resize((s, s), Image.LANCZOS)


icon(180).save(os.path.join(ROOT, "apple-touch-icon.png"))
icon(192).save(os.path.join(ROOT, "icon-192.png"))
icon(512).save(os.path.join(ROOT, "icon-512.png"))
icon(32).save(os.path.join(ROOT, "favicon.ico"), sizes=[(32, 32)])
json.dump({"name": "Types of Rock", "short_name": "Types of Rock", "start_url": "/", "display": "standalone", "background_color": "#f6f0e4", "theme_color": "#f6f0e4",
           "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(os.path.join(ROOT, "site.webmanifest"), "w"), ensure_ascii=False)

GENRES = genres_1.GENRES + genres_2.GENRES + genres_3.GENRES + genres_4.GENRES
BY = {g["id"]: g for g in GENRES}
for gid, extra in genres_4.ADD_PARENTS.items():
    BY[gid]["parents"] += extra
INK, BEIGE, PAPER = "#17161a", "#f6f0e4", "#fffdf7"
DISPLAY = os.path.join(HERE, "fonts", "GermaniaOne.ttf")
BODYF = os.path.join(HERE, "fonts", "GoogleSans.ttf")
K = 2


def rad(y):
    return 80 + (max(y, 1900) - 1900) * 1.5 if y <= 1950 else 154 + (min(y, 2026) - 1950) ** .88 * 8.3


def mix(col, f):
    return tuple(int(int(col[j:j + 2], 16) * f + int(BEIGE[j:j + 2], 16) * (1 - f)) for j in (1, 3, 5))


def pick(d, x, y, h, col):
    u = h / 64
    d.polygon([(x + a * u, y + b * u) for a, b in path_points(PICK)], fill=col)


def tree(d, cx, cy, s):
    order = list(CLADES)
    lst = sorted(GENRES, key=lambda g: (order.index(g["clade"]), g["year"]))
    rest = [g for g in lst if g["clade"] != "raizes"]
    roots = [g for g in lst if g["clade"] == "raizes"]
    gap, a, last, pos = .05, -math.pi / 2, None, {}
    unit = (2 * math.pi - gap * (len(order) - 1)) / len(rest)
    for g in rest:
        if last and last != g["clade"]:
            a += gap
        last = g["clade"]
        a += unit
        pos[g["id"]] = a
    for n, g in enumerate(roots):
        pos[g["id"]] = -math.pi / 2 + .5 + n * 2 * math.pi / len(roots)
    P = lambda r, a: (cx + s * r * math.cos(a), cy + s * r * math.sin(a))
    for y in (1950, 1970, 1990, 2010, 2026):
        r = rad(y) * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#dcd0ba", width=K)
    for g in GENRES:
        for n, pid in enumerate(g["parents"]):
            a0, r0, a1, r1 = pos[pid], rad(BY[pid]["year"]), pos[g["id"]], rad(g["year"])
            m = (r0 + r1) / 2
            p0, c0, c1, p1 = P(r0, a0), P(m, a0), P(m, a1), P(r1, a1)
            pts = []
            for q in range(25):
                t = q / 24
                u = 1 - t
                pts.append(tuple(u ** 3 * p0[j] + 3 * u * u * t * c0[j] + 3 * u * t * t * c1[j] + t ** 3 * p1[j] for j in (0, 1)))
            d.line(pts, fill=mix(CLADES[g["clade"]][2], .8 if n == 0 else .35), width=(2 if n == 0 else 1) * K)
    for g in GENRES:
        x, y = P(rad(g["year"]), pos[g["id"]])
        q = (3.5 + sum(g["id"] in c["parents"] for c in GENRES) * .6) * K
        d.ellipse([x - q, y - q, x + q, y + q], fill=CLADES[g["clade"]][2], outline=BEIGE, width=K)


def save(im, path, colors=64):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = im.resize((1200, 630), Image.LANCZOS)
    if colors:
        im = im.quantize(colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(path, optimize=True)


def og(site, tagline, stats, path):
    W, H = 1200 * K, 630 * K
    im = Image.new("RGB", (W, H), BEIGE)
    d = ImageDraw.Draw(im)
    tree(d, 840 * K, 315 * K, .56 * K)
    d.rectangle([0, 0, 480 * K, H], fill=INK)
    pick(d, 56 * K, 58 * K, 92 * K, BEIGE)
    y = 190 * K
    for line in site:
        d.text((56 * K, y), line.upper(), font=ImageFont.truetype(DISPLAY, 96 * K), fill=BEIGE)
        y += 100 * K
    y += 18 * K
    f = ImageFont.truetype(BODYF, 29 * K)
    for line in tagline:
        d.text((56 * K, y), line, font=f, fill=BEIGE)
        y += 40 * K
    d.text((56 * K, 556 * K), stats, font=ImageFont.truetype(BODYF, 21 * K), fill="#cfcabe")
    save(im, path, None)


def wrap(d, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def og_genre(g, lang, site, traits, path):
    W, H = 1200 * K, 630 * K
    col = CLADES[g["clade"]][2]
    im = Image.new("RGB", (W, H), BEIGE)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 92 * K], fill=INK)
    pick(d, 56 * K, 22 * K, 48 * K, BEIGE)
    d.text((116 * K, 22 * K), site.upper(), font=ImageFont.truetype(DISPLAY, 44 * K), fill=BEIGE)
    size = 118
    while True:
        font = ImageFont.truetype(DISPLAY, size * K)
        lines = wrap(d, g["name"][lang], font, 610 * K)
        if len(lines) * size * 1.08 <= 300 or size <= 56:
            break
        size -= 6
    y = 150 * K
    for line in lines:
        d.text((56 * K, y), line, font=font, fill=INK)
        y += int(size * 1.08) * K
    meta = ImageFont.truetype(BODYF, 28 * K)
    d.text((56 * K, y + 16 * K), f'{g["year"]} · {g["place"][lang]}', font=meta, fill="#47454b")
    d.text((56 * K, 552 * K), CLADES[g["clade"]][0 if lang == "pt" else 1], font=ImageFont.truetype(DISPLAY, 34 * K), fill=INK)
    cx, cy, r = 945 * K, 365 * K, 168 * K
    pt = lambda v, i: (cx + r * v / 10 * math.cos(-math.pi / 2 + i * math.pi / 4), cy + r * v / 10 * math.sin(-math.pi / 2 + i * math.pi / 4))
    for lv in (2.5, 5, 7.5, 10):
        d.polygon([pt(lv, i) for i in range(8)], outline="#cfc3ab", width=K)
    d.polygon([pt(v, i) for i, v in enumerate(g["genome"])], fill=mix(col, .45), outline=col, width=3 * K)
    lf = ImageFont.truetype(BODYF, 19 * K)
    for i, name in enumerate(traits):
        x, y2 = pt(10.9, i)
        c = math.cos(-math.pi / 2 + i * math.pi / 4)
        d.text((x, y2), name, font=lf, fill="#47454b", anchor="lm" if c > .3 else "rm" if c < -.3 else "mm")
    save(im, path)


sys.path.insert(0, HERE)
from content import TRAITS_PT, TRAITS_EN
songs = sum(len(v) for v in json.load(open(os.path.join(HERE, "lists.json"), encoding="utf8"))["decades"].values())
og(["Tipos", "de Rock"], ["A árvore evolutiva do rock"], f"{len(GENRES)} gêneros · {songs} músicas", os.path.join(ROOT, "og-image.png"))
og(["Types", "of Rock"], ["The evolutionary tree of rock"], f"{len(GENRES)} genres · {songs} songs", os.path.join(ROOT, "og-image-en.png"))
for g in GENRES:
    og_genre(g, "pt", "Tipos de Rock", TRAITS_PT, os.path.join(ROOT, "og", "pt", g["id"] + ".png"))
    og_genre(g, "en", "Types of Rock", TRAITS_EN, os.path.join(ROOT, "og", "en", g["id"] + ".png"))
