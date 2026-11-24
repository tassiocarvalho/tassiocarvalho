"""Gera os SVGs do perfil (cabeçalho, cartão neofetch e cartões de projeto).

Roda localmente ou no GitHub Actions. Usa só a biblioteca padrão.
Se GITHUB_TOKEN existir, usa para ter limite maior na API do GitHub.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

USER = "tassiocarvalho"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"
SANS = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"

BG, BORDER, GRID = "#0d1117", "#30363d", "#161b22"
FG, MUTED = "#e6edf3", "#8b949e"
GREEN, BLUE, PURPLE, ORANGE, RED = "#3fb950", "#58a6ff", "#d2a8ff", "#ffa657", "#ff7b72"


# ---------------------------------------------------------------- GitHub API
def api(path, accept="application/vnd.github+json"):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "profile-readme-builder")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def stats():
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    try:
        commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]
    except Exception:
        commits = None
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    years = (datetime.now(timezone.utc) - created).days / 365.25
    return {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in repos if not r["fork"]),
        "commits": commits,
        "years": years,
        "by_name": {r["name"]: r for r in repos},
    }


# ---------------------------------------------------------------- helpers
def frame(w, h, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<defs>
  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
    <path d="M20 0H0V20" fill="none" stroke="{GRID}" stroke-width="1"/>
  </pattern>
</defs>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12" fill="url(#grid)" opacity="0.9"/>
<circle cx="22" cy="20" r="5.5" fill="{RED}"/><circle cx="40" cy="20" r="5.5" fill="#e3b341"/><circle cx="58" cy="20" r="5.5" fill="{GREEN}"/>
<text x="{w/2}" y="24" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(title)}</text>
{body}
</svg>
"""


def write(name, svg):
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print("ok", name)


# ---------------------------------------------------------------- cabeçalho
def bus(y, color, values, seg=170, slant=7, half=11):
    """Barramento de analisador lógico rolando para a esquerda, em loop."""
    shapes = []
    period = seg * len(values)
    for copy in range(3):
        for i, v in enumerate(values):
            x = 180 + copy * period + i * seg
            pts = (f"{x},{y} {x+slant},{y-half} {x+seg-slant},{y-half} {x+seg},{y} "
                   f"{x+seg-slant},{y+half} {x+slant},{y+half}")
            shapes.append(f'<polygon points="{pts}" fill="{color}" fill-opacity="0.13" stroke="{color}" stroke-width="1.6"/>')
            shapes.append(f'<text x="{x+seg/2}" y="{y+4.5}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{color}">{escape(v)}</text>')
    dur = period / 32  # ~32 px/s
    return (f'<g clip-path="url(#plot)"><g>{"".join(shapes)}'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{period} 0" dur="{dur:.2f}s" repeatCount="indefinite"/>'
            f'</g></g>')


def clock(y, color, period=40, high=11):
    pts, x = [], 180
    while x < 180 + 900:
        pts += [f"{x},{y+high}", f"{x},{y-high}", f"{x+period/2},{y-high}", f"{x+period/2},{y+high}"]
        x += period
    return (f'<g clip-path="url(#plot)"><polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.8">'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{period} 0" dur="{period/32:.2f}s" repeatCount="indefinite"/>'
            f'</polyline></g>')


