 #!/bin/bash

# --- CONFIGURATION ---
# Define the list of all relevant project directory names.
# "root" represents the parent directory (ICICI_Direct).
PROJECT_DIRS=("mod_rsi" "algo_suresh" "whatsapp" "Algo_1" "binance" "selling" "MAC" "root")
# ---------------------

# --- VALIDATION ---
# Check if a source directory was provided as an argument.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <source_directory>"
    echo "Example: $0 whatsapp"
    echo "Use 'root' for the main ICICI_Direct directory."
    exit 1
fi

source_dir_name=$1
is_valid_source=false

# Check if the provided source directory is in the project list.
for dir in "${PROJECT_DIRS[@]}"; do
    if [ "$dir" == "$source_dir_name" ]; then
        is_valid_source=true
        break
    fi
done

if [ "$is_valid_source" = false ]; then
    echo "Error: Invalid source directory '$source_dir_name'."
    echo "Please use one of the following: ${PROJECT_DIRS[*]}"
    exit 1
fi

# Define the full path to the source file.
# It's named "Gemini.md", not "GEMINI.md".
if [ "$source_dir_name" == "root" ]; then
    source_file="../Gemini.md"
else
    source_file="../$source_dir_name/Gemini.md"
fi

# Check if the source Gemini.md file exists.
if [ ! -f "$source_file" ]; then
    echo "Error: Source file '$source_file' not found."
    exit 1
fi
# --- SYNC LOGIC ---
echo "Syncing Gemini.md from source: $source_dir_name"

# Loop through all defined project directories to use them as destinations.
for target_dir_name in "${PROJECT_DIRS[@]}"; do
    # Skip copying to the source directory itself.
    if [ "$target_dir_name" == "$source_dir_name" ]; then
        continue
    fi

    # Define the destination path.
    if [ "$target_dir_name" == "root" ]; then
        dest_path=".."
    else
        dest_path="../$target_dir_name"
    fi

    dest_file="$dest_path/Gemini.md"

    # Check if the destination directory exists.
    if [ ! -d "$dest_path" ]; then
        echo "  -> Warning: Destination directory '$dest_path' not found. Skipping."
        continue
    fi
    
    # Check if the destination file exists and is newer than the source.
    if [ -f "$dest_file" ] && [ "$dest_file" -nt "$source_file" ]; then
        echo "  -> Skipped: '$dest_file' is newer than the source. No copy needed."
    else
        # Copy the file if the destination doesn't exist or is older.
        cp "$source_file" "$dest_file"
        if [ "$target_dir_name" == "root" ]; then
            echo "  -> Copied to root ICICI_Direct/ directory."
        else
            echo "  -> Copied to $dest_path/"
        fi
    fi
done

echo "Sync complete."
