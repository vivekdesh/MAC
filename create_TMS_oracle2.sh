#!/bin/bash

# Oracle 2 tmux setup for whatsapp + rokde + ngrok sessions.

setup_session() {
    local session_name="$1"
    local directory="$2"

    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        tmux new-session -d -s "$session_name"
        echo "Created tmux session: $session_name"

        tmux send-keys -t "$session_name" "source ~/myenv/bin/activate" Enter
        tmux send-keys -t "$session_name" "cd ~/$directory" Enter
        tmux send-keys -t "$session_name" "clear" Enter
        echo "Configured session $session_name in directory $directory"
    else
        echo "Session '$session_name' already exists. Doing nothing."
    fi
}

setup_ngrok_session() {
    local session_name="ngrok"

    if ! tmux has-session -t "$session_name" 2>/dev/null; then
        tmux new-session -d -s "$session_name"
        echo "Created tmux session: $session_name"
        
        # Create log directory and the script file
        mkdir -p ~/ngrok
        
        cat << 'EOF' > ~/ngrok/run_ngrok.sh
#!/bin/bash
consecutive_failures=0
max_failures=5
while [ $consecutive_failures -lt $max_failures ]; do
    start_time=$(date +%s)
    /snap/bin/ngrok http 3000 --log=stdout >> ~/ngrok/ngrok.log 2>&1
    exit_code=$?
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo "$(date) - Ngrok exited with code $exit_code after $duration seconds." >> ~/ngrok/ngrok.log
    if [ $duration -gt 60 ]; then
        consecutive_failures=0
    else
        consecutive_failures=$((consecutive_failures + 1))
        echo "$(date) - Ngrok crashed quickly. Failure count: $consecutive_failures/$max_failures" >> ~/ngrok/ngrok.log
    fi
    if [ $consecutive_failures -ge $max_failures ]; then
        echo "$(date) - Ngrok crashed $max_failures times consecutively. Exiting loop." >> ~/ngrok/ngrok.log
        break
    fi
    sleep 20
done
EOF
        chmod +x ~/ngrok/run_ngrok.sh
        
        # Start ngrok script safely
        tmux send-keys -t "$session_name" "~/ngrok/run_ngrok.sh" Enter
        echo "Started loop-wrapped Ngrok in session '$session_name'."
    else
        echo "Session '$session_name' already exists. Doing nothing."
    fi
}

# fwupd (firmware updater) has no real hardware to update on a cloud VM but held
# ~155 MB RAM on this 956 MB box. Masked so it never restarts. Undo: systemctl unmask.
disable_fwupd() {
    if [ "$(systemctl is-enabled fwupd 2>/dev/null)" = "masked" ]; then
        echo "fwupd already masked. Doing nothing."
        return
    fi
    sudo -n systemctl stop fwupd fwupd-refresh.timer 2>/dev/null
    sudo -n systemctl mask fwupd fwupd-refresh.timer \
        && echo "Disabled fwupd (stopped + masked)." \
        || echo "WARNING: could not mask fwupd (sudo?)."
}

echo "Starting Oracle 2 tmux session setup..."

disable_fwupd
setup_session "whatsapp" "whatsapp"
setup_session "rokde" "whatsapp"
setup_ngrok_session

echo "Finished Oracle 2 tmux session setup."
tmux ls 2>/dev/null || echo "No sessions"
