#!/usr/bin/env python3
"""Inferential statistics + LaTeX-ready tables for the paper. Case-level paired tests
(average reps within case, then pair across the 9 cases) and 95% CIs. Writes:
  results/stats.md           human-readable
  paper/tab_stats.tex        paired-test table (efficiency + accuracy)
  paper/tab_percase.tex      per-case recall / halluc / tshark grid
Run: .venv/bin/python harness/stats.py"""
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
ARMS = ["A", "B", "B2", "B3", "B4", "C", "D1", "D2", "D3"]
LAB = {"A": "A vanilla", "B": "B1 comm-wireshark", "B2": "B2 comm-malware",
       "B3": "B3 comm-pcap", "B4": "B4 comm-wireshark2", "C": "C custom",
       "D1": "D1 no-wf", "D2": "D2 no-rec", "D3": "D3 no-sch"}


def load():
    df = pd.read_csv(ROOT / "results" / "summary.csv")
    df = df[(df["returncode"] == 0) & (df["tool_calls"] > 0)].copy()
    # Table III and the main aggregate describe the PRIMARY model (Sonnet).
    # The Haiku cross-model comparison lives in its own table (crossmodel.py).
    df = df[df["model"] == "sonnet"].copy()
    df["fam"] = df["family_correct"].map(lambda x: 1.0 if str(x) == "True" else 0.0)
    df["victim_acc"] = df["victim_correct"] / df["victim_total"]
    return df


def casemeans(df, metric):
    return df.groupby(["case", "arm"])[metric].mean().unstack()


def ci95(x):
    x = np.asarray(x, float)
    n = len(x); m = x.mean(); sd = x.std(ddof=1)
    h = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n)
    return m, m - h, m + h


def paired(df, metric, a1, a2):
    m = casemeans(df, metric)[[a1, a2]].dropna()
    d = m[a1] - m[a2]
    t, p = stats.ttest_rel(m[a1], m[a2])
    dz = d.mean() / d.std(ddof=1) if d.std(ddof=1) else float("nan")
    return dict(mean_d=d.mean(), t=t, p=p, dz=dz, n=len(m))


