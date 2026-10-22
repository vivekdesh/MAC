#!/bin/zsh
# Daily what-if: P&L if Momentum_Extreme_Break_enabled had been 1 (nifty + retire).
# Run in the evening, AFTER /Users/vivek/Documents/nifty/data/clean.nosync is updated and
# the VM logs are downloaded (v.d / o.d), so today's bars and logs are present.
#
#   ./run_daily.sh                 refresh sheets, validate, print daily + cumulative table
#   ./run_daily.sh --no-refresh    reuse the CSVs already in ./sheets/
set -e
cd "${0:A:h}"
mkdir -p results
stamp=$(date +%Y-%m-%d)
out="results/run_${stamp}.txt"

if [[ "$1" != "--no-refresh" ]]; then
  echo "== 1/4 refresh sheets (read-only, 6 reads)"
  python3 -I refresh_sheets.py
fi

{
  echo "== 2/4 gate replay vs bot logs (must end: VALIDATION CLEAN)"
  python3 validate.py 2>&1 | grep -E "########|bars checked|informational|VALIDATION|^ +[0-9]{4}-" || true
  echo
  echo "== 3/4 exit simulator vs every real chain on clean-data days (22-10-2026 baseline: nifty +18.6%, retire -3.7%)"
  python3 validate_sim.py nifty,retire 2>&1 | grep -E "=====|TOTAL|excluded"
  echo
  echo "== 4/4 flag=1 timeline from 01-10-2026 13:20 to today"
  python3 engine2.py nifty,retire "01-10-2026 13:20" "$(date +%d-%m-%Y) 15:30" 2>&1 \
    | grep -v -E "DeprecationWarning|from py_vollib"
} | tee "$out"

echo
echo "saved: $PWD/$out"
