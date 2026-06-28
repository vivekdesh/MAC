#!/bin/bash

# ==============================================================================
# 🚀 REMOTE ORACLE SCRIPT
# Manages remote operations for the Oracle VM (GCP instance)
# ==============================================================================

# --- Configuration for Oracle VM ---
REMOTE_CONN="ubuntu@80.225.215.187"
KEY_FILE="$HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key"
REMOTE_BASE_DIR="/home/ubuntu"
RESTART_BINANCE_SCRIPT="$REMOTE_BASE_DIR/binance/kill_run.sh"
UNIFIED_RESTART_SCRIPT="$REMOTE_BASE_DIR/kill_run_oracle.sh"
SETUP_SCRIPT="$REMOTE_BASE_DIR/create_TMS_oracle.sh"
# Defined sessions list for reuse
BINANCE_SESSION="bnc"
SESSIONS_LIST="rsi_trade rsi_sin sell_1_trade sell_1_sin sen_trade sen_sin $BINANCE_SESSION"

# --- TMUX HEALTH SCRIPT ---
TMUX_HEALTH_CMD=' 
sessions="'"$SESSIONS_LIST"'"

echo "================ TMUX PROCESS HEALTH (ORACLE) ================"
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
find mod_rsi selling_1 binance sensex -maxdepth 2 -name "*.log" -exec ls -lh {} + 2>/dev/null | awk "{print \$5, \$9}"
echo "============================================================"
'

usage() {
    echo "Usage: $0 [command] [args]"
    echo "Commands:"
    echo "  status         Check running processes and tmux sessions"
    echo "  restart <project_name> [clear_logs:y|n]"
    echo "                 clear_logs default: n"
    echo "  setup          Run tmux setup (create_TMS_oracle.sh)"
    echo "  kill <session> Kill a specific tmux session or 'all'"
    exit 1
}

if [ -z "$1" ]; then usage; fi

COMMAND=$1
ARG2=$2
ARG3=$3

execute_remote() {
    local remote_command="$1"
    ssh -i "$KEY_FILE" "$REMOTE_CONN" "$remote_command"
}

case "$COMMAND" in
    "status")
        echo "🔍 Checking STATUS on Oracle VM..."
        execute_remote "$TMUX_HEALTH_CMD"
        ;; 
    "restart")
        PROJECT_NAME=$ARG2
        CLEAR_LOGS=${ARG3:-n} # Default to 'n' if not provided
        PROJECT_KEY=""
        RESTART_SCRIPT=""

        if [ -z "$PROJECT_NAME" ]; then
            echo "❌ Error: Please provide a project name to restart (e.g., 'rsi', 'selling_1', 'sensex', or 'binance')."
            usage
        fi

        if [ "$PROJECT_NAME" == "binance" ]; then
            PROJECT_KEY="binance"
            RESTART_SCRIPT="$RESTART_BINANCE_SCRIPT"
        elif [[ "$PROJECT_NAME" == "rsi" || "$PROJECT_NAME" == "mod_rsi" ]]; then
            PROJECT_KEY="mod_rsi"
            RESTART_SCRIPT="$UNIFIED_RESTART_SCRIPT"
        elif [[ "$PROJECT_NAME" == "selling_1" ]]; then
            PROJECT_KEY="selling_1"
            RESTART_SCRIPT="$UNIFIED_RESTART_SCRIPT"
        elif [[ "$PROJECT_NAME" == "sensex" ]]; then
            PROJECT_KEY="sensex"
            RESTART_SCRIPT="$UNIFIED_RESTART_SCRIPT"
        else
            echo "❌ Unknown project for restart: $PROJECT_NAME"
            exit 1
        fi

        if ! execute_remote "[ -f \"$RESTART_SCRIPT\" ]"; then
            echo "❌ Restart script not found on Oracle VM: $RESTART_SCRIPT"
            exit 1
        fi
        
        # Pass the project name and the clear_logs flag to the script
        # The script handles the 'y/n' prompts internally, but we pipe y for the script starts
        echo "🔄 Restarting '$PROJECT_KEY' on Oracle VM..."
        execute_remote "printf 'y
y
' | bash $RESTART_SCRIPT $PROJECT_KEY $CLEAR_LOGS"
        ;; 
    "setup")
        echo "🛠️ Running Tmux Setup (create_TMS_oracle.sh)..."
        if ! execute_remote "[ -f \"$SETUP_SCRIPT\" ]"; then
            echo "❌ Setup script not found on Oracle VM: $SETUP_SCRIPT"
            exit 1
        fi
        execute_remote "bash $SETUP_SCRIPT"
        ;; 
    "kill")
        SESSION_NAME=$ARG2
        if [ -z "$SESSION_NAME" ]; then
            echo "❌ Error: Please provide a session name or 'all'."
            echo "Usage: $0 kill <session_name|all>"
            exit 1
        fi

        if [ "$SESSION_NAME" == "all" ]; then
            echo "🔪 Killing ALL tmux sessions on Oracle VM..."
            for s in $SESSIONS_LIST; do
                echo "   -> Killing $s"
                execute_remote "tmux kill-session -t $s 2>/dev/null || echo '      $s not found'"
            done
        else
            echo "🔪 Killing tmux session '$SESSION_NAME' on Oracle VM..."
            execute_remote "tmux kill-session -t $SESSION_NAME"
        fi
        ;;
    *)
        usage
        ;; 
esac
