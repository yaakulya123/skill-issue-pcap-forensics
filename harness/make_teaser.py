#!/usr/bin/env python3
"""fig_teaser.drawio: one-column intro figure. Same agent, three skill conditions; the
stack height is the real mean tshark command count (Sonnet, case-level means), and every
lane ends in a report of near-identical recall."""
src = open("make_arch.py").read()
exec(src[:src.index("# ---------- canvas ----------")])

LANES = [  # label, skill badge, colour, commands (mean), recall, chips
    ("A: no skill", None, "#999999", "12.3", "0.87", 12),
    ("B1-B4: community", "SKILL", "#D9822B", "11.0", "0.88", 11),
    ("C: custom", "SKILL", "#3B7DD8", "8.6", "0.90", 9),
]
NOSKILL = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 125">'
           '<path d="M14 4 H70 L96 30 V121 H14 Z" fill="none" stroke="#B9C0C8" stroke-width="5" '
           'stroke-dasharray="10 7"/><line x1="10" y1="118" x2="100" y2="8" stroke="#D93B30" '
           'stroke-width="7" stroke-linecap="round"/></svg>')
CHIP = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 22">'
        '<rect x="0" y="0" width="140" height="22" rx="6" fill="#111111"/>'
        '<path d="M10 6 L17 11 L10 16" stroke="#FFFFFF" stroke-width="3" fill="none" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '<rect x="22" y="14" width="10" height="3" fill="#FFFFFF"/>'
        '<rect x="42" y="9" width="70" height="4" rx="2" fill="#6C7A89"/></svg>')

W = 780
for i, (lab, badge, col, cmds, rec, n) in enumerate(LANES):
    cx = 140 + i * 250
    text(cx - 120, 6, 240, 36, f"<b>{lab}</b>", size=24)
    if badge:
        icon(cx - 33, 48, 66, 76, doc(badge, col))
    else:
        icon(cx - 33, 48, 66, 76, NOSKILL)
    edge([(cx, 128), (cx, 168)], dashed=False, width=2)
    icon(cx - 30, 170, 60, 60, TERMINAL)
    edge([(cx, 232), (cx, 262)], dashed=False, width=2)
    for k in range(n):
        icon(cx - 70, 266 + k * 26, 140, 22, CHIP)
    top, bot = 266, 266 + n * 26
    text(cx + 74, top, 90, 40, f"<b>{cmds}</b>", size=28, align="left")
    text(cx + 74, top + 34, 90, 30, "cmds", size=18, align="left")
    edge([(cx, bot + 4), (cx, 600)], dashed=False, width=2)
    icon(cx - 33, 602, 66, 76, doc(mark="check"))
    text(cx - 110, 680, 220, 34, f"<b>recall {rec}</b>", size=22)

box(150, 730, 480, 50, f"rounded=1;arcSize=50;whiteSpace=wrap;html=1;fillColor=#111111;strokeColor=none;"
    f"fontColor=#FFFFFF;fontStyle=3;fontFamily={FONT};fontSize=22;",
    "C: 30% fewer commands, same recall")

xml = ('<mxfile host="drawio"><diagram name="teaser" id="teaser">'
       f'<mxGraphModel dx="{W}" dy="800" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
       f'arrows="1" fold="1" page="0" pageScale="1" pageWidth="{W}" pageHeight="800" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) +
       "</root></mxGraphModel></diagram></mxfile>")
open("fig_teaser.drawio", "w").write(xml)
print("cells:", len(cells))
