#!/usr/bin/env python3
"""Cross-model (Haiku vs Sonnet) comparison table for the paper."""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "results" / "summary.csv")
df = df[(df["returncode"] == 0) & (df["tool_calls"] > 0)].copy()
df["vic"] = df["victim_correct"] / df["victim_total"]

BS = "\\\\"
lines = [r"\begin{tabular}{@{}llrrrrr@{}}", r"\toprule",
         r"Model & Arm & Recall & Victim & Halluc.$\downarrow$ & \texttt{tshark}$\downarrow$ & Wall s$\downarrow$ " + BS,
         r"\midrule"]
for mdl, lab in [("haiku", "Haiku"), ("sonnet", "Sonnet")]:
    dd = df[df["model"] == mdl]
    cm = dd.groupby(["case", "arm"])[["recall", "vic", "hallucination_count", "tshark_calls", "wall_time_s"]].mean()
    d = cm.groupby("arm").mean().rename(columns={
        "hallucination_count": "halluc", "tshark_calls": "tshark", "wall_time_s": "wall"})
    for arm in ["A", "C"]:
        r = d.loc[arm]
        name = lab if arm == "A" else ""
        lines.append(f"{name} & {arm} & {r.recall:.3f} & {r.vic:.3f} & {r.halluc:.2f} "
                     f"& {r.tshark:.1f} & {r.wall:.0f} " + BS)
    if mdl == "haiku":
        lines.append(r"\midrule")
lines += [r"\bottomrule", r"\end{tabular}"]
(ROOT / "paper" / "tab_crossmodel.tex").write_text("\n".join(lines))
print("\n".join(lines))
