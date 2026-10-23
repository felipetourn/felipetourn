#!/usr/bin/env python3
"""Builds assets/*.svg, README.md and preview.html from profile.json.

Usage: python3 scripts/build.py
The SVGs are self-contained (no JS, no external fonts or resources).
Colors are CSS variables (--main, --sec, --dim, --alert, --bg) at the top of each SVG.
"""
import colorsys
import json
import random
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
P = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
T = P["theme"]
W = 600                      # viewBox width for every SVG
FONT = 'ui-monospace,"Courier New",monospace'
CW = 0.6                     # monospace char width / font-size


def mix(hex_color, factor):
    """Darken a color by mixing it with black (factor 0..1 = how much color is kept)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % tuple(round(c * factor) for c in (r, g, b))


def adjust(hex_color, sat=1.0, light=1.0):
    """Scale a color's HSL saturation and lightness (1 = unchanged)."""
    h = hex_color.lstrip("#")
    hh, l, s = colorsys.rgb_to_hls(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
    r, g, b = colorsys.hls_to_rgb(hh, min(0.85, l * light), min(1.0, s * sat))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


# Theme colors with saturation and brightness applied.
SAT = T.get("saturate", 1)
LIGHT = T.get("brightness", 1)
C = {k: adjust(T[k], SAT, LIGHT) for k in ("main", "sec", "blue", "pink")}
C.update(alert=T["alert"], bg=T["bg"])
DIM = mix(C["main"], 0.5)


def x(s):
    return escape(str(s))


def wrap(text, width):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        while len(w) > width:            # word longer than the line
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(w[:width])
            w = w[width:]
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def head(h, title, extra_css=""):
    """Shared header: variables, type, glow, scanlines, CRT vignette."""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{x(title)}">
<title>{x(title)}</title>
<style>
svg{{--main:{C["main"]};--sec:{C["sec"]};--blue:{C["blue"]};--pink:{C["pink"]};--dim:{DIM};--alert:{C["alert"]};--bg:{C["bg"]}}}
text{{font-family:{FONT};white-space:pre}}
.m{{fill:var(--main)}}.s{{fill:var(--sec)}}.d{{fill:var(--dim)}}.a{{fill:var(--alert)}}.bg{{fill:var(--bg)}}
.p{{fill:var(--pink)}}.f{{fill:url(#fold)}}.fh{{fill:url(#barg)}}
.ms{{stroke:var(--main);fill:none}}.ds{{stroke:var(--dim);fill:none}}
.b{{font-weight:700}}
.c0{{stop-color:var(--blue)}}.c1{{stop-color:var(--main)}}.c2{{stop-color:var(--pink)}}
.g0{{stop-color:var(--main);stop-opacity:0}}.g1{{stop-color:var(--main);stop-opacity:.10}}
.crt{{animation:flicker 7s infinite}}
.band{{animation:roll 6s linear infinite}}
.blink{{animation:blink 1s step-end infinite}}
@keyframes flicker{{0%,100%{{opacity:1}}48%{{opacity:1}}49%{{opacity:.86}}50%{{opacity:1}}83%{{opacity:.94}}84%{{opacity:1}}}}
@keyframes roll{{from{{transform:translateY(-80px)}}to{{transform:translateY({h}px)}}}}
@keyframes blink{{50%{{opacity:0}}}}
{extra_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.band{{display:none}}.rm-show{{opacity:1!important}}}}
</style>
<defs>
<filter id="glow" x="-15%" y="-15%" width="130%" height="130%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#000" opacity=".15"/></pattern>
<radialGradient id="vig" cx="50%" cy="50%" r="75%"><stop offset="60%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".5"/></radialGradient>
<linearGradient id="fold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" class="c0"/><stop offset="1" class="c1"/></linearGradient>
<linearGradient id="barg" x1="150" x2="490" y1="0" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" class="c0"/><stop offset="1" class="c1"/></linearGradient>
<linearGradient id="bandg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" class="g0"/><stop offset=".5" class="g1"/><stop offset="1" class="g0"/></linearGradient>
</defs>
<rect class="bg" width="{W}" height="{h}"/>
'''


def tail(h):
    return f'''<rect class="band" width="{W}" height="80" fill="url(#bandg)"/>
<rect width="{W}" height="{h}" fill="url(#scan)"/>
<rect width="{W}" height="{h}" fill="url(#vig)"/>
</svg>
'''


def frame(h):
    """Outer frame with heavier corners."""
    c = 14
    s = f'<rect x="6.5" y="6.5" width="{W - 13}" height="{h - 13}" class="ds"/>\n'
    for (px, py, dx, dy) in ((6, 6, 1, 1), (W - 6, 6, -1, 1), (6, h - 6, 1, -1), (W - 6, h - 6, -1, -1)):
        s += f'<path d="M{px} {py + dy * c}V{py}H{px + dx * c}" class="ms" stroke-width="2"/>\n'
    return s


# ---------------------------------------------------------------- pixel font 5x7
GLYPHS = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "Ñ": "01101 10010 00000 11001 10101 10011 10001",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000", "-": "00000 00000 00000 11111 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100", "_": "00000 00000 00000 00000 00000 00000 11111",
    "!": "00100 00100 00100 00100 00100 00000 00100", "[": "01110 01000 01000 01000 01000 01000 01110",
    "]": "01110 00010 00010 00010 00010 00010 01110", "/": "00001 00010 00010 00100 01000 01000 10000",
    "?": "01110 10001 00001 00010 00100 00000 00100",
}
ACCENTS = str.maketrans("ÁÉÍÓÚÜÀÈÌÒÙ", "AEIOUUAEIOU")


def pixel_path(text, x0, y0, p):
    """Return a path with one square per lit pixel."""
    d = []
    for i, ch in enumerate(text):
        rows = GLYPHS.get(ch, GLYPHS["?"]).split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    px = x0 + (i * 6 + c) * p
                    py = y0 + r * p
                    d.append(f"M{px:g} {py:g}h{p - 1:g}v{p - 1:g}h-{p - 1:g}z")
    return "".join(d)


def name_cycle(words, top, left=None, hold=4.0, step=0.08, scramble=5, delay=2.9, avail=552, max_p=10):
    """Pixel-art title that cycles between words with a decode effect.

    Each state (word or scrambled frame) is a <path> in <defs>, shown only during
    its slice of the loop by its own CSS animation.
    With reduced motion the first word stays put. Centered unless `left` is given.
    """
    words = [w.upper().translate(ACCENTS) for w in words]
    p = max(3, min(max_p, int(avail / (max(map(len, words)) * 6 - 1))))
    rnd = random.Random(7)
    pool = "ABCDEFGHJKLMNPRSTUVXYZ0123456789"
    states = []                                # (text, duration, is_scramble)
    for i, w in enumerate(words):
        states.append((w, hold, False))
        if len(words) > 1:
            nxt = words[(i + 1) % len(words)]
            for k in range(1, scramble + 1):
                fixed = round(k * len(nxt) / (scramble + 1))       # chars already decoded
                ln = len(w) + round((len(nxt) - len(w)) * k / (scramble + 1))
                states.append((nxt[:fixed] + "".join(rnd.choice(pool) for _ in range(max(0, ln - fixed))),
                               step, True))
    total = sum(d for _, d, _ in states)
    defs, body, css, t0 = [], [], [], 0.0
    for j, (txt, d, mid) in enumerate(states):
        wpx = (len(txt) * 6 - 1) * p
        defs.append(f'<path id="n{j}" d="{pixel_path(txt, (W - wpx) / 2 if left is None else left, top, p)}"/>')
        cls = ""
        if len(states) > 1:
            a, b = t0 / total * 100, (t0 + d) / total * 100
            on = f"{a:.3f}%{{opacity:1}}" if a > 0 else ""
            css.append(f"@keyframes n{j}{{0%{{opacity:{0 if a > 0 else 1}}}{on}{b:.3f}%{{opacity:0}}}}"
                       f".n{j}{{opacity:0;animation:n{j} {total:.2f}s step-end {delay}s infinite}}")
            cls = f' class="n{j}{" rm-show" if j == 0 else ""}"'
        body.append(f'<g{cls}><use href="#n{j}" class="d" transform="translate(2 2)"/>'
                    f'<use href="#n{j}" class="{"p" if mid else "f"}" filter="url(#glow)"/></g>')
        t0 += d
    return "<defs>" + "".join(defs) + "</defs>" + "".join(body), "".join(css), 8 * p


# ---------------------------------------------------------------- flag
def flag(x0, y0, s, cols=14):
    """Argentine flag in pixel blocks, like the name.

    Each column bobs with a phase shift so it waves; the left edge moves least.
    Returns (markup, css).
    """
    amp = s * .25
    css = (".ac{fill:#75aadb}.aw{fill:#f4f4f4}.ay{fill:#f6b40e}"
           + "".join(f".w{t}{{animation:w{t} 1s ease-in-out infinite alternate}}"
                     f"@keyframes w{t}{{from{{transform:translateY(-{t * amp:.2f}px)}}"
                     f"to{{transform:translateY({t * amp:.2f}px)}}}}" for t in (1, 2, 3)))
    rows = ["ac"] * 3 + ["aw"] * 3 + ["ac"] * 3
    mid = cols // 2
    b = s - max(.5, s * .2)                          # block size, leaving a gap
    out = []
    for c in range(cols):
        cells = []
        for r, cls in enumerate(rows):
            if 3 <= r <= 5 and c in (mid - 1, mid):
                cls = "ay"                           # sun
            cells.append(f'<rect x="{x0 + c * s:.1f}" y="{y0 + r * s:.1f}" width="{b:.1f}" height="{b:.1f}" class="{cls}"/>')
        tier = 0 if c == 0 else 1 + 3 * c // (cols + 1)
        attr = f' class="w{tier}" style="animation-delay:-{c * .09:.2f}s"' if tier else ""
        out.append(f'<g{attr}>{"".join(cells)}</g>')
    return f'<g filter="url(#glow)">{"".join(out)}</g>', css


# ---------------------------------------------------------------- header.svg
def build_header():
    boot = [
        ("m", "> POWER ON SELF TEST ...... OK", 0.2),
        ("m", "> MEMORY CHECK ............ OK", 0.55),
        ("m", "> INITIALIZING PROFILE .... OK", 0.9),
        ("a", "! WARNING: OUTPUT CRITICAL", 1.25),
    ]
    fs = 14
    top, nh = 77, 70                                 # name: 7 rows of 10px blocks
    title, ncss, _ = name_cycle(P.get("title") or [P["name"]], top, left=22, delay=3, avail=380)
    fsz = nh / 9                                     # flag as tall as the name
    fl, fcss = flag(492 - 7 * fsz, top, fsz)
    y = top + nh + 60
    h = y + 44
    css = ncss + fcss + (
        ".cv{transform-box:fill-box;transform-origin:right;transform:scaleX(0)}"
        "@keyframes type{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
        ".boot{animation:out .5s linear 2.6s both}"
        "@keyframes out{0%{opacity:1}30%{opacity:.2}45%{opacity:.8}100%{opacity:0}}"
        ".name{animation:flick 1s linear 3s both}"
        "@keyframes flick{0%{opacity:0}15%{opacity:.9}20%{opacity:.1}40%{opacity:1}45%{opacity:.3}60%,100%{opacity:1}}"
        ".warn{animation:blink 1.1s step-end 1.6s infinite}"
        "@media (prefers-reduced-motion:reduce){.boot{display:none}}"
    )
    s = head(h, f"{P['name']} - {P['role']}", css)
    s += '<g class="crt">\n' + frame(h)
    # top bar
    s += (f'<text x="22" y="30" font-size="12" class="m b">SYS.PROFILE // TERMINAL 01</text>'
          f'<text x="{W - 22}" y="30" font-size="12" class="s" text-anchor="end">CH-01 <tspan class="blink">●</tspan> LIVE</text>'
          f'<path d="M14 40H{W - 14}" class="ds"/>\n')
    # boot sequence, typed out char by char, then cleared for the name
    s += '<g class="boot" filter="url(#glow)">\n'
    for i, (cls, line, t0) in enumerate(boot):
        by = 68 + i * 24
        wpx = len(line) * fs * CW + 4
        dur = len(line) * 0.012
        warn = ' warn' if cls == "a" else ''
        s += (f'<text x="22" y="{by}" font-size="{fs}" class="{cls}{warn}">{x(line)}</text>'
              f'<rect class="cv bg" x="20" y="{by - fs}" width="{wpx:.0f}" height="{fs + 6}" '
              f'style="animation:type {dur:.2f}s steps({len(line)}) {t0}s both"/>\n')
    s += '</g>\n'
    s += f'<g class="name">{title}</g>\n' + fl + '\n'
    s += f'<path d="M14 {y - 18}H{W - 14}" class="ds" stroke-dasharray="2 4"/>\n'
    role = wrap(P["role"], 60)[0]
    s += (f'<text x="22" y="{y}" font-size="14" class="s" filter="url(#glow)">'
          f'<tspan class="m">ROLE:</tspan> {x(role)}</text>\n')
    s += (f'<text x="22" y="{y + 24}" font-size="14" class="m" filter="url(#glow)">'
          f'guest@profile:~$ <tspan class="p blink">█</tspan></text>\n')
    s += '</g>\n'
    return s + tail(h)


# ---------------------------------------------------------------- system.svg
def build_system():
    fs, lh = 13, 20
    cols = int((W - 44) / (fs * CW))        # chars per line
    lead = 16                               # column where values start
    body, y = [], 34
    css = ""
    sec = 0

    def title(name):
        nonlocal y, sec
        sec += 1
        idx = sec
        y += 18
        label = f"[ {name} ]"
        tw = len(label) * fs * CW
        body.append(f'<text x="22" y="{y}" font-size="{fs}" class="m b" filter="url(#glow)">{x(label)}</text>'
                    f'<path d="M{22 + tw + 8:.0f} {y - 4}H{W - 44}" class="ds"/>'
                    f'<text x="{W - 22}" y="{y}" font-size="10" class="d" text-anchor="end">{idx:02d}</text>')
        y += 8

    def row(label, value):
        nonlocal y
        if not value:                       # skip empty fields
            return
        dots = "." * max(2, lead - len(label) - 1)
        lines = wrap(value, cols - lead - 1)
        for i, ln in enumerate(lines):
            y += lh
            pre = f'{x(label)} <tspan class="d">{dots}</tspan> ' if i == 0 else " " * (lead + 1)
            body.append(f'<text x="22" y="{y}" font-size="{fs}" class="m">{pre}'
                        f'<tspan class="s">{x(ln)}</tspan></text>')

    # top bar
    body.append(f'<text x="22" y="28" font-size="11" class="m b">DIAGNOSTIC PANEL // NODE 01</text>'
                f'<text x="{W - 22}" y="28" font-size="11" class="s" text-anchor="end">UPLINK <tspan class="blink">●</tspan> OK</text>'
                f'<path d="M14 38H{W - 14}" class="ds"/>')
    y = 40

    title("system")
    row("name", P["name"])
    row("role", P["role"])
    row("location", P["location"])
    y += 10

    title("dev")
    row("frontend", P["frontend"])
    row("backend", P["backend"])
    row("other", P["other"])
    if P["languages"]:
        # one boxed "module" per language, three per row, with a status LED
        css += ".led{animation:led 2.4s step-end infinite}@keyframes led{50%{opacity:.2}}"
        cw, ch, gap = (W - 44 - 2 * 12) / 3, 26, 12
        for n, lang in enumerate(P["languages"]):
            cx0 = 22 + (n % 3) * (cw + gap)
            if n % 3 == 0:
                y += ch + 10
            top = y - ch + 4
            body.append(f'<rect x="{cx0 + .5:.1f}" y="{top + .5}" width="{cw - 1:.1f}" height="{ch - 1}" class="ds"/>'
                        f'<path d="M{cx0:.1f} {top + 6}V{top}H{cx0 + 6:.1f}" class="ms" stroke-width="1.5"/>'
                        f'<rect x="{cx0 + 10:.1f}" y="{top + 10}" width="6" height="6" class="fh led" '
                        f'style="animation-delay:{-n * 0.4:.1f}s" filter="url(#glow)"/>'
                        f'<text x="{cx0 + 24:.1f}" y="{top + 17}" font-size="12" class="s">{x(lang[:14])}</text>'
                        f'<text x="{cx0 + cw - 8:.1f}" y="{top + 17}" font-size="9" class="d" text-anchor="end">MOD-{n + 1:02d}</text>')
    y += 10
    if P["projects"]:
        title("projects")
    for pr in P["projects"]:
        y += lh
        body.append(f'<text x="22" y="{y}" font-size="{fs}" class="m b">&gt; {x(pr["name"])}</text>')
        for ln in wrap(pr["desc"], cols - 4):
            y += lh - 2
            body.append(f'<text x="44" y="{y}" font-size="{fs}" class="s">{x(ln)}</text>')
    if P["projects"]:
        y += 10

    c = P["contact"]
    if any(c.values()):
        title("contact")
    row("mail", c["mail"])
    row("web", c["web"])
    row("linkedin", c["linkedin"])

    y += 30
    body.append(f'<path d="M14 {y - 16}H{W - 14}" class="ds"/>'
                f'<text x="22" y="{y}" font-size="11" class="d">END OF TRANSMISSION <tspan class="p blink">█</tspan></text>')
    h = y + 18
    return head(h, f"{P['name']} system panel", css) + '<g class="crt">\n' + frame(h) + \
        "\n".join(body) + "\n</g>\n" + tail(h)


# ---------------------------------------------------------------- divider.svg
def build_divider():
    h = 24
    css = (".sweep{animation:sweep 3.5s linear infinite}"
           f"@keyframes sweep{{from{{transform:translateX(-140px)}}to{{transform:translateX({W + 20}px)}}}}")
    ticks = "".join(f"M{i} {12 - (4 if i % 60 == 0 else 2)}v{8 if i % 60 == 0 else 4}" for i in range(20, W - 19, 20))
    s = head(h, "divider", css)
    s += (f'<path d="M8 12H{W - 8}" class="ds"/><path d="{ticks}" class="ds"/>'
          f'<path d="M4 6v12M{W - 4} 6v12" class="ms" stroke-width="2"/>'
          f'<linearGradient id="sw" x1="0" x2="1"><stop offset="0" class="g0"/>'
          f'<stop offset="1" class="c2"/></linearGradient>'
          f'<g class="sweep"><rect width="120" height="2" y="11" fill="url(#sw)" filter="url(#glow)"/>'
          f'<rect x="118" y="8" width="3" height="8" class="p" filter="url(#glow)"/></g>\n')
    # no rolling band on something this short
    return s + f'<rect width="{W}" height="{h}" fill="url(#scan)"/>\n</svg>\n'


# ---------------------------------------------------------------- project cards
def build_card(pr, i):
    fs = 13
    lines = wrap(pr["desc"], int((W - 170) / (fs * CW)))[:2]
    h = 44 + len(lines) * 18
    s = head(h, f"Project {pr['name']}: {pr['desc']}")
    s += frame(h)
    s += (f'<text x="22" y="30" font-size="15" class="m b" filter="url(#glow)">&gt; {x(pr["name"])}</text>'
          f'<text x="{W - 22}" y="20" font-size="9" class="d" text-anchor="end">PRJ-{i:02d}</text>')
    for k, ln in enumerate(lines):
        s += f'<text x="22" y="{52 + k * 18}" font-size="{fs}" class="s">{x(ln)}</text>'
    s += (f'<rect x="{W - 112}" y="{h / 2 - 7:.0f}" width="90" height="22" class="ms"/>'
          f'<text x="{W - 67}" y="{h / 2 + 9:.0f}" font-size="12" class="m b" text-anchor="middle">OPEN <tspan class="blink">▸</tspan></text>\n')
    return s + tail(h).replace('<rect class="band" width="600" height="80" fill="url(#bandg)"/>\n', "")


# ---------------------------------------------------------------- README + preview
def build_readme(cards):
    v = P.get("version", 1)
    q = f"?v={v}"
    c = P["contact"]
    alt_sys = ", ".join(v for v in (
        P["name"], P["role"], P["location"],
        "Languages: " + ", ".join(P["languages"]),
        P["frontend"] and f"Frontend: {P['frontend']}",
        P["backend"] and f"Backend: {P['backend']}",
        P["other"] and f"Other: {P['other']}") if v)
    div = f'<img src="assets/divider.svg{q}" width="100%" alt="">'
    out = [
        '<div align="center">',
        "",
        f'<img src="assets/header.svg{q}" width="100%" alt="{x(P["name"])} - {x(P["role"])}">',
        "",
        div,
        "",
        f'<img src="assets/system.svg{q}" width="100%" alt="{x(alt_sys)}">',
        "",
        div,
        "",
    ]
    for pr, f in zip(P["projects"], cards):
        out += [f'<a href="{x(pr["url"])}"><img src="assets/{f}{q}" width="100%" alt="{x(pr["name"])}: {x(pr["desc"])}"></a>', ""]
    links = []
    if c["mail"]:
        links.append(f'<a href="mailto:{x(c["mail"])}">mail</a>')
    if c["web"]:
        web = c["web"] if c["web"].startswith("http") else f"https://{c['web']}"
        links.append(f'<a href="{x(web)}">web</a>')
    if c["linkedin"]:
        li = c["linkedin"] if c["linkedin"].startswith("http") else f"https://www.linkedin.com/in/{c['linkedin']}"
        links.append(f'<a href="{x(li)}">linkedin</a>')
    if cards:
        out += [div, ""]
    if links:
        out += [" - ".join(links), ""]
    out += ["</div>", ""]
    return "\n".join(out)


def build_preview(cards):
    imgs = ['<img src="assets/header.svg" alt="">', '<img src="assets/divider.svg" alt="">',
            '<img src="assets/system.svg" alt="">', '<img src="assets/divider.svg" alt="">']
    imgs += [f'<img src="assets/{f}" alt="">' for f in cards]
    stack = "\n".join(imgs)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Profile preview</title>
<style>
body{{margin:0;background:#000;color:{C["main"]};font:13px ui-monospace,"Courier New",monospace;padding:16px}}
h2{{font-size:13px;font-weight:400;color:{C["sec"]};margin:24px 0 8px}}
.row{{display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start}}
.col{{display:flex;flex-direction:column;gap:6px}}
.col img{{width:100%;display:block}}
.light{{background:#fff;padding:12px;border-radius:6px}}
.m{{width:380px}}.d{{width:830px;max-width:100%}}
</style></head><body>
<h1 style="font-size:15px">PREVIEW // main {C["main"]}, sec {C["sec"]}, blue {C["blue"]}, pink {C["pink"]}, saturation ×{SAT}, brightness ×{LIGHT}</h1>
<div class="row">
<div><h2>MOBILE - 380px</h2><div class="col m">{stack}</div></div>
<div><h2>DESKTOP - 830px</h2><div class="col d">{stack}</div></div>
</div>
<h2>GITHUB LIGHT MODE (white background)</h2>
<div class="light d"><div class="col">{stack}</div></div>
</body></html>
'''


def main():
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for old in assets.glob("project-*.svg"):
        old.unlink()
    files = {"header.svg": build_header(), "system.svg": build_system(), "divider.svg": build_divider()}
    cards = []
    for i, pr in enumerate(P["projects"], 1):
        f = f"project-{i}.svg"
        files[f] = build_card(pr, i)
        cards.append(f)
    for f, s in files.items():
        (assets / f).write_text(s, encoding="utf-8")
        print(f"assets/{f:16} {len(s.encode()) / 1024:6.1f} KB")
    (ROOT / "README.md").write_text(build_readme(cards), encoding="utf-8")
    (ROOT / "preview.html").write_text(build_preview(cards), encoding="utf-8")
    print("README.md, preview.html")
    def strings(o):
        if isinstance(o, dict):
            o = list(o.values())
        if isinstance(o, list):
            return [s for v in o for s in strings(v)]
        return [o] if isinstance(o, str) else []
    left = sorted({m for v in strings(P) for m in re.findall(r"\[[^\]]+\]", v)})
    if left:
        print("\nUnfilled placeholders in profile.json:", ", ".join(left))


if __name__ == "__main__":
    main()
