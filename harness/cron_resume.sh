#!/usr/bin/env bash
# Self-healing overnight collector for the clean-epoch Sonnet re-run.
# Launched ONCE, detached. It loops: attempt all missing runs, and if a rate-limit
# wall is hit, sleep an hour and retry, until all 243 valid runs exist. Then it
# writes a DONE marker and exits. A single-instance lock stops duplicate workers.
#
# It intentionally does NOT regenerate tables or the paper: the fresh 3-rep numbers
# differ from the hardcoded prose, and reconciling that needs the agent, not a script.
set -uo pipefail
export PATH="/Users/yaakulyasabbani/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="/Users/yaakulyasabbani/Documents/GitHub/latex_researchpapers/Skill_Issue_LLM_PCAP_Forensics"
cd "$ROOT"
LOG="$ROOT/results/cron.log"
LOCK="$ROOT/results/.cron.lock"
DONE="$ROOT/results/CLEAN_EPOCH_DONE"
TARGET=243   # 9 arms x 9 cases x 3 reps
MAX_ITERS=48 # safety: at most ~48 hourly passes (~2 days) then give up
CASES="mta-2024-07-30 mta-2024-09-04 mta-2024-11-26 mta-2025-01-22 mta-2024-08-15 \
mta-2022-01-07 mta-2021-09-10 mta-2026-01-31 mta-2026-02-28"
ARMS="A B B2 B3 B4 C D1 D2 D3"

log(){ echo "[$(date '+%m-%d %H:%M:%S')] $*" >> "$LOG"; }

[ -f "$DONE" ] && { log "DONE already present; worker exits"; exit 0; }

# single-instance lock (mkdir is atomic). A lock whose worker died is cleared after 3h.
if ! mkdir "$LOCK" 2>/dev/null; then
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +180 2>/dev/null)" ]; then
    log "stale lock (>3h) cleared"; rm -rf "$LOCK"; mkdir "$LOCK" 2>/dev/null || exit 0
  else
    log "another worker holds the lock; exit"; exit 0
  fi
fi
trap 'rm -rf "$LOCK"' EXIT
echo "$$" > "$LOCK/pid"

source "$ROOT/.venv/bin/activate" 2>/dev/null || true

valid_count(){
python3 - <<'PY'
import json,glob
n=0
for f in glob.glob("results/*__sonnet__*.json"):
    try:
        d=json.load(open(f))
        if d.get("returncode")==0 and (d.get("final_text") or "").strip(): n+=1
    except Exception: pass
print(n)
PY
}

log "worker started (pid $$); target $TARGET valid Sonnet runs"
iter=0
while [ "$iter" -lt "$MAX_ITERS" ]; do
  iter=$((iter+1))
  before=$(valid_count)
  if [ "$before" -ge "$TARGET" ]; then break; fi
  log "pass $iter: $before/$TARGET valid; attempting missing runs"
  # caffeinate keeps the Mac awake for the duration of the pass; circuit breaker
  # stops the pass after 4 consecutive failures (a rate-limit wall) so we sleep+retry.
  caffeinate -ims python3 harness/run_matrix.py --cases $CASES --arms $ARMS \
    --model sonnet --reps 3 --stop-after-failures 4 >> "$LOG" 2>&1
  after=$(valid_count)
  log "pass $iter done: $after/$TARGET valid (was $before)"
  if [ "$after" -ge "$TARGET" ]; then break; fi
  if [ "$after" -le "$before" ]; then
    log "no progress this pass (likely rate-limited); sleeping 1h before retry"
    caffeinate -ims sleep 3600
  fi
done

final=$(valid_count)
if [ "$final" -ge "$TARGET" ]; then
  touch "$DONE"
  log "COLLECTION COMPLETE: $final/$TARGET valid. DONE marker written; awaiting agent to reconcile paper."
else
  log "worker stopping after $iter passes at $final/$TARGET valid (hit MAX_ITERS or gave up)."
fi
