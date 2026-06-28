#!/bin/bash

# --- Test Configuration for Suresh ---
REMOTE_CONN="ubuntu@140.245.15.195"
KEY_FILE="$HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key"
REMOTE_DIR="/home/ubuntu/mod_rsi"
RESTART_SCRIPT="$REMOTE_DIR/kill_rsi_sur.sh"
SETUP_SCRIPT="$REMOTE_DIR/create_TMX_sur.sh"
SESSIONS_LIST="rsi_trade rsi_sin sen_trade sen_sin"

# --- TMUX HEALTH SCRIPT ---
TMUX_HEALTH_CMD=' 
sessions="'"$SESSIONS_LIST"'"

echo "================ TMUX PROCESS HEALTH (SURESH) ================"
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
find mod_rsi sensex_suresh -maxdepth 2 -name "*.log" -exec ls -lh {} + 2>/dev/null | awk "{print \$5, \$9}"
echo "============================================================"
'

usage() {
    echo "Usage: $0 [command] [args]"
    echo "Commands:"
    echo "  status         Check running processes"
    echo "  restart [project:all|mod_rsi|sensex] [y|n]"
    echo "                 If project omitted, defaults to 'all'"
    echo "                 If clear_logs omitted, defaults to 'n'"
    echo "  setup          Run tmux setup script (create_TMX_sur.sh)"
    echo "  kill <session> Kill a specific tmux session or 'all'"
    exit 1
}

if [ -z "$1" ]; then usage; fi

COMMAND=$1
ARG2=$2

