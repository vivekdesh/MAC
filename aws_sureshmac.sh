#!/bin/bash

# --- Configuration vivek latest---
PKEY="/Users/sureshsoni/Desktop/algo/ssh_suresh_oracle.key"
REMOTE_USER="ubuntu"
REMOTE_HOST="140.245.15.195"

# --- Parallel arrays for macOS compatibility ---
NAMES=("mod_rsi" "sensex_suresh")
REMOTE_DIRS=("/home/ubuntu/mod_rsi/" "/home/ubuntu/sensex_suresh/")

# Extensions to fetch
EXTS=("*.log" "*.txt" "*.json" "*.py" "*.sh")

# --- Helper Functions ---
create_local_dir() {
  local LOCAL_PATH="$1"
  mkdir -p "$LOCAL_PATH"
  return $?
}

run_sftp() {
  local BATCH_FILE="$1"
  local REMOTE_PATH="$2"
  local LOCAL_PATH="$3"

  sftp -i "$PKEY" -b "$BATCH_FILE" "$REMOTE_USER@$REMOTE_HOST" 2> sftp_error.log
  if [ $? -ne 0 ]; then
    echo "❌ ERROR: SFTP failed for $REMOTE_PATH to $LOCAL_PATH"
    cat sftp_error.log
    rm -f sftp_error.log
    return 1
  fi
  rm -f sftp_error.log
  return 0
}

run_sftp_per_ext() {
  local NAME="$1"
  local REMOTE_PATH="$2"
  local EXT="$3"
  local LOCAL_PATH="/Users/sureshsoni/Desktop/algo/AWS/$NAME"
  local BATCH_FILE="sftp_${NAME}_${EXT//\*/}.txt"

  create_local_dir "$LOCAL_PATH" || return 1

  echo "cd $REMOTE_PATH" > "$BATCH_FILE"
  echo "mget -P $EXT $LOCAL_PATH/" >> "$BATCH_FILE"
  echo "quit" >> "$BATCH_FILE"

  echo "🔄 Getting $EXT from $REMOTE_PATH to $LOCAL_PATH"
  run_sftp "$BATCH_FILE" "$REMOTE_PATH" "$LOCAL_PATH" || echo "⚠️ Failed to get $EXT"
  rm -f "$BATCH_FILE"
}

# --- MAIN ---
clear
echo "🚀 Starting SFTP sync from $REMOTE_HOST"

# Loop using index
for i in "${!NAMES[@]}"; do
  NAME="${NAMES[$i]}"
  REMOTE_PATH="${REMOTE_DIRS[$i]}"

  echo "📁 Processing directory: $NAME ($REMOTE_PATH)"

  for EXT in "${EXTS[@]}"; do
    run_sftp_per_ext "$NAME" "$REMOTE_PATH" "$EXT"
  done

  echo "✅ Finished $NAME"
done

echo -e "\n✅ All transfers completed."
read -p "Press any key to close..."
exit 0
