#!/bin/bash

# Define the two folders you want to synchronize
folder1="/Users/vivek/ICICI_Direct"
folder2="/Users/vivek/Library/CloudStorage/GoogleDrive-deshpande.vivek@gmail.com/My Drive/Programming_experiments/ICICI_Direct"
#'/Users/vivek/Library/CloudStorage/GoogleDrive-deshpande.vivek@gmail.com/My Drive/Programming_experiments/ICICI_Direct'
# Ensure that both source folders exist
if [ ! -d "$folder1" ]; then
  echo "Error: Source folder 1 '$folder1' does not exist."
  exit 1
fi

if [ ! -d "$folder2" ]; then
  echo "Error: Source folder 2 '$folder2' does not exist."
  exit 1
fi

# Function to perform the synchronization
synchronize_folders() {
  local source="$1"
  local destination="$2"

  echo "Synchronizing from '$source' to '$destination' (updating existing, no deletions)..."

  # Use rsync with the following options:
  # -av: archive mode (recursive, preserves permissions, times, etc.), verbose
  # -u: update - skip files that are newer on the destination
  # --dry-run: perform a trial run without making changes (initially)
  rsync -avu "$source/" "$destination"

  echo ""
  echo "If the dry run output looks correct, remove '--dry-run' from the rsync command to perform the actual synchronization."
}

# Perform the synchronization from folder1 to folder2
synchronize_folders "$folder1" "$folder2"

echo ""

# Perform the synchronization from folder2 to folder1
synchronize_folders "$folder2" "$folder1"

echo ""
echo "Synchronization process completed. Please review the dry-run output and run the script again without '--dry-run' to apply the changes."
echo "Remember to test this thoroughly to ensure it behaves as expected."

exit 0