#!/usr/bin/env python3
"""Classify every shell/tshark command each arm issued across all trajectories into
forensic categories, then plot the per-arm command grammar. This exposes HOW each arm
investigates, not just how well. Also reports behavioral signals: did the arm inventory
the evidence directory, and did it read the IDS alert file.

Run: .venv/bin/python harness/grammar.py"""
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TRAJ = ROOT / "results" / "trajectories"
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)

ARM_ORDER = ["A", "B", "B2", "B3", "B4", "C", "D1", "D2", "D3"]
ARM_LABEL = {"A": "A\nvanilla", "B": "B1\ncomm", "B2": "B2\ncomm", "B3": "B3\ncomm",
             "B4": "B4\ncomm", "C": "C\ncustom",
             "D1": "D1\nno-wf", "D2": "D2\nno-rec", "D3": "D3\nno-sch"}
MODEL = "sonnet"  # primary model only; trajectories dir also holds Haiku runs

# category -> ordered list of (regex) tests applied to each command string
CATS = [
    ("inventory",   [r"\bls\b", r"\bfile\s", r"\bcat\s+[^|]*alert", r"\bhead\s+[^|]*\.txt"]),
    ("stats",       [r"-z\s*io,phs", r"-z\s*conv", r"-z\s*endpoints", r"-z\s*io,stat", r"-z\s*expert"]),
    ("victim_id",   [r"nbns", r"dhcp", r"kerberos", r"ldap", r"\barp\b", r"smb.*session", r"browser"]),
    ("http",        [r"http\.request", r"http\.host", r"-z\s*http", r"http\.user_agent"]),
    ("dns",         [r"dns\.qry", r"-z\s*dns", r"\bdns\b"]),
    ("tls",         [r"tls\.handshake", r"server_name", r"\bja3\b", r"x509"]),
    ("flow_beacon", [r"tcp\.flags\.syn", r"tcp\.stream", r"follow", r"tcp\.analysis"]),
    ("export_hash", [r"--export-objects", r"shasum", r"sha256", r"md5"]),
]


def classify(cmd: str) -> str:
    c = cmd.lower()
    for name, tests in CATS:
        if any(re.search(t, c) for t in tests):
            return name
    if "tshark" in c:
        return "other_tshark"
    return "non_tshark"


def arm_of(fname: str) -> str:
    # mta-XXXX__ARM__model__rN.stream.jsonl
    return fname.split("__")[1]


def commands(path: Path):
    """Return (bash_commands, read_targets): bash command strings and the file paths
    the agent opened with the Read/Grep tools."""
    cmds, reads = [], []
    for line in path.read_text().splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for b in ev.get("message", {}).get("content", []):
                if b.get("type") != "tool_use":
                    continue
                inp = b.get("input", {})
                if "command" in inp:
                    cmds.append(inp["command"])
                for key in ("file_path", "path", "pattern"):
                    if key in inp and isinstance(inp[key], str):
                        reads.append(inp[key])
    return cmds, reads


def main():
    cat_counts = defaultdict(lambda: defaultdict(int))   # arm -> cat -> count
    behav = defaultdict(lambda: {"runs": 0, "inv": 0, "alert": 0, "cmds": 0})
    for f in sorted(TRAJ.glob("*.stream.jsonl")):
        arm = arm_of(f.name)
        if arm not in ARM_ORDER or f.name.split("__")[2] != MODEL:
            continue
        cmds, reads = commands(f)
        behav[arm]["runs"] += 1
        behav[arm]["cmds"] += len(cmds)
        run_txt = " \n ".join(cmds).lower()
        reads_txt = " \n ".join(reads).lower()
        if re.search(r"\bls\b", run_txt) or "alert" in reads_txt:
            behav[arm]["inv"] += 1
        # alert access via bash OR the Read/Grep tool file_path
        if re.search(r"(cat|head|grep|less|strings)\s+[^|\n]*alert", run_txt) or "alert" in reads_txt:
            behav[arm]["alert"] += 1
        for cmd in cmds:
            cat_counts[arm][classify(cmd)] += 1

    cats = [c[0] for c in CATS] + ["other_tshark", "non_tshark"]
    # ---- stacked bar: normalized command grammar per arm ----
    fig, ax = plt.subplots(figsize=(8.4, 4))
    arms = [a for a in ARM_ORDER if a in cat_counts]
    bottoms = np.zeros(len(arms))
    cmap = plt.cm.tab20(np.linspace(0, 1, len(cats)))
    for ci, cat in enumerate(cats):
        vals = np.array([cat_counts[a].get(cat, 0) for a in arms], float)
        tot = np.array([sum(cat_counts[a].values()) for a in arms], float)
        frac = np.divide(vals, tot, out=np.zeros_like(vals), where=tot > 0)
        ax.bar([ARM_LABEL[a] for a in arms], frac, bottom=bottoms,
               label=cat, color=cmap[ci], edgecolor="white", linewidth=0.4)
        bottoms += frac
    ax.set_ylabel("fraction of commands"); ax.set_ylim(0, 1)
    ax.legend(ncol=2, fontsize=7, frameon=False, bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.set_title("Investigation grammar: command mix by arm (Sonnet)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_grammar.pdf"); plt.close(fig)

    # ---- behavioral table ----
    lines = ["| Arm | runs | inventoried dir | read alerts | mean cmds/run |",
             "|---|---|---|---|---|"]
    for a in arms:
        b = behav[a]
        lines.append(f"| {a} | {b['runs']} | {b['inv']}/{b['runs']} | "
                     f"{b['alert']}/{b['runs']} | {b['cmds']/max(b['runs'],1):.1f} |")
    (ROOT / "results" / "grammar_behavior.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nfig_grammar.pdf written")


if __name__ == "__main__":
    main()
