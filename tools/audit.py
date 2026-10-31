"""Confere links internos, referências proibidas e texto em português em /en/. Rode: python tools/audit.py"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bad = 0
PT = re.compile(r"\b(Gêneros|Músicas|Bandas|Sobre|Contexto|Sonoridade|Laboratório|Filhos|Pais)\b")
for d, _, fs in os.walk(ROOT):
    if "tools" in d or ".git" in d:
        continue
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(d, f)
        s = open(p, encoding="utf8").read()
        if "assuper" + "listas" in s.lower():
            print("CITA FONTE", p); bad += 1
        for h in re.findall(r'(?:href|src)="([^"#]+)', s):
            if re.match(r"https?:|mailto:|//", h) or f == "404.html":
                continue
            t = os.path.normpath(os.path.join(d, h))
            if not os.path.exists(t):
                print("LINK", os.path.relpath(p, ROOT), h); bad += 1
        if os.path.relpath(p, ROOT).startswith("en"):
            body = re.sub(r'<a class="lang".*?</a>', "", s.split("<main", 1)[1]) if "<main" in s else ""
            m = PT.search(re.sub(r"<[^>]+>", " ", s.split("<body", 1)[1]))
            if m:
                print("PT EM /en/", os.path.relpath(p, ROOT), m.group(0)); bad += 1
print("problemas:", bad)
