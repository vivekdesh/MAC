#!/bin/bash
# ==============================================================================
# Safe Incremental Backup: ICICI_Direct -> Google Drive
# Strictly one-way push: Source (/Users/vivek/ICICI_Direct) is NEVER modified/polluted.
# ==============================================================================

SOURCE="/Users/vivek/ICICI_Direct/"
DEST="/Users/vivek/Library/CloudStorage/GoogleDrive-deshpande.vivek@gmail.com/My Drive/Programming_experiments/ICICI_Direct/"

if [ ! -d "$SOURCE" ]; then
  echo "Error: Source directory '$SOURCE' does not exist."
  exit 1
fi

if [ ! -d "$DEST" ]; then
  echo "Error: Destination directory '$DEST' does not exist."
  exit 1
fi

echo "Starting safe incremental backup to Google Drive..."

rsync -auv --stats \
  --exclude="binance/data/" \
  --exclude="weekly/data/" \
  --exclude="Google/" \
  --exclude="Ubentu/" \
  --exclude="*venv*" \
  --exclude=".claude/" \
  --exclude=".antigravity/" \
  --exclude=".gemini/" \
  --exclude="*.tmp" \
  --exclude="*.scratch" \
  --exclude="__pycache__/" \
  --exclude=".DS_Store" \
  "$SOURCE" \
  "$DEST"

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "Backup completed successfully (Exit code: 0)."
else
  echo "Backup exited with error code: $EXIT_CODE"
fi

exit $EXIT_CODE
