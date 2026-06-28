#!/usr/bin/env bash

set -e

echo "Detecting OS and shell…"

OS_TYPE="$(uname -s)"
CURRENT_SHELL=$(basename "$SHELL")

echo "OS: $OS_TYPE"
echo "Shell: $CURRENT_SHELL"
echo ""

# ---------------------------------------
# Helper: Reverse file safely (macOS/Ubuntu)
# ---------------------------------------
reverse_file() {
    if command -v tac >/dev/null 2>&1; then
        tac "$1"
    else
        tail -r "$1"
    fi
}

# ---------------------------------------
# 1. UBUNTU / LINUX BASH
# ---------------------------------------
if [[ "$OS_TYPE" == "Linux" && "$CURRENT_SHELL" == "bash" ]]; then

    HIST_FILE="$HOME/.bash_history"

    [[ ! -f "$HIST_FILE" ]] && { echo "No .bash_history found."; exit 1; }

    echo "Backup created: $HIST_FILE.backup"
    cp "$HIST_FILE" "$HIST_FILE.backup"

    echo "Deduplicating bash history… (keep newest)"

    reverse_file "$HIST_FILE" | awk '!seen[$0]++' | reverse_file > "${HIST_FILE}_clean"
    mv "${HIST_FILE}_clean" "$HIST_FILE"

    echo "Reloading bash history…"
    history -c
    history -r

    echo "DONE."
    exit 0
fi

# ---------------------------------------
# 2. MACOS ZSH
# ---------------------------------------
if [[ "$OS_TYPE" == "Darwin" && "$CURRENT_SHELL" == "zsh" ]]; then

    HIST_FILE="$HOME/.zsh_history"

    [[ ! -f "$HIST_FILE" ]] && { echo "No .zsh_history found."; exit 1; }

    echo "Backup created: $HIST_FILE.backup"
    cp "$HIST_FILE" "$HIST_FILE.backup"

    echo "Deduplicating zsh history (mixed formats safe)…"

    # zsh new format: : 12345:0;command
    # zsh old format: command

    reverse_file "$HIST_FILE" | \
    awk '
        BEGIN { FS=";" }
        {
            if ($0 ~ /^:/ && NF>=2) {
                cmd = $2     # new format
            } else {
                cmd = $0     # old format
            }
            if (!seen[cmd]++) {
                lines[NR] = $0
                order[NR] = cmd
            }
        }
        END {
            for (i=1; i<=NR; i++) {
                if (order[i] != "") print lines[i]
            }
        }
    ' | reverse_file > "${HIST_FILE}_clean"

    mv "${HIST_FILE}_clean" "$HIST_FILE"

    echo "Reloading zsh…"
    exec zsh

    exit 0
fi

echo "Unsupported OS or shell."
exit 1
