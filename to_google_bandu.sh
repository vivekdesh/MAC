#!/bin/bash

# ==========================================================
# 🧭 Fixed Project Settings (Single Project)
# ==========================================================

# --- ADDED: Source directory for Python files ---
# --- Configuration ---

sourcePyDir="/Users/vivek/ICICI_Direct/mod_rsi"

localBaseDir="/Users/vivek/ICICI_Direct/vinay"
remoteBaseDir="~/mod_rsi"


# --- ADDED: Copy Python files before transfer ---
echo "Syncing changed *.py files from $sourcePyDir to $localBaseDir..."
rsync -avu --include='*.py' --exclude='*' "$sourcePyDir/" "$localBaseDir/"
echo "Sync complete."
echo "----------------------------------------"


# SSH alias from ~/.ssh/config
remoteHost="vinay"





# ==========================================================
# 📂 File transfer function
# ==========================================================

transfer_files() {
  local filePattern="$1"

  # Ensure local directory exists
  if [ ! -d "$localBaseDir" ]; then
    echo "❌ Local directory not found: $localBaseDir"
    exit 1
  fi

  echo "📁 Local source : $localBaseDir"
  echo "📡 Remote target: $remoteHost:$remoteBaseDir"

  local find_args=()

  if [ -z "$filePattern" ]; then
    echo "📤 Transferring .csv, .json, .py, .sh files..."
    find_args=( -maxdepth 1 -type f \( \
      -name "*.csv" -o \
      -name "*.json" -o \
      -name "*.py" -o \
      -name "*.sh" \
    \) )
  else
    echo "📤 Transferring files matching: $filePattern"
    find_args=( -maxdepth 1 -type f -name "$filePattern" )
  fi

  # Ensure remote directory exists
  ssh "$remoteHost" "mkdir -p '$remoteBaseDir'"

  # Rsync using SSH alias
  (
    cd "$localBaseDir" && \
    find . "${find_args[@]}" -print0
  ) | rsync -avz --files-from=- --from0 \
      "$localBaseDir/" \
      "$remoteHost:$remoteBaseDir/"

  if [ $? -eq 0 ]; then
    echo "✅ Transfer complete."
  else
    echo "❌ Transfer failed."
    exit 1
  fi
}

# ==========================================================
# 🧠 Usage
# ==========================================================

if [ "$#" -gt 1 ]; then
  echo "Usage:"
  echo "  ./ToGCP.sh            # transfer standard files"
  echo "  ./ToGCP.sh '*.py'     # transfer specific pattern"
  exit 1
fi

filePattern="$1"

transfer_files "$filePattern"

echo "✔️ Done."
