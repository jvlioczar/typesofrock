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
json.dump({"name": "Tipos de Rock", "short_name": "Tipos de Rock", "start_url": "/", "display": "standalone", "background_color": "#f6f0e4", "theme_color": "#f6f0e4",
           "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
          open(os.path.join(ROOT, "site.webmanifest"), "w"), ensure_ascii=False)

GENRES = genres_1.GENRES + genres_2.GENRES + genres_3.GENRES + genres_4.GENRES
BY = {g["id"]: g for g in GENRES}
for gid, extra in genres_4.ADD_PARENTS.items():
    BY[gid]["parents"] += extra


def rad(y):
    return 54 + (max(y, 1900) - 1900) * 2 if y <= 1950 else 154 + (min(y, 2026) - 1950) ** .88 * 8.3


def og(title, sub, path):
    k = 2
    W, H = 1200 * k, 630 * k
    im = Image.new("RGB", (W, H), "#f6f0e4")
    d = ImageDraw.Draw(im)
    order = list(CLADES)
    lst = sorted(GENRES, key=lambda g: (order.index(g["clade"]), g["year"]))
    pos, a, last = {}, -math.pi / 2, None
    gap = .05
    unit = (2 * math.pi - gap * len(order)) / len(lst)
    cx, cy, s = 860 * k, 315 * k, .56 * k
    for g in lst:
        if last and last != g["clade"]:
            a += gap
        last = g["clade"]
        a += unit
        r = rad(g["year"])
        pos[g["id"]] = (cx + s * r * math.cos(a), cy + s * r * math.sin(a), a, r)
    for g in GENRES:
        col = CLADES[g["clade"]][2]
        for i, p in enumerate(g["parents"]):
            x0, y0, a0, r0 = pos[p]
            x1, y1, a1, r1 = pos[g["id"]]
            m = (r0 + r1) / 2
            c0, c1 = (cx + s * m * math.cos(a0), cy + s * m * math.sin(a0)), (cx + s * m * math.cos(a1), cy + s * m * math.sin(a1))
            pts = []
            for n in range(25):
                t = n / 24
                u = 1 - t
                pts.append((u ** 3 * x0 + 3 * u * u * t * c0[0] + 3 * u * t * t * c1[0] + t ** 3 * x1, u ** 3 * y0 + 3 * u * u * t * c0[1] + 3 * u * t * t * c1[1] + t ** 3 * y1))
            fade = tuple(int(int(col[j:j + 2], 16) * (.7 if i == 0 else .35) + 240 * (1 - (.7 if i == 0 else .35))) for j in (1, 3, 5))
            d.line(pts, fill=fade, width=(3 if i == 0 else 2) * k // 2 + 1)
    for g in GENRES:
        x, y, *_ = pos[g["id"]]
        q = (5 + len([c for c in GENRES if g["id"] in c["parents"]]) * .8) * k * .75
        d.ellipse([x - q, y - q, x + q, y + q], fill=CLADES[g["clade"]][2], outline="#f6f0e4", width=2 * k)
    d.rectangle([0, 0, 500 * k, H], fill=None)
    font = None
    for f in ["C:/Windows/Fonts/ariblk.ttf", "C:/Windows/Fonts/arialbd.ttf"]:
        if os.path.exists(f):
            font = f
            break
    big = ImageFont.truetype(font, 72 * k)
    small = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30 * k)
    y = 215 * k
    for line in title:
        d.text((60 * k, y), line, font=big, fill="#17161a")
        y += 90 * k
    y += 12 * k
    for line in sub:
        d.text((60 * k, y), line, font=small, fill="#c93a12")
        y += 40 * k
    im.resize((1200, 630), Image.LANCZOS).save(path)


og(["Tipos", "de Rock"], ["A árvore evolutiva do rock"], os.path.join(ROOT, "og-image.png"))
og(["Types", "of Rock"], ["The evolutionary tree of rock"], os.path.join(ROOT, "og-image-en.png"))
