#!/usr/bin/env python3
"""fig_scoring.drawio: how one run is scored, dense lane layout.
Three tinted dashed lanes (accuracy, faithfulness, efficiency); four inputs on the left;
every output card carries its definition and the measured range from the paper.
Original hand-drawn icons from make_arch.py plus three Fluent Emoji document icons (MIT)."""
src = open("make_arch.py").read()
exec(src[:src.index("# ---------- canvas ----------")])


def step(x, y, w, h, title, sub, ico=None):
    box(x, y, w, h, f"rounded=0;whiteSpace=wrap;html=1;fillColor=#F3F5F7;strokeColor=#6C7A89;"
        f"strokeWidth=3;fontFamily={FONT};fontSize=18;fontColor=#111111;spacingLeft=8;spacingRight=8;",
        f"<b><i>{title}</i></b><br><font style='font-size:14px'>{sub}</font>")
    if ico:
        icon(x - 18, y - 18, 36, 36, ico)


def arrow(points):
    edge(points, dashed=False, width=2)


def card(x, y, w, h, title, sub, result, ico=None):
    box(x, y, w, h, "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#111111;"
        "strokeWidth=2;", "")
    off = 0
    if ico:
        icon(x + 8, y + (h - 50) / 2, 44, 50, ico)
        off = 54
    text(x + 10 + off, y + 4, w - 18 - off, h - 8,
         f"<b>{title}</b><br><font style='font-size:14px'>{sub}</font><br>"
         f"<font style='font-size:14px' color='#3B7DD8'><b>{result}</b></font>", size=17, align="left")


def lane(y, h, title, fill, stroke):
    box(200, y, 1300, h, f"rounded=1;arcSize=4;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
        "strokeWidth=2;dashed=1;dashPattern=4 3;", "")
    text(212, y + 4, 300, 22, f"<b>{title}</b>", size=14, align="left")


def inp(y, ico_name, badge, col, title, sub, svg=None):
    if svg:
        icon(26, y, 60, 60, svg)
    else:
        ficon(24, y - 6, 64, ico_name)
        tag(30, y + 40, badge, col, w=54 if len(badge) < 4 else 62, h=22, size=13)
    text(4, y + 66, 180, 44, f"<b>{title}</b><br><font style='font-size:13px'>{sub}</font>", size=16)


# ---------- lanes ----------
lane(8, 142, "ACCURACY", "#F2F7FD", "#3B7DD8")
lane(160, 262, "FAITHFULNESS", "#FDF9EE", "#D9A21B")
lane(432, 132, "EFFICIENCY", "#F4FBF6", "#1E9E5A")

# ---------- inputs ----------
inp(22, "spiral-notepad", "JSON", "#1E9E5A", "Ground truth", "9 cases, typed IOCs")
inp(170, "page-with-curl", "TXT", "#6C7A89", "Agent report", "free prose, any format")
inp(310, "page-facing-up", "PCAP", "#3B7DD8", "Packet capture", "5k to 49k packets")
inp(446, None, None, None, "Trajectory", "stream log per run", svg=TERMINAL)

# ---------- accuracy lane ----------
step(232, 38, 220, 84, "Value match", "each vetted IOC found in the<br>report by value or alias")
arrow([(96, 52), (232, 52)])
arrow([(96, 208), (190, 208), (190, 104), (232, 104)])
for i, (t_, s_, r_) in enumerate([("IOC recall", "vetted IOCs found / total", "0.87 to 0.91 across arms"),
                                  ("Victim ID", "IP, MAC, hostname, user", "1.00 in 8 of 9 arms"),
                                  ("Family", "malware family named", "0.44 to 0.56, max 5 of 9")]):
    card(500 + i * 330, 34, 318, 92, t_, s_, r_)
arrow([(452, 80), (500, 80)])
for i in (1, 2):
    cx = 500 + i * 330 + 159
    arrow([(476, 80), (476, 136), (cx, 136), (cx, 126)])

# ---------- faithfulness lane ----------
step(232, 186, 220, 84, "Extract tokens", "regex over the report:<br>every IPv4 and domain")
arrow([(96, 234), (232, 234)])
tag(474, 196, "141.98.10.79", "#3B7DD8", w=140, h=28, size=14)
tag(490, 230, "c2.example", "#8E44AD", w=124, h=28, size=14)
text(466, 260, 160, 22, "<b>asserted tokens</b>", size=14)
arrow([(452, 228), (472, 228)])
step(660, 186, 250, 116, "Fabrication test", "token absent from the observable<br>universe and not excluded?")
arrow([(626, 228), (660, 228)])

card(1000, 176, 486, 76, "Fabricated IOC", "counted per case and per emitted token",
     "0.07 to 0.26 per case; no arm differs (C vs A p=0.51)", ico=doc(mark="alert"))
card(1000, 260, 486, 70, "Grounded", "token seen as endpoint, DNS answer, HTTP, TLS, or host field",
     "not counted", ico=doc(mark="check"))
arrow([(910, 222), (950, 222), (950, 214), (1000, 214)])
elabel(955, 200, "yes", w=50, h=24, size=14)
arrow([(910, 270), (950, 270), (950, 295), (1000, 295)])
elabel(955, 284, "no", w=50, h=24, size=14)

step(232, 318, 220, 84, "tshark passes", "ip, dns.a, http, TLS SNI,<br>x509, nbns, dhcp, kerberos",
     WRENCH)
arrow([(96, 342), (232, 342)])
icon(478, 326, 58, 64, DATABASE)
text(544, 324, 160, 70, "<b>Observable universe</b><br><font style='font-size:13px'>up to 310 IPs, "
     "157 domains</font>", size=15, align="left")
arrow([(452, 358), (478, 358)])
arrow([(700, 358), (760, 358), (760, 302)])
elabel(760, 330, "lookup", w=70, h=24, size=14)

box(1000, 340, 486, 70, "rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#999999;"
    "strokeWidth=2;dashed=1;", "")
text(1012, 344, 466, 62, "<b>Never counted</b><br><font style='font-size:14px'>victim subnet, gateway "
     "and DC, benign reference domains (allowlist)</font>", size=16, align="left")
arrow([(1000, 375), (860, 375), (860, 302)])

# ---------- efficiency lane ----------
step(232, 456, 220, 84, "Parse trajectory", "count tool calls; read token<br>and timing fields")
arrow([(96, 476), (232, 476)])
for i, (t_, s_, r_) in enumerate([("<font color='#3B7DD8'>tshark</font> calls", "discrete invocations",
                                   "C 8.6 vs A 12.3: 30% fewer, p&lt;0.001"),
                                  ("Output tokens", "per run", "11% fewer, n.s. (p=0.22)"),
                                  ("Wall-clock", "seconds per run", "13% faster, n.s. (p=0.09)")]):
    card(500 + i * 330, 452, 318, 92, t_, s_, r_)
arrow([(452, 498), (500, 498)])

xml = ('<mxfile host="drawio"><diagram name="scoring" id="scoring">'
       '<mxGraphModel dx="1510" dy="570" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" '
       'arrows="1" fold="1" page="0" pageScale="1" pageWidth="1510" pageHeight="570" math="0" shadow="0">'
       '<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) +
       "</root></mxGraphModel></diagram></mxfile>")
open("fig_scoring.drawio", "w").write(xml)
print("cells:", len(cells))
