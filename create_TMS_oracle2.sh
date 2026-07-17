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
        tmux send-keys -t "$session_name" "/snap/bin/ngrok http 3000" Enter
        echo "Started 'ngrok http 3000' in session '$session_name'."
    else
        echo "Session '$session_name' already exists. Doing nothing."
    fi
}

echo "Starting Oracle 2 tmux session setup..."

setup_session "whatsapp" "whatsapp"
setup_session "rokde" "whatsapp"
setup_ngrok_session

echo "Finished Oracle 2 tmux session setup."
tmux ls 2>/dev/null || echo "No sessions"
