#!/usr/bin/env python3
"""Generate fig_architecture.drawio for the Skill-Issue PCAP paper.
Style: big rounded numbered panels, grey cards, white
inner cards, black code panels, black pill labels on dashed connectors, flat icons.
All icons are hand-drawn SVG (no third-party icon licences)."""
import base64
from xml.sax.saxutils import escape

FONT = "Liberation Sans"
MONO = "DejaVu Sans Mono"
cells = []
_id = [10]


def nid():
    _id[0] += 1
    return f"c{_id[0]}"


def attr(s):
    return escape(s, {'"': "&quot;"})


def box(x, y, w, h, style, value=""):
    cells.append(
        f'<mxCell id="{nid()}" value="{attr(value)}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def text(x, y, w, h, value, size=18, align="center", bold=False, valign="middle", font=FONT):
    st = (f"text;html=1;whiteSpace=wrap;align={align};verticalAlign={valign};fontFamily={font};"
          f"fontSize={size};fontColor=#111111;strokeColor=none;fillColor=none;"
          f"{'fontStyle=1;' if bold else ''}spacing=0;")
    box(x, y, w, h, st, value)


def svg_icon(svg):
    return "data:image/svg+xml," + base64.b64encode(svg.encode()).decode()


def icon(x, y, w, h, svg):
    box(x, y, w, h, f"shape=image;html=1;imageAspect=1;aspect=fixed;image={svg_icon(svg)};", "")


def edge(points, dashed=True, arrow=True, width=2):
    sx, sy = points[0]
    tx, ty = points[-1]
    mids = "".join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in points[1:-1])
    st = (f"endArrow={'block' if arrow else 'none'};endFill=1;endSize=7;html=1;rounded=0;"
          f"strokeColor=#111111;strokeWidth={width};"
          + ("dashed=1;dashPattern=3 3;" if dashed else ""))
    cells.append(
        f'<mxCell id="{nid()}" style="{st}" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
        f'<mxPoint x="{sx}" y="{sy}" as="sourcePoint"/><mxPoint x="{tx}" y="{ty}" as="targetPoint"/>'
        f'<Array as="points">{mids}</Array></mxGeometry></mxCell>')


def pill(cx, cy, w, h, label, size=17):
    box(cx - w / 2, cy - h / 2, w, h,
        f"rounded=1;arcSize=50;whiteSpace=wrap;html=1;fillColor=#111111;strokeColor=none;"
        f"fontColor=#FFFFFF;fontStyle=3;fontFamily={FONT};fontSize={size};", label)


def panel(x, y, w, h, title):
    box(x, y, w, h, "rounded=1;arcSize=5;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
        "strokeColor=#222222;strokeWidth=1.6;", "")
    text(x, y + 12, w, 40, title, size=30, bold=True)


def card(x, y, w, h, fill="#E6E6E6"):
    box(x, y, w, h, f"rounded=1;arcSize=7;whiteSpace=wrap;html=1;fillColor={fill};strokeColor=none;", "")


def white(x, y, w, h, value, size=16, align="center"):
    box(x, y, w, h, f"rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=none;"
        f"fontFamily={FONT};fontSize={size};fontColor=#111111;align={align};spacingLeft=6;spacingRight=6;",
        value)


def code(x, y, w, h, value, size=13):
    box(x, y, w, h, f"rounded=1;arcSize=6;whiteSpace=wrap;html=1;fillColor=#111111;strokeColor=none;"
        f"fontFamily={MONO};fontSize={size};fontColor=#FFFFFF;align=left;verticalAlign=top;"
        f"spacingLeft=10;spacingTop=8;spacingRight=6;", value)


def chip(x, y, w, h, label, fill, stroke, strike=False, size=16):
    lab = f"<s>{label}</s>" if strike else label
    box(x, y, w, h, f"rounded=1;arcSize=30;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
        f"strokeWidth=2;fontStyle=1;fontFamily={FONT};fontSize={size};fontColor=#111111;"
        + ("opacity=55;" if strike else ""), lab)


