#!/bin/bash

# --- 🧭 Configuration (Google Cloud) ---
PKEY="$HOME/.ssh/gcp_key"               # ✅ Your GCP private key
REMOTE_USER="deshpande_vivek"           # ✅ GCP default user
REMOTE_HOST="35.237.249.135"           # ✅ Your GCP static IP

# --- Parallel arrays for directories to sync ---
NAMES=("mod_rsi" "whatsapp" "selling")
REMOTE_DIRS=(
  "/home/deshpande_vivek/mod_rsi/"
  "/home/deshpande_vivek/whatsapp/"
  "/home/deshpande_vivek/selling/"
)

# --- 🚀 MAIN ---
clear
echo "🚀 Starting rsync to transfer new/updated files from $REMOTE_HOST (Google Cloud)"

# Loop through each directory pair
for i in "${!NAMES[@]}"; do
  NAME="${NAMES[$i]}"
  REMOTE_PATH="${REMOTE_DIRS[$i]}"
  LOCAL_PATH="$HOME/ICICI_Direct/Google/$NAME/"

  echo ""
  echo "--- 🔄 Syncing directory: $NAME ---"
  echo "FROM: $REMOTE_PATH"
  echo "TO:   $LOCAL_PATH"

  # Ensure the local target directory exists
  mkdir -p "$LOCAL_PATH"

  # Use rsync to synchronize files.
  rsync -avz -e "ssh -i $PKEY" \
    --include='*.log' \
    --include='*.txt' \
    --include='*.json' \
    --include='*.py' \
    --include='*.sh' \
    --include='*.csv' \
    --exclude='*' \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH" "$LOCAL_PATH"

  # --- CORRECTED LOGIC: Rename copied log files with timestamp ---
  echo "Renaming log files in $LOCAL_PATH..."
  TIMESTAMP=$(date +%d%m%y%H%M) # Generate timestamp in DDMMYYHHMM format
  
  # Use a more robust for loop. Enable nullglob to prevent errors if no .log files are found.
  shopt -s nullglob
  for LOG_FILE in "$LOCAL_PATH"*.log; do
    FILENAME=$(basename "$LOG_FILE")
    
    # --- FIX: Check if the filename already contains a timestamp-like pattern ---
    if [[ ! "$FILENAME" =~ _[0-9]{10} ]]; then
      # This file has NOT been renamed yet. Proceed with renaming.
      BASE_NAME="${FILENAME%.*}" # Extract filename without extension
      EXTENSION="${FILENAME##*.}" # Extract extension
      
      NEW_FILENAME="${BASE_NAME}_${TIMESTAMP}.${EXTENSION}"
      mv "$LOG_FILE" "$LOCAL_PATH/$NEW_FILENAME"
      echo "  Renamed $FILENAME to $NEW_FILENAME"
    else
      echo "  Skipping already renamed file: $FILENAME"
    fi
  done
  shopt -u nullglob # Reset shell option
  # --- END CORRECTED LOGIC ---

done

echo -e "\n✅ All transfers completed."
read -p "Press any key to close..."
exit 0