def main():
    df = load()
    out = ["# Inferential statistics (case-level, n=9 unless noted)\n"]

    # 95% CIs per arm per metric
    out.append("## 95% confidence intervals (case-level means)\n")
    for metric in ["recall", "victim_acc", "fam", "hallucination_count", "tshark_calls",
                   "output_tokens", "wall_time_s"]:
        cm = casemeans(df, metric)
        row = [metric]
        for a in ARMS:
            if a in cm:
                m, lo, hi = ci95(cm[a].dropna())
                row.append(f"{a}={m:.3f}[{lo:.3f},{hi:.3f}]")
        out.append("- " + "  ".join(row))
    out.append("")

    # Paired tests vs vanilla (A) and C vs B
    out.append("## Paired t-tests\n")
    tests = []
    for metric in ["tshark_calls", "output_tokens", "wall_time_s", "recall",
                   "hallucination_count", "fam"]:
        for a1, a2 in [("C", "A"), ("B", "A"), ("C", "B")]:
            r = paired(df, metric, a1, a2)
            sig = "***" if r["p"] < .001 else "**" if r["p"] < .01 else "*" if r["p"] < .05 else "ns"
            tests.append((metric, a1, a2, r, sig))
            out.append(f"- {metric} {a1}-{a2}: d={r['mean_d']:+.3f} t={r['t']:.2f} "
                       f"p={r['p']:.4f} dz={r['dz']:+.2f} {sig}")
    (ROOT / "results" / "stats.md").write_text("\n".join(out))
    print("\n".join(out))

    # --- LaTeX: paired-test table (efficiency block + accuracy block) ---
    # Holm-Bonferroni over the 6 efficiency contrasts (one "cost" family)
    eff = [("tshark_calls", "C", "A"), ("tshark_calls", "B", "A"),
           ("output_tokens", "C", "A"), ("output_tokens", "B", "A"),
           ("wall_time_s", "C", "A"), ("wall_time_s", "B", "A")]
    effp = sorted(((paired(df, m, a, b)["p"], (m, a, b)) for m, a, b in eff))
    holm = {}
    for i, (p, key) in enumerate(effp):
        holm[key] = p * (len(effp) - i)  # step-down adjusted p (not yet monotone-enforced)
    run = 0.0
    for p, key in effp:
        run = max(run, holm[key]); holm[key] = min(run, 1.0)

    disp = {"B": "B1"}  # arm "B" in the data is the single skill B1; label it so
    def texrow(metric, a1, a2):
        d1, d2 = disp.get(a1, a1), disp.get(a2, a2)
        r = paired(df, metric, a1, a2)
        p = r["p"]
        hp = holm.get((metric, a1, a2))
        star = lambda q: "\\textbf{***}" if q < .001 else "\\textbf{**}" if q < .01 else "\\textbf{*}" if q < .05 else "ns"
        if np.isnan(r["t"]):
            return f"{metric.replace('_',' ')} & {d1}$-${d2} & {r['mean_d']:+.2f} & --- & --- & --- & ns \\\\"
        pstr = "$<$0.001" if p < .001 else f"{p:.3f}"
        hstr = "" if hp is None else (f" ({'$<$.001' if hp<.001 else f'{hp:.3f}'})")
        # significance star reflects the ADJUSTED p where a correction applies (efficiency
        # rows), so the table never shows more significance than survives correction.
        sig_p = hp if hp is not None else p
        return f"{metric.replace('_',' ')} & {d1}$-${d2} & {r['mean_d']:+.2f} & {r['t']:.2f} & {pstr}{hstr} & {r['dz']:+.2f} & {star(sig_p)} \\\\"
    lines = [r"\begin{tabular}{@{}llrrrrl@{}}", r"\toprule",
             r"Metric & Contrast & $\Delta$ & $t$ & $p$ & $d_z$ & sig \\", r"\midrule",
             r"\multicolumn{7}{@{}l}{\emph{Efficiency / cost}}\\"]
    for m in ["tshark_calls", "output_tokens", "wall_time_s"]:
        lines.append(texrow(m, "C", "A")); lines.append(texrow(m, "B", "A"))
    lines.append(r"\midrule")
    lines.append(r"\multicolumn{7}{@{}l}{\emph{Accuracy / faithfulness}}\\")
    for m in ["recall", "hallucination_count", "fam"]:
        lines.append(texrow(m, "C", "A"))
    lines += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "paper" / "tab_stats.tex").write_text("\n".join(lines))

    # --- LaTeX: per-case grid (recall | halluc | tshark) for arms A,B,C ---
    rec = casemeans(df, "recall"); hal = casemeans(df, "hallucination_count"); tsh = casemeans(df, "tshark_calls")
    pl = [r"\begin{tabular}{@{}lrrrrrr@{}}", r"\toprule",
          r" & \multicolumn{3}{c}{IOC recall} & \multicolumn{3}{c}{Halluc.\ / tshark (C)} \\",
          r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
          r"Case & A & B1 & C & rec.\ sd & hal.\ C & tshk C \\", r"\midrule"]
    for case in sorted(rec.index):
        cn = case.replace("mta-", "")
        sd = rec.loc[case, ["A", "B", "C"]].std()
        pl.append(f"{cn} & {rec.loc[case,'A']:.2f} & {rec.loc[case,'B']:.2f} & {rec.loc[case,'C']:.2f} "
                  f"& {sd:.2f} & {hal.loc[case,'C']:.1f} & {tsh.loc[case,'C']:.0f} \\\\")
    pl += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "paper" / "tab_percase.tex").write_text("\n".join(pl))
    print("\nwrote paper/tab_stats.tex, paper/tab_percase.tex")


if __name__ == "__main__":
    main()
