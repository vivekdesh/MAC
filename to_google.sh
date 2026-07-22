#!/bin/bash

# === 🧭 Google Cloud VM Settings ===
userDir="/Users/vivek/ICICI_Direct"
privateKeyPath="$HOME/.ssh/gcp_key"    # Path to your GCP private key
remoteHost="deshpande_vivek@34.26.75.26"   # <-- your GCP static IP + username
remoteBaseDir="/home/deshpande_vivek/"        # GCP default home dir

# === 📂 Function to transfer files ===
transfer_files() {
  local sourceDir="$1"
  local filePattern="$2"
  local remoteDir="$1" # same folder structure on remote
  local fullSourceDir="$userDir/$sourceDir"
  local fullRemoteDir="$remoteHost:$remoteBaseDir$remoteDir/"

  # Ensure local directory exists
  if [ ! -d "$fullSourceDir" ]; then
    echo "❌ Error: Local directory not found: $fullSourceDir"
    return 1
  fi

  local find_args=()
  if [ -z "$filePattern" ]; then
    echo "📤 Transferring CSV, JSON, Python, and Shell files from $sourceDir to $remoteDir..."
    find_args=( -maxdepth 1 -type f \( -name "*.csv" -o -name "*.json" -o -name "*.py" -o -name "*.sh" \) )
  else
    echo "📤 Transferring files matching '$filePattern' from $sourceDir to $remoteDir..."
    find_args=( -maxdepth 1 -type f -name "$filePattern" )
  fi

  # Use find + rsync for efficient transfer
  (cd "$fullSourceDir" && find . "${find_args[@]}" -print0) | \
  rsync -avz --files-from=- --from0 -e "ssh -i $privateKeyPath" "$fullSourceDir/" "$fullRemoteDir"

  local rsync_status=$?
  if [ $rsync_status -eq 0 ]; then
    echo "✅ Transfer complete for $sourceDir."
  else
    echo "❌ Error during rsync transfer for $sourceDir (exit code: $rsync_status)."
    return 1
  fi
}

# === 🧠 Usage checks ===
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: to_vivek (or ./to_google.sh) <directory_name|all|ALL> [file_pattern]"
  echo "Example 1 (all .py, .json, & .sh): to_vivek Algo_1"
  echo "Example 2 (specific file):        to_vivek Algo_1 paper_trade.py"
  echo "Example 3 (all supported dirs):   to_vivek all"
  exit 1
fi

# === 🚀 Execute transfer ===
targetDir="$1"
filePattern="$2"

if [[ "$targetDir" == "all" || "$targetDir" == "ALL" ]]; then
  echo "🚀 Batch mode: Transferring 'mod_rsi', 'selling', and 'whatsapp'..."
  for dir in "mod_rsi" "selling" "whatsapp"; do
    transfer_files "$dir" "$filePattern"
  done
else
  transfer_files "$targetDir" "$filePattern"
fi

read -p "Press Enter to continue..."