# ---------- icons ----------
def doc(badge=None, color="#3B7DD8", mark=None):
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 125">',
         '<path d="M14 4 H70 L96 30 V121 H14 Z" fill="#E4E7EB"/>',
         '<path d="M70 4 V30 H96 Z" fill="#B9C0C8"/>']
    for yy in (44, 56, 68):
        s.append(f'<rect x="26" y="{yy}" width="56" height="6" rx="3" fill="#AEB6BF"/>')
    if badge:
        s.append(f'<rect x="2" y="78" width="88" height="34" rx="6" fill="{color}"/>')
        s.append(f'<text x="46" y="103" font-family="{FONT}" font-weight="bold" font-size="23" '
                 f'fill="#FFFFFF" text-anchor="middle">{badge}</text>')
    if mark == "alert":
        s.append('<circle cx="84" cy="98" r="22" fill="#D93B30"/>'
                 f'<text x="84" y="109" font-family="{FONT}" font-weight="bold" font-size="32" '
                 'fill="#FFFFFF" text-anchor="middle">!</text>')
    if mark == "check":
        s.append('<circle cx="84" cy="98" r="22" fill="#1E9E5A"/>'
                 '<path d="M73 98 L81 106 L96 89" stroke="#FFFFFF" stroke-width="6" fill="none" '
                 'stroke-linecap="round" stroke-linejoin="round"/>')
    s.append("</svg>")
    return "".join(s)


TERMINAL = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
            '<rect x="2" y="2" width="96" height="96" rx="20" fill="#111111"/>'
            '<path d="M24 34 L44 50 L24 66" stroke="#FFFFFF" stroke-width="8" fill="none" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            '<rect x="50" y="62" width="28" height="8" rx="4" fill="#FFFFFF"/></svg>')

DATABASE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 110">'
            + "".join(
                f'<path d="M8 {y} V{y+22} A42 12 0 0 0 92 {y+22} V{y} Z" fill="{c}"/>'
                for y, c in ((70, "#3F4560"), (46, "#565E86"), (22, "#6E7FB8")))
            + '<ellipse cx="50" cy="22" rx="42" ry="12" fill="#9FB4E3"/></svg>')

WRENCH = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
          '<path d="M64 8 A26 26 0 0 0 40 44 L10 74 A9 9 0 0 0 26 90 L56 60 A26 26 0 0 0 92 36 '
          'L76 48 L60 40 L52 24 Z" fill="#3B7DD8"/></svg>')


# ---------- Fluent Emoji Flat icons (Microsoft, MIT) ----------
ICON_DIR = "/root/paper-diagrams/icons/fluent-emoji-flat"


def fl(name):
    return open(f"{ICON_DIR}/{name}.svg").read()


def ficon(x, y, size, name):
    icon(x, y, size, size, fl(name))


def tag(x, y, label, color, w=58, h=24, size=14):
    box(x, y, w, h, f"rounded=1;arcSize=30;whiteSpace=wrap;html=1;fillColor={color};strokeColor=#FFFFFF;"
        f"strokeWidth=2;fontColor=#FFFFFF;fontStyle=1;fontFamily={FONT};fontSize={size};", label)


def elabel(cx, cy, label, w=60, h=26, size=15):
    box(cx - w / 2, cy - h / 2, w, h, f"rounded=1;arcSize=40;whiteSpace=wrap;html=1;fillColor=#FFFFFF;"
        f"strokeColor=#111111;strokeWidth=1.5;fontStyle=3;fontFamily={FONT};fontSize={size};", label)

# ---------- canvas ----------
W, PT, PB = 1600, 64, 530  # panel top / bottom

# (1) EVIDENCE
panel(10, PT, 300, PB - PT, "(1) EVIDENCE")
icon(28, 118, 66, 76, doc("PCAP", "#3B7DD8"))
text(104, 118, 196, 76, "<b>9 MTA captures</b><br>Windows infections,<br>5k to 49k packets",
     size=16, align="left")
icon(28, 210, 66, 76, doc(mark="alert"))
text(104, 210, 196, 76, "<b>Suricata alerts</b><br>shipped with<br>2 of 9 captures", size=16, align="left")
card(22, 304, 276, 210)
icon(30, 312, 30, 30, WRENCH)
text(64, 312, 230, 30, "validate_ground_truth", size=19, bold=True, align="left")
white(32, 350, 256, 152,
      "Writeup IOCs (victim, family, C2, domains, URLs, hashes) checked against the packets "
      "with <font color='#7B3FA0'><b>tshark</b></font>.<br><br><font color='#D93B30'><b>4 of 9</b></font> "
      "published keys corrected: 2 C2 IPs, 1 victim IP, 1 victim MAC.", size=16)

# (2) INJECTED SKILL  (x 340-720)
panel(340, PT, 380, PB - PT, "(2) INJECTED SKILL")
card(352, 116, 356, 92)
white(362, 124, 336, 34, "<b>A</b> &nbsp;no skill (baseline)", size=16, align="left")
white(362, 164, 336, 36, "<b>B1 to B4</b> &nbsp;community skills, top-2 starred repos", size=15,
      align="left")
