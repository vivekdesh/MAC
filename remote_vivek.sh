#!/bin/bash

# --- Configuration for Vivek (GCP) ---
REMOTE_CONN="deshpande_vivek@35.237.249.135"
KEY_FILE="$HOME/.ssh/gcp_key"

# Remote Paths
REMOTE_HOME="/home/deshpande_vivek"
KILL_RET="$REMOTE_HOME/kill_retire_google.sh"
KILL_SELL="$REMOTE_HOME/kill_selling_google.sh"
KILL_WHATSAPP="$REMOTE_HOME/kill_whatsapp_google.sh"
KILL_NIFTY="$REMOTE_HOME/kill_nifty_google.sh"
SETUP_SCRIPT="$REMOTE_HOME/create_TMS.sh"

usage() {
    echo "Usage: $0 [command] [sub-command/args]"
    echo "Commands:"
    echo "  status               Check Process Health (tmux_health)"
    echo "  restart ret [y|n]    Restart Retire Algo"
    echo "  restart sell [y|n]   Restart Selling Algo"
    echo "  restart wa [y|n]     Restart Whatsapp"
    echo "  restart nifty [y|n]  Restart Nifty Algo"
    echo "  restart all [y|n]    Restart EVERYTHING"
    echo "  setup                Run tmux setup (create_TMS.sh)"
    exit 1
}

if [ -z "$1" ]; then usage; fi

COMMAND=$1
SUB_CMD=$2
ARG3=$3

# Defined sessions list for reuse
SESSIONS_LIST="sell_sin sell_trade ret_trade ret_sin whatsapp rokde nifty_trade"

# --- TMUX HEALTH SCRIPT (EXACT ALIAS CODE) ---
TMUX_HEALTH_CMD=' 
sessions="'"$SESSIONS_LIST"'"

echo "================ TMUX PROCESS HEALTH ================"
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
find retire selling whatsapp -maxdepth 2 -name "*.log" -exec ls -lh {} + 2>/dev/null | awk "{print \$5, \$9}"
echo "===================================================="
'

case "$COMMAND" in
    "status")
        echo "🔍 Running tmux_health on Vivek (GCP)..."
        ssh -i "$KEY_FILE" "$REMOTE_CONN" "$TMUX_HEALTH_CMD"
        ;;
    "restart")
        CLEAR_LOGS=${ARG3:-n}

        if [[ "$SUB_CMD" == "all" ]]; then
            echo "🔄 REMOTE RESTART: all on Vivek..."
            
            echo "Executing retire kill script..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $KILL_RET"
            
            echo "Executing kill_sell_google.sh..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $KILL_SELL"

            echo "Executing kill_whatsapp_google.sh..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $KILL_WHATSAPP"

            echo "Executing kill_nifty_google.sh..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $KILL_NIFTY"

            echo "All kill scripts executed."
        else
            TARGET_SCRIPT=""
            case "$SUB_CMD" in
                "ret"|"retire") TARGET_SCRIPT="$KILL_RET" ;; 
                "sell") TARGET_SCRIPT="$KILL_SELL" ;; 
                "wa"|"whatsapp") TARGET_SCRIPT="$KILL_WHATSAPP" ;; 
                "nif"|"nifty") TARGET_SCRIPT="$KILL_NIFTY" ;;
                *) echo "❌ Invalid restart target: $SUB_CMD"; usage ;; 
            esac

            echo "🔄 REMOTE RESTART: $SUB_CMD on Vivek..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $TARGET_SCRIPT"
        fi
        ;;
    "setup")
        echo "🛠️ Running Tmux Setup (create_TMS.sh)..."
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
            echo "🔪 Killing ALL tmux sessions on Vivek (GCP)..."
            # Using the SESSIONS_LIST defined locally
            for s in $SESSIONS_LIST; do
                echo "   -> Killing $s"
                ssh -i "$KEY_FILE" "$REMOTE_CONN" "tmux kill-session -t $s 2>/dev/null || echo '      $s not found'"
            done
        else
            echo "🔪 Killing tmux session '$SESSION_NAME' on Vivek (GCP)..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "tmux kill-session -t $SESSION_NAME"
        fi
        ;; 
    *) 
        usage
        ;; 
esac
