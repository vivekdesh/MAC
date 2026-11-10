#!/bin/bash
# ==============================================================================
# Daily Evening Tasks Runner (5:00 PM or immediate on wake)
# Runs: fetchopt (with 3m timeout guard), md.nb, md.bb_nb (in parallel)
# Location: /Users/vivek/ICICI_Direct/MAC/run_evening_tasks.sh
# ==============================================================================

LOG_FILE="/Users/vivek/Documents/nifty/logs/daily_evening_tasks.log"
PYTHON_BIN="/opt/homebrew/opt/python@3.13/bin/python3"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "[START] Triggered 5 PM evening scheduled tasks."

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

# 2. Step 1: fetchopt with 3-minute hard timeout guard
log "[TASK 1/3] Running fetchopt (max 180s)..."
/usr/bin/timeout 180 "$PYTHON_BIN" /Users/vivek/ICICI_Direct/data_extraction/extract_option_data.py \
    --bot mod_rsi,sensex,selling >> "$LOG_FILE" 2>&1
EXIT_FETCHOPT=$?

if [ $EXIT_FETCHOPT -eq 124 ]; then
    log "[WARNING] fetchopt timed out after 180s and was killed. Proceeding to market data bots."
else
    log "[TASK 1/3] fetchopt finished with exit code $EXIT_FETCHOPT."
fi

# 3. Step 2: md.nb (Market Data Bot for Indian Indices - background parallel)
log "[TASK 2/3] Spawning md.nb (run_market_data_bot_background.sh)..."
bash /Users/vivek/Documents/nifty/market_data_bot/run_market_data_bot_background.sh >> "$LOG_FILE" 2>&1
EXIT_MD=$?
log "[TASK 2/3] md.nb initiated with exit code $EXIT_MD."

# 4. Step 3: md.bb_nb (Binance Market Data Bot --no-backup - background parallel)
log "[TASK 3/3] Spawning md.bb_nb (run_binance_market_data_bot_background.sh --no-backup)..."
bash /Users/vivek/ICICI_Direct/binance/market_data_bot/run_binance_market_data_bot_background.sh --no-backup >> "$LOG_FILE" 2>&1
EXIT_BINANCE=$?
log "[TASK 3/3] md.bb_nb initiated with exit code $EXIT_BINANCE."

log "[END] All 5 PM evening tasks triggered successfully."
