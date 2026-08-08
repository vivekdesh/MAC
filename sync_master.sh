#!/bin/bash

# ==============================================================================
# 🚀 MASTER SYNC SCRIPT (Bash 3.2 Compatible for macOS)
# Unified controller for all file transfers (Uploads & Downloads)
# ==============================================================================

# --- ⚙️ Configuration ---
# Define project root on your local machine
LOCAL_ROOT="$HOME/ICICI_Direct"
KEY_BASE_PATH="$LOCAL_ROOT/Key/"

# --- 📝 File Type Globals ---
# Uploads are restrictive (Code + Config only)
UPLOAD_OPTS="--exclude=backtest_ha_ema34/ --exclude=backtest_ha_ema34_selling/ --exclude=FONSEScripMaster.csv --exclude=parameters_cache.json --exclude=index_daily_ha_bias_cache.json --exclude=*state*.json --exclude=calculated_greeks*.json --exclude=option_chain_cache.json --exclude=.claude/ --exclude=__pycache__/ --exclude=.git/ --include=*.py --include=*.json --include=*.sh --include=*.csv --include=requirements.txt --exclude=*"

# Downloads are permissive (Get everything except junk)
# We exclude .git and __pycache__ to keep it clean, but get all logs/txt/etc.
# We also exclude apiLogs* (verbose Breeze SDK debug logs). They are large, grow
# unbounded, and are never needed on the Mac — excluding them removes the bulk of
# our egress cost.
# Note: --append is added selectively in rsync commands (logs only) for incremental
# transfers. Non-log files (JSON, CSV, .py, etc.) use -z compression only.
DOWNLOAD_OPTS="--exclude=.git --exclude=__pycache__ --exclude=.DS_Store --exclude=apiLogs*"

# ==============================================================================
# 🛠️ Configuration Lookup Function (Replaces Associative Arrays)
# ==============================================================================
get_target_config() {
    local target=$1
    
    # Defaults
    REMOTE_CONN=""
    KEY_FILE=""
    FOLDER_LIST=""
    DL_BASE=""

    case "$target" in
        "vivek")
            REMOTE_CONN="deshpande_vivek@34.26.75.26:/home/deshpande_vivek"
            KEY_FILE="$HOME/.ssh/gcp_key"
            FOLDER_LIST="retire:retire selling:selling nifty:nifty Program_restart:Program_restart MAC/create_TMS_google_root.sh:create_TMS.sh"
            DL_BASE="$HOME/ICICI_Direct/Google"
            ;;
        "suresh")
            REMOTE_CONN="ubuntu@140.245.15.195:/home/ubuntu"
            KEY_FILE="$LOCAL_ROOT/Key/suresh_oracle/ssh_suresh_oracle.key"
            FOLDER_LIST="algo_suresh:mod_rsi sensex_suresh:sensex_suresh nifty:nifty Program_restart:Program_restart"
            DL_BASE="$HOME/ICICI_Direct/Ubentu/suresh"
            ;;
        "sensex_suresh")
            REMOTE_CONN="suresh@server.com"
            KEY_FILE="$KEY_BASE_PATH/suresh_oracle/ssh_suresh_oracle.key"
            FOLDER_LIST="sensex_suresh/"
            DL_BASE="$LOCAL_ROOT/sensex_suresh/"
            ;;
        "sensex")
            REMOTE_CONN=""
            KEY_FILE=""
            FOLDER_LIST="sensex/"
            DL_BASE=""
            ;;
        "bandu")
            REMOTE_CONN="vivek@35.196.102.57:/home/vivek"
            KEY_FILE="$HOME/.ssh/gcp_key"
            FOLDER_LIST="vinay:mod_rsi selling_1:selling_1"
            DL_BASE="$HOME/ICICI_Direct/Google/Bandu"
            ;;
        "oracle_binance")
            REMOTE_CONN="ubuntu@80.225.215.187:/home/ubuntu"
            KEY_FILE="$LOCAL_ROOT/Key/oracle/ssh-key-2026-02-11.key"
            FOLDER_LIST="binance:binance mod_rsi:mod_rsi selling_1:selling_1 sensex:sensex nifty:nifty Program_restart:Program_restart MAC/kill_run_oracle.sh:kill_run_oracle.sh mod_rsi/create_TMS_oracle.sh:create_TMS_oracle.sh"
            DL_BASE="$LOCAL_ROOT/Google"
            ;;
        "oracle2")
            REMOTE_CONN="ubuntu@155.248.244.211:/home/ubuntu"
            KEY_FILE="$LOCAL_ROOT/Key/oracle2/ssh-key-2026-02-11.key"
            FOLDER_LIST="whatsapp:whatsapp ngrok:ngrok Program_restart:Program_restart MAC/create_TMS_oracle2.sh:create_TMS.sh"
            DL_BASE="$LOCAL_ROOT/Google"
            ;;
        *)
            echo "❌ Unknown target: $target"
            exit 1
            ;;
    esac
}

