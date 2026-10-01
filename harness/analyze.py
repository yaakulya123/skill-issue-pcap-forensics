#!/usr/bin/env python3
"""Aggregate results/summary.csv into per-arm statistics and publication figures.

Run with the project venv:  .venv/bin/python harness/analyze.py
Robust to partial data: works on whatever runs have completed so far."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

ARM_ORDER = ["A", "B", "B2", "B3", "B4", "C", "D1", "D2", "D3"]
ARM_LABEL = {"A": "A: vanilla", "B": "B1: comm-wireshark", "B2": "B2: comm-malware",
             "B3": "B3: comm-pcap", "B4": "B4: comm-wireshark2", "C": "C: custom",
             "D1": "D1: no-workflow", "D2": "D2: no-recipes", "D3": "D3: no-schema"}
# Okabe-Ito colorblind-safe palette (community skills share the orange family)
OI = {"A": "#999999", "B": "#E69F00", "B2": "#F0A830", "B3": "#D68910", "B4": "#B9770E",
      "C": "#0072B2", "D1": "#56B4E9", "D2": "#009E73", "D3": "#CC79A7"}

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 300, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "font.family": "sans-serif",
})


def load():
    df = pd.read_csv(ROOT / "results" / "summary.csv")
    # Drop runs that never executed: the Claude Code session-limit hit during reps 2-3
    # produced empty transcripts (returncode 1, zero tool calls). These are not
    # forensic outcomes and must not enter the statistics.
    n0 = len(df)
    df = df[(df["returncode"] == 0) & (df["tool_calls"] > 0)].copy()
    # Primary-model results (Sonnet); Haiku is reported only in the cross-model table.
    df = df[df["model"] == "sonnet"].copy()
    dropped = n0 - len(df)
    if dropped:
        print(f"[load] dropped {dropped} empty/limit-hit runs; {len(df)} valid runs remain")
    # blanks (agent named no family, or capture has no labeled ground-truth family)
    # score as incorrect, consistent with stats.py and the "blanks scored incorrect"
    # convention -> denominator is all 9 cases for every arm.
    df["family_correct"] = df["family_correct"].map(
        lambda x: 1.0 if str(x) == "True" else 0.0)
    df["victim_acc"] = df["victim_correct"] / df["victim_total"]
    return df


METRICS = ["recall", "victim_acc", "family_correct", "hallucination_count",
           "tshark_calls", "output_tokens", "wall_time_s"]


def agg(df):
    """Two-level aggregation: average over reps within each (case, arm), then take the
    mean and std across the 9 cases. This reports case-level variability (n=cases) and
    keeps a case with more reps from dominating."""
    per_case = df.groupby(["arm", "case"])[METRICS].mean().reset_index()
    g = per_case.groupby("arm")
    out = pd.DataFrame({
        "n_cases": g["recall"].count(),
        "recall": g["recall"].mean(), "recall_sd": g["recall"].std(),
        "victim_acc": g["victim_acc"].mean(),
        "family_rate": g["family_correct"].mean(),
        "halluc": g["hallucination_count"].mean(),
        "halluc_sd": g["hallucination_count"].std(),
        "tshark": g["tshark_calls"].mean(),
        "out_tok": g["output_tokens"].mean(),
        "wall": g["wall_time_s"].mean(),
    }).reindex([a for a in ARM_ORDER if a in g.groups])
    out["reps"] = df.groupby("arm")["rep"].nunique().reindex(out.index)
    return out


def write_tables(a):
    (ROOT / "results" / "aggregate.csv").write_text(a.to_csv())
    md = ["| Arm | reps | Recall (sd) | Victim | Family | Halluc (sd) | tshark | Out tok | Wall s |",
          "|---|---|---|---|---|---|---|---|---|"]
    for arm, r in a.iterrows():
        md.append(f"| {ARM_LABEL.get(arm, arm)} | {int(r['reps'])} | "
                  f"{r['recall']:.3f} ({r['recall_sd']:.3f}) | {r['victim_acc']:.3f} | "
                  f"{r['family_rate']:.3f} | {r['halluc']:.2f} ({r['halluc_sd']:.2f}) | "
                  f"{r['tshark']:.1f} | {r['out_tok']:.0f} | {r['wall']:.0f} |")
    (ROOT / "results" / "aggregate.md").write_text("\n".join(md))
    print("\n".join(md))
    # LaTeX 9-arm main table (generated so it always matches the data)
    short = {"A": "A: vanilla", "B": "B1: comm-wireshark", "B2": "B2: comm-malware",
             "B3": "B3: comm-pcap", "B4": "B4: comm-wireshark2", "C": "\\textbf{C: custom}",
             "D1": "D1: no-workflow", "D2": "D2: no-recipes", "D3": "D3: no-schema"}
    tl = [r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
          r"Arm & Recall & Victim & Family & Halluc.$\downarrow$ & \texttt{tshark}$\downarrow$ & Tok$\downarrow$ \\",
          r"\midrule"]
    for arm, r in a.iterrows():
        bold = arm == "C"
        rec = f"\\textbf{{{r['recall']:.3f}}}" if bold else f"{r['recall']:.3f}"
        tsh = f"\\textbf{{{r['tshark']:.1f}}}" if bold else f"{r['tshark']:.1f}"
        tl.append(f"{short.get(arm, arm)} & {rec} & {r['victim_acc']:.3f} & {r['family_rate']:.2f} "
                  f"& {r['halluc']:.2f} & {tsh} & {r['out_tok']:.0f} \\\\")
        if arm == "B4":
            tl.append(r"\midrule")
    tl += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "paper" / "tab_main.tex").write_text("\n".join(tl))


def fig_main(a):
    arms = list(a.index)
    metrics = [("recall", "IOC recall"), ("victim_acc", "Victim ID acc"),
               ("family_rate", "Family acc")]
    x = np.arange(len(arms)); w = 0.26
    fig, ax = plt.subplots(figsize=(7, 3.4))
    for j, (col, lab) in enumerate(metrics):
        yerr = a["recall_sd"].values if col == "recall" else None
        ax.bar(x + (j - 1) * w, a[col].values, w, label=lab, yerr=yerr, capsize=2,
               error_kw={"linewidth": 0.7},
               color=plt.cm.Blues(0.4 + 0.2 * j), edgecolor="white", linewidth=0.5)
    ax.set_xticks(x); ax.set_xticklabels([ARM_LABEL[m] for m in arms], rotation=20, ha="right")
    ax.set_ylabel("score"); ax.set_ylim(0, 1.05)
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(); fig.savefig(FIG / "fig_main_bars.pdf"); plt.close(fig)


def fig_pareto(a):
    fig, ax = plt.subplots(figsize=(5.2, 4))
    for arm, r in a.iterrows():
        ax.scatter(r["out_tok"], r["recall"], s=120, color=OI.get(arm, "#333"),
                   edgecolor="black", linewidth=0.6, zorder=3)
        ax.annotate(arm, (r["out_tok"], r["recall"]),
                    textcoords="offset points", xytext=(7, 4), fontsize=9)
    ax.set_xlabel("mean output tokens (cost proxy)"); ax.set_ylabel("mean IOC recall")
    ax.set_title("Accuracy vs cost by arm", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_pareto.pdf"); plt.close(fig)


def fig_halluc(a):
    arms = list(a.index)
    fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.bar([ARM_LABEL[m] for m in arms], a["halluc"].values,
           color=[OI[m] for m in arms], edgecolor="white")
    ax.set_ylabel("mean hallucinated IOCs"); ax.tick_params(axis="x", rotation=20)
    for lab in ax.get_xticklabels():
        lab.set_ha("right")
    fig.tight_layout(); fig.savefig(FIG / "fig_halluc.pdf"); plt.close(fig)


def fig_heatmap(df):
    piv = df.pivot_table(index="case", columns="arm", values="recall", aggfunc="mean")
    piv = piv.reindex(columns=[a for a in ARM_ORDER if a in piv.columns])
    fig, ax = plt.subplots(figsize=(6.4, 0.5 * len(piv) + 1.6))
    im = ax.imshow(piv.values, cmap="YlGnBu", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(piv.columns))); ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels([c.replace("mta-", "") for c in piv.index], fontsize=8)
    for i in range(len(piv.index)):
        for j in range(len(piv.columns)):
            v = piv.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7,
                        color="white" if v > 0.6 else "black")
    fig.colorbar(im, ax=ax, label="IOC recall", fraction=0.046)
    ax.set_title("Per-case IOC recall by arm", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_heatmap.pdf"); plt.close(fig)


def fig_ablation(a):
    """Component contribution measured as (ablation - full skill C), case-level means.
    Left panel: extra tshark commands when the component is removed, on both models
    (positive = the component makes the agent leaner). Right panel: recall change when
    the component is removed, primary model (negative = the component helped recall).
    Haiku is read straight from summary.csv because load() keeps Sonnet only."""
    if not all(x in a.index for x in ["C", "D1", "D2", "D3"]):
        return
    comps = [("workflow", "D1"), ("recipes", "D2"), ("schema", "D3")]
    raw = pd.read_csv(ROOT / "results" / "summary.csv")
    raw = raw[(raw["returncode"] == 0) & (raw["tool_calls"] > 0)]
    def cm(model, arm, col):
        s = raw[(raw["model"] == model) & (raw["arm"] == arm)]
        return s.groupby("case")[col].mean().mean()
    x = np.arange(len(comps)); w = 0.38
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    ax = axes[0]
    for off, model, col in [(-w/2, "sonnet", "#0072B2"), (w/2, "haiku", "#56B4E9")]:
        vals = [cm(model, d, "tshark_calls") - cm(model, "C", "tshark_calls") for _, d in comps]
        ax.bar(x + off, vals, w, label=model.capitalize(), color=col)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels([c for c, _ in comps])
    ax.set_ylabel("extra tshark commands\nwhen removed (ablation $-$ C)", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Command count", fontsize=10)
    ax = axes[1]
    rec = [a.loc[d, "recall"] - a.loc["C", "recall"] for _, d in comps]
    ax.bar(x, rec, 0.5, color="#999999")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels([c for c, _ in comps])
    ax.set_ylabel("recall change when removed\n(ablation $-$ C), Sonnet", fontsize=9)
    ax.set_title("IOC recall", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_ablation.pdf"); plt.close(fig)


def fig_community(a):
    """Vanilla (A) vs the community-skill population (B1-B4, shown as a band with its
    mean) vs the custom skill (C), on hallucination and tool-call efficiency. Makes the
    point that C beats the whole community population, not one cherry-picked skill."""
    comm = [x for x in ["B", "B2", "B3", "B4"] if x in a.index]
    if not comm or "C" not in a.index or "A" not in a.index:
        return
    import numpy as np
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    for ax, col, ylab in [(axes[0], "halluc", "fabricated IOCs / case"),
                          (axes[1], "tshark", "tshark commands")]:
        groups = ["A"] + comm + ["C"]
        vals = [a.loc[g, col] for g in groups]
        colors = [OI["A"]] + [OI[g] for g in comm] + [OI["C"]]
        ax.bar(range(len(groups)), vals, color=colors, edgecolor="white")
        # community band
        cmean = np.mean([a.loc[g, col] for g in comm])
        ax.axhline(cmean, color="#B9770E", ls="--", lw=1, alpha=0.7)
        ax.set_xticks(range(len(groups)))
        ax.set_xticklabels(["A"] + [g if g != "B" else "B1" for g in comm] + ["C"],
                           fontsize=8, rotation=0)
        ax.set_ylabel(ylab, fontsize=9)
    axes[0].set_title("Faithfulness", fontsize=10)
    axes[1].set_title("Efficiency", fontsize=10)
    fig.suptitle("Custom skill (C) vs the community-skill population (B1-B4) vs vanilla (A)",
                 fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_community.pdf"); plt.close(fig)


def main():
    df = load()
    a = agg(df)
    fig_community(a)
    print(f"loaded {len(df)} runs across arms {list(a.index)}\n")
    write_tables(a)
    fig_main(a); fig_pareto(a); fig_halluc(a); fig_ablation(a)
    if df["case"].nunique() >= 1:
        fig_heatmap(df)
    print(f"\nfigures written to {FIG}")


if __name__ == "__main__":
    main()
