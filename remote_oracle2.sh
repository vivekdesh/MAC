#!/bin/bash

# --- Configuration for Oracle 2 VM ---
REMOTE_CONN="ubuntu@155.248.244.211"
KEY_FILE="$HOME/ICICI_Direct/Key/oracle2/ssh-key-2026-02-11.key"
REMOTE_BASE_DIR="/home/ubuntu"
KILL_WHATSAPP="$REMOTE_BASE_DIR/kill_whatsapp_google.sh"
SESSIONS_LIST="whatsapp rokde"

# --- TMUX HEALTH SCRIPT ---
TMUX_HEALTH_CMD=' 
sessions="'"$SESSIONS_LIST"'"

echo "================ TMUX PROCESS HEALTH (ORACLE 2) ================"
for s in $sessions; do
  if tmux has-session -t "$s" 2>/dev/null; then
    echo "Session: $s"

    tmux list-panes -t "$s" -F "#{pane_index} #{pane_pid}" | \
    while read -r pane ppid; do

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
find whatsapp -maxdepth 2 -name "*.log" -exec ls -lh {} + 2>/dev/null | awk "{print \$5, \$9}"
echo "============================================================"
'

usage() {
    echo "Usage: $0 [command] [args]"
    echo "Commands:"
    echo "  status               Check running processes and tmux sessions"
    echo "  restart wa [y|n]     Restart WhatsApp Bot"
    echo "  kill <session|all>   Kill specific tmux session or all"
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
        echo "🔍 Checking STATUS on Oracle 2 VM..."
        execute_remote "$TMUX_HEALTH_CMD"
        ;;
    "restart")
        CLEAR_LOGS=${ARG3:-n}
        if [[ "$ARG2" == "wa" || "$ARG2" == "whatsapp" ]]; then
            echo "🔄 Restarting WhatsApp Bot on Oracle 2 VM..."
            execute_remote "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $KILL_WHATSAPP"
        else
            echo "❌ Unknown project for restart: $ARG2"
            usage
        fi
        ;;
    "kill")
        SESSION_NAME=$ARG2
        if [ -z "$SESSION_NAME" ]; then
            echo "❌ Error: Please provide a session name or 'all'."
            usage
        fi

        if [ "$SESSION_NAME" == "all" ]; then
            echo "🔪 Killing ALL tmux sessions on Oracle 2 VM..."
            for s in $SESSIONS_LIST; do
                echo "   -> Killing $s"
                execute_remote "tmux kill-session -t $s 2>/dev/null || echo '      $s not found'"
            done
        else
            echo "🔪 Killing tmux session '$SESSION_NAME' on Oracle 2 VM..."
            execute_remote "tmux kill-session -t $SESSION_NAME"
        fi
        ;;
    *)
        usage
        ;;
esac