usage() {
    echo "Usage: $0 [target|command] [action]"
    echo ""
    echo "Standard Usage:"
    echo "  $0 vivek up      # Upload to Vivek"
    echo "  $0 suresh down   # Download from Suresh"
    echo "  $0 sensex up/down # Upload/Download sensex (Master Bot)"
    echo "  $0 senx_suresh  # Copy sensex → senx_suresh"
    echo ""
    echo "Batch Commands:"
    echo "  $0 all           # Upload AND Download for ALL targets"
    echo "  $0 all_u         # Upload to ALL targets"
    echo "  $0 all_d         # Download from ALL targets"
    exit 1
}

# --- 🔄 Copy Function for sensex → sensex_suresh ---
copy_sensex_to_sensex_suresh() {
    echo "🔄 Syncing changed root-level sensex → sensex_suresh (*.py, *.sh only)..."

    SRC_DIR="$LOCAL_ROOT/sensex"
    DEST_DIR="$LOCAL_ROOT/sensex_suresh"

    mkdir -p "$DEST_DIR"

    echo "📁 Copying only changed root-level Python and shell files..."
    find "$SRC_DIR" -maxdepth 1 -type f \( -name '*.py' -o -name '*.sh' \) | while IFS= read -r src_file; do
        dest_file="$DEST_DIR/$(basename "$src_file")"

        if [ ! -f "$dest_file" ] || ! cmp -s "$src_file" "$dest_file"; then
            cp -f "$src_file" "$dest_file"
            echo "    Updated: $(basename "$src_file")"
        fi
    done

    echo "✅ Copy completed: sensex → sensex_suresh"
}

