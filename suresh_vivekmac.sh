#!/bin/bash

# --- Configuration vivek latest---
PKEY="$HOME/ICICI_Direct/Key/soch12_openssh"
REMOTE_USER="ubuntu"
REMOTE_HOST="16.171.172.182"

# --- Parallel arrays for macOS compatibility ---
NAMES=("mod_rsi")
REMOTE_DIRS=("/home/ubuntu/mod_rsi/")

# --- MAIN ---
clear
echo "🚀 Starting rsync to transfer new/updated files from $REMOTE_HOST"

# Loop using index
for i in "${!NAMES[@]}"; do
  NAME="${NAMES[$i]}"
  REMOTE_PATH="${REMOTE_DIRS[$i]}"
  LOCAL_PATH="$HOME/ICICI_Direct/Ubentu/suresh/$NAME/"

  echo ""
  echo "--- 🔄 Syncing directory: $NAME ---"
  echo "FROM: $REMOTE_PATH"
  echo "TO:   $LOCAL_PATH"

  # Ensure the local target directory exists
  mkdir -p "$LOCAL_PATH"

  # Use rsync to synchronize files.
  # -a: archive mode (preserves permissions, times, etc.)
  # -v: verbose (shows what's being transferred)
  # -z: compress file data during transfer
  # -e: specifies the remote shell (ssh) and the key to use
  # --include/--exclude: Selectively transfer only the desired file types.
  rsync -avz -e "ssh -i $PKEY" \
    --include='*.log' \
    --include='*.txt' \
    --include='*.json' \
    --include='*.py' \
    --include='*.sh' \
    --exclude='*' \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH" "$LOCAL_PATH"

done

echo -e "\n✅ All transfers completed."
read -p "Press any key to close..."
exit 0