#!/usr/bin/env python3
"""Four-arm (six-variant) agent harness for the Skill Issue experiment.

Runs the SAME forensic task and the SAME tshark toolbox across arms that differ only
in the injected Agent Skill (the independent variable):

  A  vanilla        no skill
  B  official       Anthropic community wireshark skill
  C  custom         our pcap-ioc-forensics skill
  D1 no-workflow    C minus the WORKFLOW section
  D2 no-recipes     C minus the tshark RECIPES section
  D3 no-schema      C minus the output SCHEMA section

The agent runtime is the `claude` CLI in print mode. Web/network tools are disallowed
so the agent cannot look up the published answer; full trajectories are logged for
post-hoc audit. Scoring is format-agnostic (see metrics.py)."""
import argparse
import json
import subprocess
import time
from pathlib import Path

from metrics import score
from pcap_universe import get_universe

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = "claude"

ARMS = {
    "A": {"label": "vanilla", "skill": None},
    "B": {"label": "community-wireshark", "skill": "skills/anthropic-official/SKILL.md"},
    "B2": {"label": "community-malware", "skill": "skills/community/B2-malware-traffic/SKILL.md"},
    "B3": {"label": "community-pcap", "skill": "skills/community/B3-pcap-analysis/SKILL.md"},
    "B4": {"label": "community-wireshark2", "skill": "skills/community/B4-wireshark-davila7/SKILL.md"},
    "C": {"label": "custom", "skill": "skills/custom/SKILL.clean.md"},
    "D1": {"label": "no-workflow", "skill": "skills/ablations/D1-no-workflow/SKILL.md"},
    "D2": {"label": "no-recipes", "skill": "skills/ablations/D2-no-recipes/SKILL.md"},
    "D3": {"label": "no-schema", "skill": "skills/ablations/D3-no-schema/SKILL.md"},
}

# Read-only local analysis only. No web, no writes, no file transfer.
ALLOWED_TOOLS = ["Bash", "Read", "Grep", "Glob", "BashOutput"]
DISALLOWED_TOOLS = [
    "WebFetch", "WebSearch", "Write", "Edit", "MultiEdit", "NotebookEdit",
    "Bash(curl:*)", "Bash(wget:*)", "Bash(nc:*)", "Bash(ncat:*)",
    "Bash(ssh:*)", "Bash(scp:*)", "Bash(git:*)",
]


def load_gt():
    return json.loads((ROOT / "harness" / "ground_truth.json").read_text())


def get_case(gt, case_id):
    c = next((c for c in gt["cases"] if c["id"] == case_id), None)
    if not c:
        raise ValueError(f"unknown case {case_id}")
    return c


def task_prompt(case):
    pcap = ROOT / case["pcap"]
    ev_dir = pcap.parent
    return f"""You are a network forensic analyst. Evidence from a suspected security \
incident is saved in this directory:

  {ev_dir}

The evidence includes a packet capture ({pcap.name}) and may include additional \
artifacts such as exported IDS/Suricata alerts. Review all evidence files in that \
directory. tshark is installed at /opt/homebrew/bin/tshark. The affected host is a \
Windows enterprise workstation on a local /24 LAN. Investigate and write a concise \
incident report. Your report must state:

  - The infected/victim host: its IPv4 address, MAC address, Windows hostname, and \
logged-in Windows user account.
  - The malware family (name it, and say whether attribution is signature-confirmed \
or behavioral).
  - All indicators of compromise you can ground in the traffic: command-and-control \
endpoints (IP:port), malicious domains, malicious URLs, and any transferred file names \
or SHA256 hashes.

Base every indicator on evidence you actually observe in the capture. Do not use the \
internet. When you finish, output the incident report as your final message."""


def resolve_system_prompt(arm):
    spec = ARMS[arm]
    if not spec["skill"]:
        return None
    p = ROOT / spec["skill"]
    if not p.exists():
        raise SystemExit(f"skill file missing for arm {arm}: {p}")
    return p.read_text()


def parse_stream(path):
    """Parse claude stream-json (one JSON object per line) into trajectory metrics."""
    final_text, tool_calls, tshark_cmds = "", 0, []
    usage = {}
    num_turns, duration_ms, cost = None, None, None
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls += 1
                    inp = block.get("input", {})
                    cmd = inp.get("command", "")
                    if "tshark" in cmd:
                        tshark_cmds.append(cmd)
        elif t == "result":
            final_text = ev.get("result", final_text) or final_text
            usage = ev.get("usage", {}) or {}
            num_turns = ev.get("num_turns")
            duration_ms = ev.get("duration_ms")
            cost = ev.get("total_cost_usd")
    return {
        "final_text": final_text,
        "tool_calls": tool_calls,
        "tshark_calls": len(tshark_cmds),
        "tshark_cmds": tshark_cmds,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "num_turns": num_turns,
        "duration_ms": duration_ms,
        "cost_usd": cost,
    }


def run(case_id, arm, model, max_turns=50, timeout=900, rep=1):
    gt = load_gt()
    case = get_case(gt, case_id)
    pcap = ROOT / case["pcap"]
    if not pcap.exists():
        raise SystemExit(f"pcap missing: {pcap}")

    run_id = f"{case_id}__{arm}__{model}__r{rep}"
    traj_dir = ROOT / "results" / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    stream_path = traj_dir / f"{run_id}.stream.jsonl"

    cmd = [
        CLAUDE, "-p", task_prompt(case),
        "--output-format", "stream-json", "--verbose",
        "--model", model,
        "--permission-mode", "bypassPermissions",
        "--max-turns", str(max_turns),
        "--add-dir", str(pcap.parent),
        "--allowedTools", *ALLOWED_TOOLS,
        "--disallowedTools", *DISALLOWED_TOOLS,
    ]
    sysprompt = resolve_system_prompt(arm)
    if sysprompt:
        cmd += ["--append-system-prompt", sysprompt]

    t0 = time.time()
    with open(stream_path, "w") as out:
        proc = subprocess.run(cmd, stdout=out, stderr=subprocess.PIPE,
                              text=True, timeout=timeout, cwd=str(ROOT))
    wall = time.time() - t0
    if proc.returncode != 0:
        print(f"  [warn] claude exit {proc.returncode}: {proc.stderr[:300]}")

    traj = parse_stream(stream_path)
    traj["wall_time_s"] = round(wall, 1)
    uni = get_universe(case_id, str(pcap))
    sc = score(traj["final_text"], case, uni)

    record = {
        "run_id": run_id, "case": case_id, "arm": arm,
        "arm_label": ARMS[arm]["label"], "model": model, "rep": rep,
        "returncode": proc.returncode,
        "trajectory": {k: v for k, v in traj.items() if k != "final_text"},
        "score": sc,
        "final_text": traj["final_text"],
    }
    res_path = ROOT / "results" / f"{run_id}.json"
    res_path.write_text(json.dumps(record, indent=2))

    print(f"  {run_id}: recall={sc['recall']} victim={sc['victim_correct']}/{sc['victim_total']} "
          f"family={sc['family_correct']} halluc={sc['hallucination_count']} "
          f"tshark={traj['tshark_calls']} tools={traj['tool_calls']} "
          f"out_tok={traj['output_tokens']} wall={traj['wall_time_s']}s")
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--arm", required=True, choices=list(ARMS))
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--max-turns", type=int, default=50)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--rep", type=int, default=1)
    a = ap.parse_args()
    run(a.case, a.arm, a.model, a.max_turns, a.timeout, a.rep)


if __name__ == "__main__":
    main()
