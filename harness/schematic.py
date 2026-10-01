#!/usr/bin/env python3
"""Page-1 teaser: the six-arm protocol as boxes (C = workflow+recipes+schema; D1-D3
remove one block each). Compact layout, no em dashes, no empty band."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

FIG = Path(__file__).resolve().parent.parent / "figures"
NAVY, BLUE, GREEN, GREY, EXT = "#1F4E79", "#2E75B6", "#009E73", "#C3CAD2", "#8FA3B0"

fig, ax = plt.subplots(figsize=(7.0, 2.55))
ax.axis("off")
ax.set_xlim(0, 10)
ax.set_ylim(0.0, 3.65)

comps = ["workflow", "recipes", "schema"]
# 0 absent (grey, blank), 1 present (colored+label), 2 external (all "ext")
arms = [("A", [0, 0, 0], "no skill"), ("B", [2, 2, 2], "community"),
        ("C", [1, 1, 1], "custom"), ("D1", [0, 1, 1], "no workflow"),
        ("D2", [1, 0, 1], "no recipes"), ("D3", [1, 1, 0], "no schema")]
present_col = [NAVY, BLUE, GREEN]

x0, cw, cgap = 0.15, 1.45, 0.18
row_top, rh, rgap = 2.62, 0.58, 0.11   # top row sits below the arm-name labels

def block(x, y, w, h, label, color, tc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.015,rounding_size=0.05",
                 fc=color, ec="white", lw=1.1))
    if label:
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                color=tc, fontsize=8.5, fontweight="bold")

for i, (name, mask, sub) in enumerate(arms):
    x = x0 + i * (cw + cgap)
    ax.text(x + cw/2, 3.42, name, ha="center", fontsize=12, fontweight="bold", color=NAVY)
    for j, present in enumerate(mask):
        y = row_top - j * (rh + rgap)
        if present == 0:
            block(x, y, cw, rh, "", GREY)           # absent: grey, blank (no em dash)
        elif present == 2:
            block(x, y, cw, rh, "ext", EXT)          # external skill
        else:
            block(x, y, cw, rh, comps[j], present_col[j])
    ax.text(x + cw/2, 0.80, sub, ha="center", fontsize=8, color="#555")

ax.text(5.0, 0.22,
        "Same model, same tshark toolbox, same task. Only the injected skill changes.",
        ha="center", fontsize=8.5, style="italic", color="#333")
fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
fig.savefig(FIG / "fig_schematic.pdf", bbox_inches="tight", pad_inches=0.03)
print("wrote fig_schematic.pdf (compact, no em dashes)")
