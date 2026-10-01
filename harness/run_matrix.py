#!/usr/bin/env python3
"""Serial driver: run a set of arms over a set of cases, one claude process at a time
(memory-bounded). Writes/updates results/summary.csv."""
import argparse
import csv
import json
import sys
from pathlib import Path

from experiment import run, ARMS, load_gt

ROOT = Path(__file__).resolve().parent.parent


def is_valid_result(path):
    """A run counts as done only if it exited cleanly with a non-empty report.
    Rate-limited/failed runs write a JSON with returncode!=0 or empty text; those
    must be re-attempted, otherwise an hourly retry loop can never heal them."""
    try:
        d = json.loads(path.read_text())
    except Exception:
        return False
    return d.get("returncode") == 0 and bool((d.get("final_text") or "").strip())


def append_summary(rec):
    path = ROOT / "results" / "summary.csv"
    new = not path.exists()
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["run_id", "case", "arm", "arm_label", "model", "rep",
                        "recall", "iocs_found", "iocs_total", "victim_correct",
                        "victim_total", "family_correct", "hallucination_count",
                        "hallucination_rate", "tshark_calls", "tool_calls",
                        "output_tokens", "num_turns", "wall_time_s", "returncode"])
        s, t = rec["score"], rec["trajectory"]
        w.writerow([rec["run_id"], rec["case"], rec["arm"], rec["arm_label"],
                    rec["model"], rec["rep"], s["recall"], s["iocs_found"],
                    s["iocs_total"], s["victim_correct"], s["victim_total"],
                    s["family_correct"], s["hallucination_count"],
                    s["hallucination_rate"], t["tshark_calls"], t["tool_calls"],
                    t["output_tokens"], t["num_turns"], t["wall_time_s"],
                    rec["returncode"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="+", required=True)
    ap.add_argument("--arms", nargs="+", default=list(ARMS))
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--max-turns", type=int, default=50)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--stop-after-failures", type=int, default=0,
                    help="stop the pass after N consecutive failed/invalid runs "
                         "(likely a rate-limit wall); 0 disables")
    a = ap.parse_args()

    total = len(a.cases) * len(a.arms) * a.reps
    n = 0
    executed = 0
    consec_fail = 0
    for case in a.cases:
        for rep in range(1, a.reps + 1):
            for arm in a.arms:
                n += 1
                if a.limit and executed >= a.limit:
                    print(f"batch limit {a.limit} reached; stopping", flush=True)
                    print("matrix complete", flush=True)
                    return
                run_id = f"{case}__{arm}__{a.model}__r{rep}"
                existing = ROOT / "results" / f"{run_id}.json"
                if existing.exists():
                    if is_valid_result(existing):
                        continue
                    existing.unlink()  # invalid (rate-limited/failed) -> redo
                print(f"[{n}/{total}] case={case} arm={arm} rep={rep}", flush=True)
                try:
                    rec = run(case, arm, a.model, a.max_turns, a.timeout, rep)
                    append_summary(rec)
                    executed += 1
                    ok = rec["returncode"] == 0 and bool((rec.get("final_text") or "").strip())
                    consec_fail = 0 if ok else consec_fail + 1
                except Exception as e:
                    print(f"  [FAIL] {case}/{arm}/r{rep}: {e}", file=sys.stderr, flush=True)
                    consec_fail += 1
                if a.stop_after_failures and consec_fail >= a.stop_after_failures:
                    print(f"circuit breaker: {consec_fail} consecutive failures "
                          f"(likely rate-limited); stopping pass", flush=True)
                    print("matrix complete", flush=True)
                    return
    print("matrix complete", flush=True)


if __name__ == "__main__":
    main()