def header():
    w, h = 1000, 330
    sub = "Engenheiro de Computação · do transistor à API"
    rows = [
        ("clk", GREEN, None),
        ("backend[7:0]", BLUE, ["Node.js", "TypeScript", "NestJS", "PostgreSQL", "Docker", "AWS EC2"]),
        ("rtl[7:0]", PURPLE, ["Verilog", "FSM Moore", "CDC", "Cadence Genus", "SKY130", "4,56 µW"]),
        ("firmware[7:0]", ORANGE, ["ESP32", "C++", "UART", "MQTT", "PWM", "HX711"]),
    ]
    body = [f'<defs><clipPath id="plot"><rect x="180" y="170" width="790" height="150"/></clipPath>'
            f'<clipPath id="type"><rect x="40" y="108" width="0" height="34">'
            f'<animate attributeName="width" dur="2.6s" begin="0.4s" fill="freeze" calcMode="discrete" '
            f'values="{";".join(str(round(530*i/len(sub))) for i in range(len(sub)+1))}"/></rect></clipPath></defs>']
    body.append(f'<text x="40" y="92" font-family="{SANS}" font-size="46" font-weight="700" fill="{FG}">Tássio Carvalho</text>')
    body.append(f'<text x="40" y="132" clip-path="url(#type)" font-family="{MONO}" font-size="19" fill="{GREEN}">{escape(sub)}</text>')
    cursor_x = ";".join(str(round(40 + 2 + 530 * i / len(sub))) for i in range(len(sub) + 1))
    body.append(f'<rect x="40" y="116" width="10" height="20" fill="{GREEN}"><animate attributeName="x" values="{cursor_x}" calcMode="discrete" dur="2.6s" begin="0.4s" fill="freeze"/>'
                f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>')
    body.append(f'<text x="{w-40}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">trigger: curiosidade ↑</text>')
    body.append(f'<text x="{w-40}" y="78" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">sample rate: 1 commit/dia</text>')
    body.append(f'<line x1="40" y1="158" x2="{w-30}" y2="158" stroke="{BORDER}"/>')
    for i, (label, color, values) in enumerate(rows):
        y = 190 + i * 36
        body.append(f'<text x="40" y="{y+5}" font-family="{MONO}" font-size="14" fill="{color}">{label}</text>')
        body.append(clock(y, color) if values is None else bus(y, color, values))
    # cursor T0
    body.append(f'<line x1="640" y1="166" x2="640" y2="318" stroke="{RED}" stroke-width="1.2" stroke-dasharray="4 4"/>')
    body.append(f'<rect x="626" y="162" width="28" height="15" rx="3" fill="{RED}"/>'
                f'<text x="640" y="173" text-anchor="middle" font-family="{MONO}" font-size="11" font-weight="700" fill="{BG}">T0</text>')
    write("header.svg", frame(w, h, "logic-analyzer — tassio.vcd", "\n".join(body)))


# ---------------------------------------------------------------- neofetch
def chip(cx, cy, size=176, pins=8, pitch=18, pin_len=16, pin_w=8):
    """Chip QFP desenhado com formas SVG (não depende de fonte); pinos acendem em sequência."""
    half = size / 2
    x0, y0 = cx - half, cy - half
    out = []
    start = -(pins - 1) * pitch / 2
    n = 0
    for side in ("top", "right", "bottom", "left"):
        for i in range(pins):
            off = start + i * pitch
            if side == "top":
                x, y, w, h = cx + off - pin_w / 2, y0 - pin_len, pin_w, pin_len
            elif side == "bottom":
                x, y, w, h = cx - off - pin_w / 2, y0 + size, pin_w, pin_len
            elif side == "right":
                x, y, w, h = x0 + size, cy + off - pin_w / 2, pin_len, pin_w
            else:
                x, y, w, h = x0 - pin_len, cy - off - pin_w / 2, pin_len, pin_w
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="1.5" fill="{GREEN}" opacity="0.35">'
                       f'<animate attributeName="opacity" values="1;0.35;0.35" keyTimes="0;0.13;1" dur="3.84s" begin="{n*0.12:.2f}s" repeatCount="indefinite"/></rect>')
            n += 1
    out.append(f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" rx="10" fill="{GRID}" stroke="{GREEN}" stroke-width="2"/>')
    out.append(f'<rect x="{x0+30}" y="{y0+30}" width="{size-60}" height="{size-60}" rx="4" fill="none" stroke="{GREEN}" stroke-opacity="0.6" stroke-dasharray="4 3"/>')
    out.append(f'<circle cx="{x0+16}" cy="{y0+size-16}" r="5" fill="{GREEN}"/>')
    for dy, txt, fsz, wgt in ((-14, "TCR", 22, 700), (10, "UEFS", 14, 400), (28, "ECOMP", 14, 400)):
        out.append(f'<text x="{cx}" y="{cy+dy}" text-anchor="middle" font-family="{MONO}" font-size="{fsz}" font-weight="{wgt}" fill="{GREEN}">{txt}</text>')
    out.append(f'<text x="{cx}" y="{y0+size-12}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">2025</text>')
    return "\n".join(out)


def neofetch(s):
    w, lh, fs = 1000, 22, 14.5
    commits = f"{s['commits']:,}".replace(",", ".") if s["commits"] is not None else "—"
    info = [
        ("title", "tassio@github"),
        ("rule", ""),
        ("OS", "Engenharia de Computação · UEFS (2025)"),
        ("Host", "Bahia, Brasil"),
        ("Uptime", f"{s['years']:.1f} anos no GitHub"),
        ("Kernel", "Back-end · Node.js / TypeScript / NestJS"),
        ("Packages", f"{s['repos']} repositórios públicos"),
        ("Shell", "Bash · PowerShell"),
        ("Langs", "TypeScript · JavaScript · Python · C/C++"),
        ("Data", "PostgreSQL · MySQL · SQL Server"),
        ("HDL", "Verilog · SystemVerilog · UVM · Cadence Genus/Xcelium"),
        ("Embedded", "ESP32 · ESP8266 · Arduino · Raspberry Pi"),
        ("Cloud", "AWS EC2 · Docker · GitHub Actions"),
        ("Idiomas", "Português (nativo) · Inglês (intermediário)"),
        ("blank", ""),
        ("section", "GitHub Stats"),
        ("rule", ""),
        ("stats", f"Repos {s['repos']}  ·  Stars {s['stars']}  ·  Commits {commits}  ·  Followers {s['followers']}"),
    ]
    h = 70 + len(info) * lh + 40
    body = []
    body.append(chip(185, 70 - 15 + len(info) * lh / 2))
    x = 380
    for i, (k, v) in enumerate(info):
        y = 70 + i * lh
        if k == "title":
            body.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs+1}" font-weight="700"><tspan fill="{GREEN}">tassio</tspan><tspan fill="{FG}">@</tspan><tspan fill="{GREEN}">github</tspan></text>')
        elif k == "rule":
            body.append(f'<line x1="{x}" y1="{y-5}" x2="{w-40}" y2="{y-5}" stroke="{BORDER}" stroke-dasharray="3 3"/>')
        elif k == "section":
            body.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" font-weight="700" fill="{GREEN}">— {escape(v)} —</text>')
        elif k == "stats":
            body.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{FG}">{escape(v)}</text>')
        elif k != "blank":
            body.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}"><tspan fill="{ORANGE}" font-weight="700">{escape(k)}</tspan><tspan fill="{MUTED}">: </tspan><tspan fill="{FG}">{escape(v)}</tspan></text>')
    # paleta estilo neofetch
    for i, c in enumerate([RED, ORANGE, "#e3b341", GREEN, BLUE, PURPLE, "#f778ba", FG]):
        body.append(f'<rect x="{x + i*30}" y="{h-42}" width="26" height="14" rx="2" fill="{c}"/>')
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    body.append(f'<text x="{w-40}" y="{h-30}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">atualizado em {today}</text>')
    write("about.svg", frame(w, h, "tassio@github: ~ $ neofetch", "\n".join(body)))


