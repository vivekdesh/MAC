#!/bin/bash
# ==============================================================================
# Daily Spare Token Runner for macOS launchd
# Location: /Users/vivek/ICICI_Direct/MAC/run_spare_token.sh
# Runs: update_spare_credentials.py (with 120s timeout guard) + dual-file sync
# ==============================================================================

LOG_FILE="/Users/vivek/Documents/nifty/data/index_options/credentials.nosync/spare_token_run.log"
PYTHON_BIN="/opt/homebrew/opt/python@3.13/bin/python3"
SCRIPT_PATH="/Users/vivek/Documents/nifty/data/index_options/credentials.nosync/update_spare_credentials.py"
BACKUP_JSON="/Users/vivek/Documents/nifty/data/index_options/credentials.nosync/spare_credentials.json"
LIVE_JSON="/Users/vivek/Documents/nifty/data/index_temp.nosync/spare_credentials.json"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Auto-trim log if exceeds 5000 lines
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE" 2>/dev/null)" -gt 5000 ]; then
    tail -n 2000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

log "[START] Triggered spare_token execution."

# 1. Wait for active internet connection (up to 60s) when waking from sleep
MAX_WAIT=60
WAITED=0
while ! /sbin/ping -q -c 1 -W 1 8.8.8.8 >/dev/null 2>&1; do
    sleep 2
    WAITED=$((WAITED + 2))
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        log "[ERROR] Network not available after ${MAX_WAIT}s. Aborting."
        exit 1
    fi
done

if [ "$WAITED" -gt 0 ]; then
    log "[INFO] Network reconnected after ${WAITED}s."
fi

# 2. Execute update_spare_credentials.py with 120-second timeout guard
log "[INFO] Running Python updater (max 120s)..."
/usr/bin/timeout 120 "$PYTHON_BIN" "$SCRIPT_PATH" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    log "[ERROR] update_spare_credentials.py timed out after 120s and was killed."
elif [ $EXIT_CODE -eq 0 ]; then
    log "[SUCCESS] update_spare_credentials.py completed successfully."
    
    # 3. Sync to live index_temp.nosync copy
    if [ -f "$BACKUP_JSON" ] && [ -f "$LIVE_JSON" ]; then
        "$PYTHON_BIN" -c "
import json
import os

backup_file = '$BACKUP_JSON'
live_file = '$LIVE_JSON'

with open(backup_file, 'r', encoding='utf-8') as fb:
    tok = json.load(fb).get('session_token')

with open(live_file, 'r', encoding='utf-8') as fl:
    data = json.load(fl)

if tok and data.get('session_token') != tok:
    old_tok = data.get('session_token')
    data['session_token'] = tok
    with open(live_file, 'w', encoding='utf-8') as fl:
        json.dump(data, fl, indent=2)
    os.chmod(live_file, 0o600)
    print(f'[SYNC] Synced session_token: {old_tok} -> {tok} in {live_file}')
else:
    print(f'[SYNC] Live copy already has session_token = {tok}')
" >> "$LOG_FILE" 2>&1
    fi
else
    log "[ERROR] update_spare_credentials.py failed with exit code $EXIT_CODE."
fi

log "[END] Finished run."
