#!/usr/bin/env bash
# Overnight clean-epoch Sonnet re-run. Fixes the epoch confound by collecting all
# nine arms in one tight timeframe. Idempotent + resumable: run once per night,
# raising REPS each night (night 1 -> REPS=1, night 2 -> REPS=2, night 3 -> REPS=3).
# Already-completed runs are skipped, so re-invoking after a rate-limit stop just
# continues where it left off.
#
# Usage:  bash harness/run_night.sh <REPS>
# Example (night 1):  bash harness/run_night.sh 1
set -euo pipefail
cd "$(dirname "$0")/.."
REPS="${1:?usage: run_night.sh <REPS>}"

CASES="mta-2024-07-30 mta-2024-09-04 mta-2024-11-26 mta-2025-01-22 mta-2024-08-15 \
mta-2022-01-07 mta-2021-09-10 mta-2026-01-31 mta-2026-02-28"
ARMS="A B B2 B3 B4 C D1 D2 D3"
ARCHIVE="results/archive_epoch_original"

# --- One-time: preserve the original (weeks-apart) Sonnet epoch, then clear it so
#     run_matrix does not skip the fresh batch. Haiku data is untouched. ---
if [ ! -d "$ARCHIVE" ]; then
  echo "[$(date '+%H:%M:%S')] archiving original Sonnet epoch -> $ARCHIVE"
  mkdir -p "$ARCHIVE/trajectories"
  # move sonnet result JSONs and their trajectories aside (keep haiku in place)
  for f in results/*__sonnet__*.json; do [ -e "$f" ] && mv "$f" "$ARCHIVE/"; done
  for f in results/trajectories/*__sonnet__*; do [ -e "$f" ] && mv "$f" "$ARCHIVE/trajectories/"; done
  cp results/summary.csv "$ARCHIVE/summary.csv" 2>/dev/null || true
  # rebuild summary.csv from the remaining (haiku) JSONs so it has no stale sonnet rows
  python3 - <<'PY'
import json,glob,csv
from pathlib import Path
ROOT=Path(".").resolve()
hdr=["run_id","case","arm","arm_label","model","rep","recall","iocs_found","iocs_total",
     "victim_correct","victim_total","family_correct","hallucination_count","hallucination_rate",
     "tshark_calls","tool_calls","output_tokens","num_turns","wall_time_s","returncode"]
rows=[]
for fp in glob.glob("results/*.json"):
    d=json.load(open(fp)); s=d["score"]; t=d["trajectory"]
    rows.append([d["run_id"],d["case"],d["arm"],d["arm_label"],d["model"],d["rep"],
        s["recall"],s["iocs_found"],s["iocs_total"],s["victim_correct"],s["victim_total"],
        s["family_correct"],s["hallucination_count"],s["hallucination_rate"],
        t["tshark_calls"],t["tool_calls"],t["output_tokens"],t["num_turns"],t["wall_time_s"],d["returncode"]])
rows.sort(key=lambda r:r[0])
with open("results/summary.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(hdr); w.writerows(rows)
print(f"summary.csv rebuilt to {len(rows)} non-sonnet rows")
PY
else
  echo "[$(date '+%H:%M:%S')] archive exists; continuing fresh epoch (resumable)"
fi

echo "[$(date '+%H:%M:%S')] launching Sonnet matrix: 9 arms x 9 cases x REPS=$REPS"
python3 harness/run_matrix.py --cases $CASES --arms $ARMS --model sonnet --reps "$REPS"
echo "[$(date '+%H:%M:%S')] matrix invocation returned (idempotent; safe to re-run)"