# --- Rename Logs by Date ---
# Renames rolling logs (app.log, app_single.log, etc.) to include today's date
# so each calendar day has its own file (app_23Jun26.log). This ensures:
# 1. --append-verify works (same filename all day, new bytes only next time)
# 2. No truncation caveat (different filename = fresh file tomorrow)
# Only renames files that don't already have a date suffix.
rename_logs_by_date() {
    local target_dir="$1"
    local today=$(date +%d%b%y)  # e.g., "23Jun26"
    echo "  📅 Renaming logs to date-stamped names (today: $today)"

    shopt -s nullglob
    for log_file in "$target_dir"/*.log; do
        filename=$(basename "$log_file")
        # Skip if already date-stamped (ends with _DDMonYY.log or _##########.log)
        if [[ "$filename" =~ _[0-9]{2}[A-Za-z]{3}[0-9]{2}\.log$ ]] || [[ "$filename" =~ _[0-9]{10}\.log$ ]]; then
            continue
        fi

        base_name="${filename%.log}"
        new_name="${base_name}_${today}.log"

        if [ "$filename" != "$new_name" ]; then
            mv "$log_file" "$target_dir/$new_name"
            echo "    ✅ Renamed: $filename → $new_name"
        fi
    done
    shopt -u nullglob
}

# --- Log Date-Split Function ---
# Splits each "live" rolling log (e.g. app.log) into per-date files named
# <base>_DDMonYY.log (e.g. app_23Jun26.log), where the date is taken from the
# "YYYY-MM-DD ..." prefix on each log line.
#
# WHY: the bots use a plain logging.FileHandler, so app.log is NOT rotated at
# midnight. Splitting on the Mac by the in-line date guarantees each day file
# holds only that calendar date's lines (split exactly at 00:00), even if
# app.log happens to span more than one day.
#
# The original live log is left IN PLACE (not renamed/moved) so the next rsync
# transfers only the newly-appended bytes (delta) instead of the whole file.
#
# Each run REGENERATES the day file for every date present in the current log
# (the awk '>' truncates on first write, then appends), so an incomplete
# previous-day file is rebuilt/completed as long as that data is still present
# in app.log. Dates no longer present in app.log are left untouched (their
# existing day files are preserved).
split_logs_by_date() {
    local target_dir="$1"
    echo "  🗂  Splitting logs by date in: $target_dir"

    shopt -s nullglob
    for LOG_FILE in "$target_dir"/*.log; do
        FILENAME=$(basename "$LOG_FILE")
        # Skip our own day-split outputs (…_DDMonYY.log) and any legacy
        # minute-stamped files (…_##########.log) so only live logs are split.
        if [[ "$FILENAME" =~ _[0-9]{2}[A-Za-z]{3}[0-9]{2}\.log$ ]] || [[ "$FILENAME" =~ _[0-9]{10}\.log$ ]]; then
            continue
        fi

        local BASE_NAME="${FILENAME%.log}"
        echo "    ↳ splitting $FILENAME"
        # Character classes (not {n} intervals) are used so this works with the
        # default macOS awk, which lacks interval-expression support.
        awk -v dir="$target_dir" -v base="$BASE_NAME" '
            BEGIN {
                split("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec", mon, " ")
            }
            {
                # A line beginning "YYYY-MM-DD" switches the current output file.
                if (substr($0, 1, 10) ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/) {
                    yy = substr($0, 3, 2);
                    mm = substr($0, 6, 2) + 0;
                    dd = substr($0, 9, 2);
                    out = dir "/" base "_" dd mon[mm] yy ".log";
                }
                # Dated lines and their continuation lines (e.g. tracebacks) are
                # written to the current date file. Lines before any dated line
                # (out still empty) are skipped.
                if (out != "") print > out;
            }
        ' "$LOG_FILE"
        # Show which day-files were created/updated by this split.
        find "$target_dir" -maxdepth 1 -name "${BASE_NAME}_[0-9][0-9][A-Za-z][a-z][a-z][0-9][0-9].log" -newer "$LOG_FILE" 2>/dev/null | while read f; do
            echo "      → $(basename "$f") ($(ls -lh "$f" | awk '{print $5}'))"
        done
    done
    shopt -u nullglob
}

# --- Sync Function ---
run_sync() {
    local target=$1
    local direction=$2
    
    # Load configuration for this target
    get_target_config "$target"
    
    # Set source directory for copy function
    SRC_DIR="$LOCAL_ROOT/sensex/"
    
    # Pre-flight checks
    if [ ! -f "$KEY_FILE" ]; then echo "❌ Key file not found: $KEY_FILE"; exit 1; fi
    
    # Debug output
    echo "🔑 DEBUG: KEY_FILE=$KEY_FILE"
    echo "🔑 DEBUG: KEY_BASE_PATH=$KEY_BASE_PATH"
    echo "🔑 DEBUG: LOCAL_ROOT=$LOCAL_ROOT"

    echo "🚀 Starting $direction for TARGET: $target"
    echo "🔑 Using Key: $KEY_FILE"

    # Iterate over defined folders (Space separated string in Bash 3.2)
    for mapping in $FOLDER_LIST; do
        local local_sub=$(echo $mapping | cut -d':' -f1)
        local remote_sub=$(echo $mapping | cut -d':' -f2)
        
        local local_path="$LOCAL_ROOT/$local_sub"
        
        # Determine remote path parts
        local remote_user_host=$(echo $REMOTE_CONN | cut -d':' -f1)
        local remote_base=$(echo $REMOTE_CONN | cut -d':' -f2)
        local remote_path="$remote_base/$remote_sub"

        # Determine source and destination with proper trailing slashes for directories
        local local_src="$local_path"
        local remote_dest="$remote_user_host:$remote_path"

        # If it's a directory, add trailing slash to sync contents
        if [ -d "$local_path" ]; then
            local_src="$local_path/"
            remote_dest="$remote_user_host:$remote_path/"
            local is_directory=1
        else
            local is_directory=0
        fi

        if [ "$direction" == "up" ]; then
            echo "  📤 UPLOADING: $local_path -> $remote_path"

            # Special case for Suresh
            if [ "$target" == "suresh" ] && [ "$local_sub" == "algo_suresh" ]; then
                echo "    Note: Syncing mod_rsi/*.py to algo_suresh/ first..."
                rsync -avu --include='*.py' --exclude='*' "$LOCAL_ROOT/mod_rsi/" "$LOCAL_ROOT/algo_suresh/"
            fi

            # Ensure sensex_suresh is refreshed from sensex before upload
            if [ "$target" == "suresh" ] && [ "$local_sub" == "sensex_suresh" ]; then
                copy_sensex_to_sensex_suresh
            fi

            # Special case for Bandu
            if [ "$target" == "bandu" ]; then
                echo "    Note: Syncing mod_rsi/*.py to vinay/ first..."
                rsync -avu --include='*.py' --exclude='*' "$LOCAL_ROOT/mod_rsi/" "$LOCAL_ROOT/vinay/"
                echo "    Note: Syncing selling/*.py to selling_1/ first..."
                rsync -avu --include='*.py' --exclude='*' "$LOCAL_ROOT/selling/" "$LOCAL_ROOT/selling_1/"
            fi

            # Special case for Oracle
            if [ "$target" == "oracle_binance" ] && [ "$local_sub" == "selling_1" ]; then
                echo "    Note: Syncing selling/*.py to selling_1/ first..."
                rsync -avu --include='*.py' --exclude='*' "$LOCAL_ROOT/selling/" "$LOCAL_ROOT/selling_1/"
            fi

            rsync -avz -e "ssh -i $KEY_FILE" \
                $UPLOAD_OPTS \
                "$local_src" "$remote_dest"

        elif [ "$direction" == "down" ]; then
            # Use configured download base
            if [ "$is_directory" -eq 1 ]; then
                local dl_final_path="$DL_BASE/$local_sub"
                mkdir -p "$dl_final_path"

                echo "  📥 DOWNLOADING: $remote_path -> $dl_final_path"

                # First, download all non-log files without --append so JSON files overwrite cleanly
                rsync -avz -e "ssh -i $KEY_FILE" \
                    $DOWNLOAD_OPTS --exclude="*.log" \
                    "$remote_user_host:$remote_path/" "$dl_final_path/"

                # Second, download ONLY .log files WITH --append for incremental transfers
                rsync -avz --append -e "ssh -i $KEY_FILE" \
                    $DOWNLOAD_OPTS --include="*.log" --exclude="*" \
                    "$remote_user_host:$remote_path/" "$dl_final_path/"

                # Rename rolling logs to include today's date (app.log → app_23Jun26.log)
                # so each calendar day has a unique file and --append-verify works
                rename_logs_by_date "$dl_final_path"

                # Split downloaded logs into per-date files (app_DDMonYY.log)
                split_logs_by_date "$dl_final_path"
            else
                local dl_parent
                dl_parent=$(dirname "$DL_BASE/$local_sub")
                mkdir -p "$dl_parent"

                echo "  📥 DOWNLOADING: $remote_path -> $DL_BASE/$local_sub"

                rsync -avz -e "ssh -i $KEY_FILE" \
                    $DOWNLOAD_OPTS --exclude="*.log" \
                    "$remote_user_host:$remote_path" "$DL_BASE/$local_sub"

                rsync -avz --append -e "ssh -i $KEY_FILE" \
                    $DOWNLOAD_OPTS --include="*.log" --exclude="*" \
                    "$remote_user_host:$remote_path" "$DL_BASE/$local_sub"
            fi
        fi
    done

    # Batch upload all kill_*.sh scripts for vivek/oracle2 in one rsync call
    if [ "$direction" == "up" ]; then
        if [ "$target" == "vivek" ]; then
            echo "  📤 UPLOADING: MAC/kill_*.sh -> /home/deshpande_vivek/ (batched)"
            rsync -avz -e "ssh -i $KEY_FILE" \
                --include='kill_retire_google.sh' \
                --include='kill_selling_google.sh' \
                --include='kill_whatsapp_google.sh' \
                --include='kill_nifty_google.sh' \
                --exclude='*' \
                "$LOCAL_ROOT/MAC/" "$remote_user_host:/home/deshpande_vivek/"
        elif [ "$target" == "oracle2" ]; then
            echo "  📤 UPLOADING: MAC/kill_*.sh -> /home/ubuntu/ (batched)"
            rsync -avz -e "ssh -i $KEY_FILE" \
                --include='kill_whatsapp_google.sh' \
                --exclude='*' \
                "$LOCAL_ROOT/MAC/" "$remote_user_host:/home/ubuntu/"
        fi

        # If we uploaded Program_restart, automatically apply it to the home directory
        # and restart the subscriber service.
        if [[ "$FOLDER_LIST" == *"Program_restart"* ]]; then
            echo "  🔄 POST-SYNC: Updating fast-param-subscriber on $target..."
            ssh -i "$KEY_FILE" -o ConnectTimeout=8 "$remote_user_host" \
              "cp ~/Program_restart/fast_parameter_handler.py ~/ 2>/dev/null; cp ~/Program_restart/fast_param_subscriber.py ~/ 2>/dev/null; sudo systemctl restart icici-fast-param-subscriber.service"
        fi
    fi

    echo "✅ Operation complete."
}

# ==============================================================================
# 🚀 Execution Logic
# ==============================================================================

COMMAND=$1
ACTION=$2

case "$COMMAND" in
    "all")
        echo "🌐 MASTER BATCH: Doing EVERYTHING (Down first, then Up for ALL)..."
        for t in "vivek" "suresh" "oracle_binance" "oracle2"; do
            echo "---------------------------------------------------"
            run_sync "$t" "down"
            run_sync "$t" "up"
        done
        ;;
    "all_u")
        echo "🌐 MASTER BATCH: Uploading to ALL..."
        copy_sensex_to_sensex_suresh
        for t in "vivek" "suresh" "oracle_binance" "oracle2"; do
            echo "---------------------------------------------------"
            run_sync "$t" "up"
        done
        ;;
    "all_d")
        echo "🌐 MASTER BATCH: Downloading from ALL..."
        for t in "vivek" "suresh" "oracle_binance" "oracle2"; do
            echo "---------------------------------------------------"
            run_sync "$t" "down"
        done
        ;;
    "sensex_suresh")
        copy_sensex_to_sensex_suresh
        ;;
    "sensex")
        echo "🎯 Maintaining sensex as master bot"
        # Use existing sensex sync logic
        run_sync "$COMMAND" "$ACTION"
        ;;
    *)
        # Standard Usage: ./script.sh vivek up
        if [ -z "$COMMAND" ] || [ -z "$ACTION" ]; then
            usage
        fi
        run_sync "$COMMAND" "$ACTION"
        ;;
esac
