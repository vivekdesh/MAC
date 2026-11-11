#!/bin/bash
# ==============================================================================
# Daily Evening Tasks Runner (5:00 PM or immediate on wake)
# Runs: fetchopt (with 3m timeout guard), md.nb, md.bb_nb (with 15m watchdog + stale PID cleanup)
# Location: /Users/vivek/ICICI_Direct/MAC/run_evening_tasks.sh
# ==============================================================================

LOG_FILE="/Users/vivek/ICICI_Direct/logs/daily_evening_tasks.log"
PYTHON_BIN="/opt/homebrew/opt/python@3.13/bin/python3"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Auto-trim log if exceeds 5000 lines
if [ -f "$LOG_FILE" ] && [ "$(wc -l < "$LOG_FILE" 2>/dev/null)" -gt 5000 ]; then
    tail -n 2000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

# Helper: clean stale locks and processes from previous runs
clean_stale_pid() {
    local pid_file="$1"
    local bot_name="$2"
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file" 2>/dev/null)
        if [ -n "$old_pid" ] && ps -p "$old_pid" >/dev/null 2>&1; then
            log "[CLEANUP] Stale $bot_name running from previous day (PID: $old_pid). Terminating."
            kill -9 "$old_pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
    fi
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
log "[TASK 1/4] Running fetchopt (max 180s)..."
/usr/bin/timeout 180 "$PYTHON_BIN" /Users/vivek/ICICI_Direct/data_extraction/extract_option_data.py \
    --bot mod_rsi,sensex,selling >> "$LOG_FILE" 2>&1
EXIT_FETCHOPT=$?

if [ $EXIT_FETCHOPT -eq 124 ]; then
    log "[WARNING] fetchopt timed out after 180s and was killed. Proceeding to market data bots."
else
    log "[TASK 1/4] fetchopt finished with exit code $EXIT_FETCHOPT."
fi

# 3. Step 2: md.nb with stale cleanup + 15-minute watchdog (timeout 900)
log "[TASK 2/4] Spawning md.nb (max 15m runtime)..."
PID_NIFTY="/Users/vivek/ICICI_Direct/logs/market_data_bot.pid"
clean_stale_pid "$PID_NIFTY" "Market Data BOT"

(
    cd /Users/vivek/Documents/nifty || exit 1
    nohup /usr/bin/timeout 900 /Users/vivek/Documents/nifty/venv.nosync/bin/python \
        /Users/vivek/Documents/nifty/market_data_bot/market_data_bot.py \
        --symbols nifty,nifty_futures,banknifty,banknifty_futures,sensex,sensex_futures,indiavix \
        --append-latest \
        --rebuild-timeframes 1,3,5,10,15 \
        >> "/Users/vivek/ICICI_Direct/logs/market_data_bot_background.log" 2>&1 &
    echo $! > "$PID_NIFTY"
)
log "[TASK 2/4] md.nb initiated (PID: $(cat "$PID_NIFTY" 2>/dev/null))."

# 4. Step 3: md.bb_nb with stale cleanup + 15-minute watchdog (timeout 900)
log "[TASK 3/4] Spawning md.bb_nb (max 15m runtime)..."
PID_BINANCE="/Users/vivek/ICICI_Direct/logs/binance_market_data_bot.pid"
clean_stale_pid "$PID_BINANCE" "Binance Market Data BOT"

nohup /usr/bin/timeout 900 /opt/homebrew/opt/python@3.13/bin/python3 -u \
    /Users/vivek/ICICI_Direct/binance/market_data_bot/binance_market_data_bot.py \
    --symbols btc,eth,btc_futures,eth_futures \
    --append-latest \
    --rebuild-timeframes 1 \
    >> "/Users/vivek/ICICI_Direct/logs/binance_market_data_bot_background.log" 2>&1 &
BOT_PID_BINANCE=$!
echo "$BOT_PID_BINANCE" > "$PID_BINANCE"
log "[TASK 3/4] md.bb_nb initiated (PID: $BOT_PID_BINANCE)."

# 5. Step 4: all.d with 15-minute watchdog (timeout 900)
log "[TASK 4/4] Spawning all.d (max 15m runtime)..."
(
    cd /Users/vivek/ICICI_Direct/MAC || exit 1
    nohup /usr/bin/timeout 900 bash /Users/vivek/ICICI_Direct/MAC/sync_master.sh all_d \
        >> "/Users/vivek/ICICI_Direct/logs/all_d_background.log" 2>&1 &
    log "[TASK 4/4] all.d initiated (PID: $!)."
)

log "[END] All 5 PM evening tasks triggered successfully with watchdog protection."