card(352, 218, 356, 196)
text(362, 224, 336, 30, "<b>C</b> &nbsp;custom IOC-forensics skill", size=18, align="left")
chip(362, 258, 104, 34, "Workflow", "#EBDDF5", "#8E44AD")
chip(478, 258, 104, 34, "Recipes", "#D9F0E1", "#1E9E5A")
chip(594, 258, 104, 34, "Schema", "#FCE5CF", "#D9822B")
code(362, 302, 336, 104,
     "## Workflow<br>0. inventory evidence, 1. scope,<br>2. victim, ... 6. cross-check IOCs<br>"
     "## tshark recipes<br>tshark -r $P -q -z conv,ip<br>## Required output schema", size=12)
card(352, 424, 356, 94)
text(362, 430, 336, 28, "<b>D1 to D3</b> &nbsp;C minus exactly one block", size=17, align="left")
chip(362, 466, 104, 34, "Workflow", "#EBDDF5", "#8E44AD", strike=True, size=15)
chip(478, 466, 104, 34, "Recipes", "#D9F0E1", "#1E9E5A", strike=True, size=15)
chip(594, 466, 104, 34, "Schema", "#FCE5CF", "#D9822B", strike=True, size=15)

# (3) AGENT  (x 810-1190)
panel(810, PT, 380, PB - PT, "(3) AGENT")
icon(826, 116, 62, 62, TERMINAL)
text(898, 112, 284, 72, "<b>Claude Code CLI</b>, print mode<br>Sonnet (primary), Haiku (replication)"
     "<br>50 turns, 15-min cap", size=15, align="left")
card(822, 194, 356, 112)
text(832, 200, 336, 26, "tool_policy", size=19, bold=True, align="left")
white(832, 230, 164, 68, "<font color='#1E9E5A'><b>ALLOWED</b></font><br>Bash (tshark), Read, Grep, Glob",
      size=14)
white(1004, 230, 164, 68, "<font color='#D93B30'><b>DENIED</b></font><br>Web, Write, Edit, curl, wget, ssh, git",
      size=14)
card(822, 316, 356, 202)
text(832, 322, 336, 26, "investigate (tool loop)", size=19, bold=True, align="left")
code(832, 354, 336, 156,
     "$ ls evidence/<br>$ tshark -r case.pcap -q -z conv,ip<br>"
     "$ tshark -r case.pcap -Y \"nbns||dhcp\"<br>&nbsp;&nbsp;-T fields -e ip.src -e nbns.name<br>"
     "$ tshark -r case.pcap -Y http.request<br>&nbsp;&nbsp;-T fields -e http.host -e http.uri<br>"
     "&gt; incident report", size=12)

# (4) SCORER  (x 1280-1620)
panel(1280, PT, 380, PB - PT, "(4) SCORER")
icon(1296, 114, 64, 72, doc(mark="check"))
text(1370, 112, 282, 76, "<b>Incident report</b> (prose)<br>victim, family, IOCs<br>scored format-agnostic",
     size=15, align="left")
card(1292, 196, 356, 222)
text(1302, 202, 336, 26, "metrics.py", size=19, bold=True, align="left")
mets = ["IOC recall", "Victim ID<br>(4 fields)", "Family<br>attribution",
        "<font color='#D93B30'>Fabricated</font> IOCs", "<font color='#3B7DD8'>tshark</font> commands",
        "Tokens,<br>wall-clock"]
for i, m in enumerate(mets):
    cx = 1302 + (i % 2) * 172
    cy = 234 + (i // 2) * 60
    white(cx, cy, 164, 54, f"<b>{m}</b>", size=15)
card(1292, 428, 356, 90)
icon(1302, 438, 62, 68, DATABASE)
text(1374, 432, 270, 82, "<b>Observable universe</b><br>endpoints, DNS answers, HTTP,<br>"
     "TLS SNI and certs, host fields", size=14, align="left")

# ---------- connectors ----------
edge([(292, PT), (292, 30), (1010, 30), (1010, PT)])
pill(650, 30, 330, 40, "Evidence directory (read-only)")
edge([(708, 300), (822, 300)], dashed=False)
pill(765, 300, 76, 52, "System<br>prompt", size=15)
edge([(1178, 300), (1292, 300)], dashed=False)
pill(1235, 300, 76, 52, "Report,<br>trajectory", size=13)
edge([(160, 514), (160, 566), (1390, 566), (1390, PB)])
pill(560, 566, 200, 40, "GroundTruth")
edge([(60, PB), (60, 604), (1540, 604), (1540, PB)])
pill(1000, 604, 250, 40, "ObservableTokens")

xml = ('<mxfile host="drawio"><diagram name="architecture" id="arch">'
       '<mxGraphModel dx="1670" dy="640" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
       'arrows="1" fold="1" page="0" pageScale="1" pageWidth="1670" pageHeight="640" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) +
       "</root></mxGraphModel></diagram></mxfile>")
open("fig_architecture.drawio", "w").write(xml)
print("cells:", len(cells))
