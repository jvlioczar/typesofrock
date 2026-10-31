"""Confere links internos, referências proibidas e texto em português em /en/. Rode: python tools/audit.py"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
SEEN = set()
PT = re.compile(r"\b(Gêneros|Músicas|Bandas|Sobre|Contexto|Sonoridade|Laboratório|Filhos|Pais)\b")
for d, _, fs in os.walk(ROOT):
    if "tools" in d or ".git" in d:
        continue
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(d, f)
        s = open(p, encoding="utf8").read()
        if f != "404.html":
            for tag, rx in [("title", r"<title>(.*?)</title>"), ("description", r'<meta name="description" content="([^"]*)"')]:
                m = re.search(rx, s)
                v = m.group(1) if m else ""
                if not v or (tag, v) in SEEN:
                    print("SEO", tag, "vazio ou repetido", os.path.relpath(p, ROOT)); bad += 1
                SEEN.add((tag, v))
                if len(v) > 175 and tag == "description":
                    print("SEO longa", len(v), os.path.relpath(p, ROOT))
            if s.count("<h1") != 1:
                print("SEO h1", os.path.relpath(p, ROOT)); bad += 1
            m = re.search(r'property="og:image" content="https://typesofrock\.biblioverse\.org/([^"]+)"', s)
            if not m or not os.path.exists(os.path.join(ROOT, m.group(1))):
                print("SEO imagem", os.path.relpath(p, ROOT)); bad += 1
        if "assuper" + "listas" in s.lower():
            print("CITA FONTE", p); bad += 1
        for h in re.findall(r'(?:href|src)="([^"#]+)', s):
            if re.match(r"https?:|mailto:|//", h) or f == "404.html":
                continue
            t = os.path.normpath(os.path.join(d, h))
            if not os.path.exists(t):
                print("LINK", os.path.relpath(p, ROOT), h); bad += 1
        if not os.path.relpath(p, ROOT).startswith("pt") and f != "404.html":
            body = re.sub(r'<a class="lang".*?</a>', "", s.split("<main", 1)[1]) if "<main" in s else ""
            m = PT.search(re.sub(r"<[^>]+>", " ", s.split("<body", 1)[1]))
            if m:
                print("PT NA VERSAO EN", os.path.relpath(p, ROOT), m.group(0)); bad += 1
print("problemas:", bad)