# ---------------------------------------------------------------- cartões de projeto
LANG_COLOR = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
              "C++": "#f34b7d", "Verilog": "#b2b7f8", "MATLAB": "#e16737"}

PROJECTS = [
    ("sualojaaqui", "SuaLojaAqui", "em produção",
     "Frente de caixa (PDV) + estoque + financeiro, white-label. NestJS, Prisma e PostgreSQL; React PWA offline-first e Electron. 79 testes automatizados. Em uso num mercado."),
    ("zap-lingua", "Zap Língua", "WhatsApp",
     "Tutor de inglês no WhatsApp com voz, pronúncia, role play, repetição espaçada (SM2), XP e medalhas. Node.js 22, TypeScript strict, SQLite e Gemini API."),
    ("ECG_Projeto_v2", "ECG RTL v2", "Verilog · Cadence",
     "Processador RTL que detecta extrassístoles ventriculares no ECG. Golden model bit-exato em Python, Se 0,89 no MIT-BIH, 4,56 µW estimados em SKY130."),
    ("Software-para-projeto-de-filtros-FIR-seletivos-em-frequencia", "Filtros FIR", "DSP",
     "Projeto de filtros FIR por janelamento (Hamming, Kaiser, Blackman...) com visualização da resposta em frequência e validação em áudio. NumPy, SciPy e Tkinter."),
]


def wrap(text, width):
    lines, cur = [], ""
    for word in text.split():
        if len(cur) + len(word) + (1 if cur else 0) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}" if cur else word
    return lines + [cur] if cur else lines


def card(slug, name, tag, desc, repo):
    w, h = 480, 190
    lang = (repo or {}).get("language") or "—"
    stars = (repo or {}).get("stargazers_count", 0)
    body = [f'<text x="24" y="62" font-family="{SANS}" font-size="20" font-weight="700" fill="{BLUE}">{escape(name)}</text>']
    tw = len(tag) * 7.4 + 18
    body.append(f'<rect x="{w-24-tw}" y="45" width="{tw}" height="22" rx="11" fill="none" stroke="{GREEN}"/>'
                f'<text x="{w-24-tw/2}" y="60" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{GREEN}">{escape(tag)}</text>')
    for i, line in enumerate(wrap(desc, 56)[:4]):
        body.append(f'<text x="24" y="{92 + i*19}" font-family="{SANS}" font-size="13.5" fill="{FG}">{escape(line)}</text>')
    body.append(f'<circle cx="30" cy="{h-22}" r="6" fill="{LANG_COLOR.get(lang, MUTED)}"/>'
                f'<text x="42" y="{h-17}" font-family="{SANS}" font-size="13" fill="{MUTED}">{escape(lang)}</text>'
                f'<text x="160" y="{h-17}" font-family="{SANS}" font-size="13" fill="{MUTED}">★ {stars}</text>')
    title = f"{USER}/{slug}"
    title = title if len(title) <= 44 else title[:43] + "…"
    write(f"card-{slug.split('-')[0].lower()}.svg", frame(w, h, title, "\n".join(body)))


def main():
    s = stats()
    header()
    neofetch(s)
    for slug, name, tag, desc in PROJECTS:
        card(slug, name, tag, desc, s["by_name"].get(slug))


if __name__ == "__main__":
    main()
