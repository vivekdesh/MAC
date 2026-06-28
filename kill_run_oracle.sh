#!/bin/bash
# Unified Restart Script for Oracle VM Projects
# Location: /home/ubuntu/kill_run_oracle.sh

PROJECT=$1
CLEAR_LOGS=$2
BASE_DIR="/home/ubuntu"

if [ -z "$PROJECT" ]; then
    echo "Usage: $0 <mod_rsi|retire|selling_1|sensex> [clear_logs:y|n]"
    exit 1
fi

# Configuration Mapping
if [ "$PROJECT" == "mod_rsi" ]; then
    DIR_NAME="mod_rsi"
    PROC_GREP="mod_rsi"
    SESSION_SIN="rsi_sin"
    SESSION_TRADE="rsi_trade"
    TRADE_SCRIPT="vivek_RSI.py"
    SINGLE_SCRIPT="vivek_RSI_single.py"
    DISPLAY_NAME="MOD_RSI"
elif [ "$PROJECT" == "retire" ]; then
    DIR_NAME="retire"
    PROC_GREP="retire"
    SESSION_SIN="ret_sin"
    SESSION_TRADE="ret_trade"
    TRADE_SCRIPT="retire_vivek_trade.py"
    SINGLE_SCRIPT="retire_vivek_single.py"
    DISPLAY_NAME="RETIRE"
elif [ "$PROJECT" == "selling_1" ]; then
    DIR_NAME="selling_1"
    PROC_GREP="selling"
    SESSION_SIN="sell_1_sin"
    SESSION_TRADE="sell_1_trade"
    TRADE_SCRIPT="selling_vivek_trade.py"
    SINGLE_SCRIPT="selling_vivek_single.py"
    DISPLAY_NAME="SELLING_1"
elif [ "$PROJECT" == "sensex" ]; then
    DIR_NAME="sensex"
    PROC_GREP="sensex"
    SESSION_SIN="sen_sin"
    SESSION_TRADE="sen_trade"
    TRADE_SCRIPT="vivek_sensex.py"
    SINGLE_SCRIPT="vivek_sensex_single.py"
    DISPLAY_NAME="SENSEX"
else
    echo "❌ Unknown project: $PROJECT"
    exit 1
fi

SCRIPT_DIR="${BASE_DIR}/${DIR_NAME}"

echo "🔄 Initializing $DISPLAY_NAME Restart..."

# 1. Log Clearing
if [ "$CLEAR_LOGS" == "y" ]; then
    REPLY="y"
else
    # Only ask if not already forced via argument
    if [ -z "$CLEAR_LOGS" ]; then
        read -p "Do you want to clear the log files for $DISPLAY_NAME? (y/n) " -n 1 -r
        echo
    else
        REPLY="n"
    fi
fi

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Clearing log files for $DISPLAY_NAME..."
    [ -f "${SCRIPT_DIR}/app.log" ] && > "${SCRIPT_DIR}/app.log"
    [ -f "${SCRIPT_DIR}/app_single.log" ] && > "${SCRIPT_DIR}/app_single.log"
    if [ -d "${SCRIPT_DIR}/logs" ]; then
        echo "Clearing API log directory..."
        rm -f "${SCRIPT_DIR}/logs"/*.log
    fi
    echo "Log files have been cleared."
else
    echo "Log files not cleared."
fi

# 2. Kill Existing Processes
echo "Finding and killing '$PROC_GREP' processes..."
ps -ef | grep "$PROC_GREP" | grep -v "grep" | grep -v "tmux" | grep -v "kill_run_oracle.sh" | awk '{print $2}' | xargs -r kill -9
echo "'$PROC_GREP' processes have been cleared."

sleep 2

# 3. Manage Tmux Sessions
for s in "$SESSION_SIN" "$SESSION_TRADE"; do
    if ! tmux has-session -t "$s" 2>/dev/null; then
        tmux new-session -d -s "$s"
        echo "Tmux session '$s' created."
    fi
done

# 4. Start Scripts (Standardized using source activate)
# Trade Script
REPLY=""
read -t 3 -p "Start ${TRADE_SCRIPT}? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    tmux send-keys -t "$SESSION_TRADE" "clear" Enter
    tmux send-keys -t "$SESSION_TRADE" "source ${BASE_DIR}/myenv/bin/activate" Enter
    tmux send-keys -t "$SESSION_TRADE" "python ${SCRIPT_DIR}/${TRADE_SCRIPT}" Enter
    echo "Started ${TRADE_SCRIPT} in '$SESSION_TRADE'"
else
    echo "Skipped ${TRADE_SCRIPT}."
fi

# Single Script
REPLY=""
read -t 3 -p "Start ${SINGLE_SCRIPT}? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    tmux send-keys -t "$SESSION_SIN" "clear" Enter
    tmux send-keys -t "$SESSION_SIN" "source ${BASE_DIR}/myenv/bin/activate" Enter
    tmux send-keys -t "$SESSION_SIN" "python ${SCRIPT_DIR}/${SINGLE_SCRIPT}" Enter
    echo "Started ${SINGLE_SCRIPT} in '$SESSION_SIN'"
else
    echo "Skipped ${SINGLE_SCRIPT}."
fi

echo "✅ $DISPLAY_NAME Restart Complete."
sleep 1
