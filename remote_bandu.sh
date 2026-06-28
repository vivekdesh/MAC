#!/bin/bash

# --- Configuration for Bandu (Vinay) ---
REMOTE_CONN="vivek@35.196.102.57"
KEY_FILE="$HOME/.ssh/gcp_key"

# Remote Paths
REMOTE_HOME="/home/vivek"
KILL_RSI="$REMOTE_HOME/mod_rsi/kill_rsi_google.sh"
KILL_SELL_1="$REMOTE_HOME/selling_1/kill_sell_second_google.sh"

# TMUX Setup script - assuming it's in mod_rsi
SETUP_SCRIPT="$REMOTE_HOME/mod_rsi/create_TMUX.sh"

# SESSIONS_LIST for `kill all` command
SESSIONS_LIST="rsi_trade rsi_sin sell_1_trade sell_1_sin"

# --- TMUX HEALTH SCRIPT ---
TMUX_HEALTH_CMD=' 
sessions="'"$SESSIONS_LIST"'"

echo "================ TMUX PROCESS HEALTH (BANDU) ================"
for s in $sessions; do
  if tmux has-session -t "$s" 2>/dev/null; then
    echo "Session: $s"

    tmux list-panes -t "$s" -F "#{pane_index} #{pane_pid}" | \
    while read -r pane ppid; do

      # Find child process (actual running program)
      child=$(pgrep -P "$ppid" | head -n 1)

      if [[ -z "$child" ]]; then
        echo "  Pane $pane | PID $ppid"
        echo "    ⚠ DEAD or IDLE (shell only)"
      else
        cmd=$(ps -o cmd= -p "$child")
        echo "  Pane $pane | Shell PID $ppid"
        echo "    ▶ Program PID $child"
        echo "    ▶ Program CMD: $cmd"
      fi

    done
  else
    echo "Session: $s ❌ NOT RUNNING"
  fi
done

echo ""
echo "--- LOG FILE SIZES ---"
find mod_rsi selling_1 -maxdepth 2 -name "*.log" -exec ls -lh {} + 2>/dev/null | awk "{print \$5, \$9}"
echo "============================================================"
'

usage() {
    echo "Usage: $0 [command] [args]"
    echo "Commands:"
    echo "  status               Check running processes (tmux & python)"
    echo "  restart rsi [y|n]    Restart RSI Algo"
    echo "  restart sell_1 [y|n] Restart Selling_1 Algo"
    echo "  restart all [y|n]    Restart both Algos"
    echo "  setup                Run tmux setup script (create_TMUX.sh)"
    echo "  kill <session>|all   Kill a specific tmux session or 'all'"
    exit 1
}

if [ -z "$1" ]; then usage; fi

COMMAND=$1
SUB_CMD=$2
ARG3=$3

case "$COMMAND" in
    "status")
        echo "🔍 STATUS check on Bandu..."
        ssh -i "$KEY_FILE" "$REMOTE_CONN" "$TMUX_HEALTH_CMD"
        ;;
    "restart")
        CLEAR_LOGS=${ARG3:-n}
        
        if [[ "$SUB_CMD" == "all" ]]; then
            echo "🔄 REMOTE RESTART: all on Bandu..."
            echo "--- Restarting RSI ---"
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\n' | bash $KILL_RSI"
            echo "--- Restarting Selling_1 ---"
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\n' | bash $KILL_SELL_1"
        else
            TARGET_SCRIPT=""
            case "$SUB_CMD" in
                "rsi") TARGET_SCRIPT="$KILL_RSI" ;;
                "sell_1") TARGET_SCRIPT="$KILL_SELL_1" ;;
                *) echo "❌ Invalid restart target: $SUB_CMD"; usage ;;
            esac

            echo "🔄 REMOTE RESTART: $SUB_CMD on Bandu..."
            # We pipe inputs to the interactive script:
            # 1. Clear logs? ($CLEAR_LOGS)
            # 2. Start script 1? (y)
            # 3. Start script 2? (y)
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\n' | bash $TARGET_SCRIPT"
        fi
        ;;
    "setup")
        echo "🛠️ Running Tmux Setup (create_TMUX.sh)..."
        ssh -i "$KEY_FILE" "$REMOTE_CONN" "bash $SETUP_SCRIPT"
        ;;
    "kill")
        SESSION_NAME=$SUB_CMD
        if [ -z "$SESSION_NAME" ]; then
            echo "❌ Error: Please provide a session name or 'all'."
            echo "Usage: $0 kill <session_name|all>"
            exit 1
        fi

        if [ "$SESSION_NAME" == "all" ]; then
            echo "🔪 Killing ALL tmux sessions on Bandu..."
            for s in $SESSIONS_LIST; do
                echo "   -> Killing $s"
                ssh -i "$KEY_FILE" "$REMOTE_CONN" "tmux kill-session -t $s 2>/dev/null || echo '      $s not found'"
            done
        else
            echo "🔪 Killing tmux session '$SESSION_NAME' on Bandu..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "tmux kill-session -t $SESSION_NAME"
        fi
        ;;
    *)
        usage
        ;;
esac