case "$COMMAND" in
    "status")
        echo "🔍 Testing STATUS check on Suresh..."
        ssh -i "$KEY_FILE" "$REMOTE_CONN" "$TMUX_HEALTH_CMD"
        ;; 
    "restart")
        PROJECT_NAME="all"
        CLEAR_LOGS="n"

        if [[ "$ARG2" == "y" || "$ARG2" == "n" || -z "$ARG2" ]]; then
            CLEAR_LOGS=${ARG2:-n}
        else
            PROJECT_NAME="$ARG2"
            CLEAR_LOGS=${ARG3:-n}
        fi
        
        echo "🔄 Testing REMOTE RESTART on Suresh..."
        echo "   Project: $PROJECT_NAME"
        echo "   Clear Logs: $CLEAR_LOGS"
        
        if [[ "$PROJECT_NAME" == "all" ]]; then
            echo "   Start Scripts: Yes (Auto-confirmed for RSI + Sensex)"
            # The remote script prompts for log clear and start confirmations.
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "printf '$CLEAR_LOGS\ny\ny\ny\ny\n' | bash $RESTART_SCRIPT"
        elif [[ "$PROJECT_NAME" == "mod_rsi" || "$PROJECT_NAME" == "rsi" ]]; then
            echo "   Start Scripts: Yes (Auto-confirmed for MOD_RSI only)"
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "
                MOD_RSI_DIR=/home/ubuntu/mod_rsi
                if [[ \"$CLEAR_LOGS\" == \"y\" ]]; then
                    echo 'Clearing log files for MOD_RSI...'
                    [ -f \"\$MOD_RSI_DIR/app.log\" ] && > \"\$MOD_RSI_DIR/app.log\"
                    [ -f \"\$MOD_RSI_DIR/app_single.log\" ] && > \"\$MOD_RSI_DIR/app_single.log\"
                    if [ -d \"\$MOD_RSI_DIR/logs\" ]; then
                        echo 'Clearing MOD_RSI API log directory...'
                        rm -f \"\$MOD_RSI_DIR\"/logs/*.log
                    fi
                    echo 'Log files have been cleared.'
                else
                    echo 'Log files not cleared.'
                fi

                echo \"Recreating MOD_RSI tmux sessions...\"
                tmux kill-session -t rsi_trade 2>/dev/null || true
                tmux kill-session -t rsi_sin 2>/dev/null || true
                sleep 2

                tmux new-session -d -s rsi_trade
                tmux new-session -d -s rsi_sin

                tmux send-keys -t rsi_trade 'clear' Enter
                tmux send-keys -t rsi_trade 'source ~/venv/bin/activate' Enter
                tmux send-keys -t rsi_trade 'cd /home/ubuntu/mod_rsi' Enter
                tmux send-keys -t rsi_trade 'python /home/ubuntu/mod_rsi/vivek_RSI.py' Enter
                echo \"Started vivek_RSI.py in 'rsi_trade'\"

                tmux send-keys -t rsi_sin 'clear' Enter
                tmux send-keys -t rsi_sin 'source ~/venv/bin/activate' Enter
                tmux send-keys -t rsi_sin 'cd /home/ubuntu/mod_rsi' Enter
                tmux send-keys -t rsi_sin 'python /home/ubuntu/mod_rsi/vivek_RSI_single.py' Enter
                echo \"Started vivek_RSI_single.py in 'rsi_sin'\"
            "
        elif [[ "$PROJECT_NAME" == "sensex" ]]; then
            echo "   Start Scripts: Yes (Auto-confirmed for Sensex only)"
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "
                SENSEX_DIR=/home/ubuntu/sensex_suresh
                if [[ \"$CLEAR_LOGS\" == \"y\" ]]; then
                    echo 'Clearing log files for SENSEX...'
                    [ -f \"\$SENSEX_DIR/app.log\" ] && > \"\$SENSEX_DIR/app.log\"
                    [ -f \"\$SENSEX_DIR/app_single.log\" ] && > \"\$SENSEX_DIR/app_single.log\"
                    if [ -d \"\$SENSEX_DIR/logs\" ]; then
                        echo 'Clearing Sensex API log directory...'
                        rm -f \"\$SENSEX_DIR\"/logs/*.log
                    fi
                    echo 'Log files have been cleared.'
                else
                    echo 'Log files not cleared.'
                fi

                echo \"Recreating Sensex tmux sessions...\"
                tmux kill-session -t sen_trade 2>/dev/null || true
                tmux kill-session -t sen_sin 2>/dev/null || true
                sleep 2

                tmux new-session -d -s sen_trade
                tmux new-session -d -s sen_sin

                tmux send-keys -t sen_trade 'clear' Enter
                tmux send-keys -t sen_trade 'source ~/venv/bin/activate' Enter
                tmux send-keys -t sen_trade 'cd /home/ubuntu/sensex_suresh' Enter
                tmux send-keys -t sen_trade 'python /home/ubuntu/sensex_suresh/vivek_sensex.py' Enter
                echo \"Started vivek_sensex.py in 'sen_trade'\"

                tmux send-keys -t sen_sin 'clear' Enter
                tmux send-keys -t sen_sin 'source ~/venv/bin/activate' Enter
                tmux send-keys -t sen_sin 'cd /home/ubuntu/sensex_suresh' Enter
                tmux send-keys -t sen_sin 'python /home/ubuntu/sensex_suresh/vivek_sensex_single.py' Enter
                echo \"Started vivek_sensex_single.py in 'sen_sin'\"
            "
        else
            echo "❌ Unknown project for restart: $PROJECT_NAME"
            exit 1
        fi
        ;; 
    "setup")
        echo "🛠️ Running Tmux Setup (create_TMX_sur.sh)..."
        ssh -i "$KEY_FILE" "$REMOTE_CONN" "bash $SETUP_SCRIPT"
        ;; 
    "kill")
        SESSION_NAME=$ARG2
        if [ -z "$SESSION_NAME" ]; then
            echo "❌ Error: Please provide a session name or 'all'."
            echo "Usage: $0 kill <session_name|all>"
            exit 1
        fi

        if [ "$SESSION_NAME" == "all" ]; then
            echo "🔪 Killing ALL tmux sessions on Suresh..."
            for s in $SESSIONS_LIST; do
                echo "   -> Killing $s"
                ssh -i "$KEY_FILE" "$REMOTE_CONN" "tmux kill-session -t $s 2>/dev/null || echo '      $s not found'"
            done
        else
            echo "🔪 Killing tmux session '$SESSION_NAME' on Suresh..."
            ssh -i "$KEY_FILE" "$REMOTE_CONN" "tmux kill-session -t $SESSION_NAME"
        fi
        ;;
    *)
        usage
        ;; 
esac
