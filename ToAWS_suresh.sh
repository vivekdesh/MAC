#!/bin/bash

# --- Configuration ---
localBaseDir="/Users/vivek/ICICI_Direct/algo_suresh"
privateKeyPath="/Users/vivek/ICICI_Direct/Key/soch12_openssh"
remoteHost="ubuntu@16.171.172.182"
remoteBaseDir="/home/ubuntu/mod_rsi"

# --- ADDED: Source directory for Python files ---
sourcePyDir="/Users/vivek/ICICI_Direct/mod_rsi"

# --- ADDED: Copy Python files before transfer ---
echo "Syncing changed *.py files from $sourcePyDir to $localBaseDir..."
# added to bypass!!
rsync -avu --include='*.py' --exclude='*' "$sourcePyDir/" "$localBaseDir/"
echo "Sync complete."
echo "----------------------------------------"

# Function to transfer files
transfer_files() {
  local filePattern="$1"
  local fullSourceDir="$localBaseDir/" # Trailing slash is important for rsync
  local fullRemoteDir="$remoteHost:$remoteBaseDir/"

  # Check if the local source directory exists
  if [ ! -d "$fullSourceDir" ]; then
    echo "Error: Local directory not found: $fullSourceDir"
    return 1
  fi

  local find_args=()
  if [ -z "$filePattern" ]; then
    echo "Transferring JSON, Python, and Shell files from $localBaseDir to $remoteBaseDir..."
    # Note: The \( ... \) is for grouping expressions with -o
    find_args=( -maxdepth 1 -type f \( -name "*.json" -o -name "*.py" -o -name "*.sh" \) )
  else
    echo "Transferring files matching '$filePattern' from $localBaseDir to $remoteBaseDir..."
    find_args=( -maxdepth 1 -type f -name "$filePattern" )
  fi

  # Use find to generate the file list and pipe to rsync for efficient transfer
  # -a: archive mode, -v: verbose, -z: compress
  # --files-from=-: read file list from stdin
  # --from0: expect NUL-terminated file names (handles special chars)
  # -e: specify the remote shell to use (ssh with our key)
  # We cd into the source directory so find produces relative paths for rsync.
  (cd "$fullSourceDir" && find . "${find_args[@]}" -print0) | rsync -avz --files-from=- --from0 -e "ssh -i $privateKeyPath" "$fullSourceDir/" "$fullRemoteDir"

  local rsync_status=$?
  if [ $rsync_status -eq 0 ]; then
    echo "Transfer complete."
  else
    echo "Error during rsync transfer (exit code: $rsync_status)."
    return 1
  fi
}

# Check for the correct number of arguments
if [ "$#" -gt 1 ]; then
  echo "Usage: ./ToAWS.sh [file_pattern]"
  echo "Example 1 (all .py, .json, & .sh): ./ToAWS.sh"
  echo "Example 2 (specific file):         ./ToAWS.sh paper_trade.py"
  echo "Example 3 (all .py files):         ./ToAWS.sh '*.py'"
  exit 1
fi

# Call the transfer function
transfer_files "$1"

read -p "Press Enter to continue..."