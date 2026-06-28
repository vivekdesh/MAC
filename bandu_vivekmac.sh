#!/bin/bash

# ==============================================================================
# 🚀 CUSTOM BANDU UPLOAD SCRIPT (for 'syncbandu' alias)
# 1. Pre-processes local files.
# 2. Uploads specific file types to the Bandu remote server.
# ==============================================================================

# --- ⚙️ Configuration ---
PKEY="$HOME/.ssh/gcp_key"               # ✅ Your GCP private key
REMOTE_USER="vivek"                     # ✅ GCP default user
REMOTE_HOST="35.196.102.57"             # ✅ Your GCP static IP
REMOTE_BASE="/home/vivek"               # ✅ Base path on remote
LOCAL_ROOT="$HOME/ICICI_Direct"         # ✅ Define Local Project Root

# --- 📝 File Type Options ---
# For the LOCAL-to-LOCAL copy step
LOCAL_COPY_OPTS="--include=*.py --exclude=*"

# For the UPLOAD-to-REMOTE step (sh, csv, py, json, txt only)
UPLOAD_OPTS="--include=*.sh --include=*.csv --include=*.py --include=*.json --include=*.txt --exclude=*"

# --- FOLDER_LIST for Bandu upload ---
# Each item: "local_staging_dir:remote_sub_dir"
FOLDER_MAP=(
  "vinay:mod_rsi"
  "selling_1:selling_1"
)

# --- 🚀 STAGE 1: PRE-TRANSFER LOCAL SYNC ---
clear
echo "🚀 Starting Pre-Transfer Local Sync for Bandu..."

# 1. Sync select files from mod_rsi -> vinay
echo "--- Syncing local: mod_rsi -> vinay (.py and .sh files) ---"
rsync -avu $LOCAL_COPY_OPTS "$LOCAL_ROOT/mod_rsi/" "$LOCAL_ROOT/vinay/"

# 2. Sync select files from selling -> selling_1
echo "--- Syncing local: selling -> selling_1 (.py and .sh files) ---"
rsync -avu $LOCAL_COPY_OPTS "$LOCAL_ROOT/selling/" "$LOCAL_ROOT/selling_1/"

# --- 📤 STAGE 2: REMOTE UPLOAD ---
echo ""
echo "🚀 Starting rsync UPLOAD to $REMOTE_HOST (Bandu's GCP)"
echo "🔑 Using Key: $PKEY"

# Pre-flight check for key file
if [ ! -f "$PKEY" ]; then echo "❌ Key file not found: $PKEY"; exit 1; fi

# Loop through each folder mapping for upload
for mapping in "${FOLDER_MAP[@]}"; do
  local_sub=$(echo "$mapping" | cut -d':' -f1)
  remote_sub=$(echo "$mapping" | cut -d':' -f2)
  
  local_path="$LOCAL_ROOT/$local_sub"
  remote_path="$REMOTE_BASE/$remote_sub"

  echo "  📤 UPLOADING: $local_path/ -> $REMOTE_USER@$REMOTE_HOST:$remote_path/"
  
  rsync -avz -e "ssh -i $PKEY" \
    $UPLOAD_OPTS \
    "$local_path/" "$REMOTE_USER@$REMOTE_HOST:$remote_path/"
done

echo -e "\n✅ All 'syncbandu' operations completed."
exit 0
