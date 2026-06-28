# ==============================================================================
# 🚀 TRADING INFRASTRUCTURE: MASTER CONTROL GUIDE
# ==============================================================================
# This file contains aliases for syncing code and managing remote VMs.
# Ensure SCRIPT_DIR is exported in your shell config:
# export SCRIPT_DIR="$HOME/ICICI_Direct/MAC"
# ==============================================================================

# === 🛰️ MASTER SYNC SYSTEM (sync_master.sh) ===
# Centralized controller for rsync-powered Smart Syncing.
#
# | Alias   | Command                | Purpose                                         |
# | :---    | :---                   | :---                                            |
# | sm      | sm <target> <up/down>  | Smart Sync (e.g. sm vivek up)                   |
# | all     | all                    | Smart Sync: Download (Logs, Data, Code) -> Upload |
# | all_u   | all_u                  | Batch Upload: Push code/configs to all servers  |
# | all_d   | all_d                  | Batch Download: Pull all logs, data, and code   |
# | all.st  | all.st                 | Check health of ALL remote servers              |
# | all.r   | all.r                  | Restart ALL projects on ALL servers             |
# | all.r.y | all.r.y                | Hard Restart (Clear Logs) ALL projects on ALL   |
# echo 'alias ssh_o="ssh -i /Users/vivek/icici_direct/key/oracle/ssh-key-2026-02-11.key ubuntu@80.225.215.187"' >> ~/.zshrc
# source ~/.zshrc

alias sm='bash "$SCRIPT_DIR/sync_master.sh"'      
alias all='bash "$SCRIPT_DIR/sync_master.sh" all'
alias all_u='bash "$SCRIPT_DIR/sync_master.sh" all_u'
alias all_d='bash "$SCRIPT_DIR/sync_master.sh" all_d'
alias all.st='v.st && s.st && o.st'
alias all.r='v.all && o.r'
alias all.r.y='v.all.y && o.r.y'

# === 🔄 INDIVIDUAL SERVER SYNC ===
alias v.u='bash "$SCRIPT_DIR/sync_master.sh" vivek up'
alias v.d='bash "$SCRIPT_DIR/sync_master.sh" vivek down'
alias s.u='bash "$SCRIPT_DIR/sync_master.sh" suresh up'
alias s.d='bash "$SCRIPT_DIR/sync_master.sh" suresh down'
alias b.u='bash "$SCRIPT_DIR/bandu_vivekmac.sh"'      # Custom Upload to Bandu
alias b.d='bash "$SCRIPT_DIR/sync_master.sh" bandu down'
alias o.u='bash "$SCRIPT_DIR/sync_master.sh" oracle_binance up'
alias o.d='bash "$SCRIPT_DIR/sync_master.sh" oracle_binance down'

# === 🕹️ REMOTE OPERATIONS (Smart Aliases) ===
# Direct, specific control for each algorithm and server.
# Format: <server>.<action>

# --- VIVEK (GCP) ---
alias v.st='bash "$SCRIPT_DIR/remote_vivek.sh" status'            # Check Health
alias v.setup='bash "$SCRIPT_DIR/remote_vivek.sh" setup'          # Run Setup

# Vivek Restarts (Default: Keep Logs)
alias v.ret='bash "$SCRIPT_DIR/remote_vivek.sh" restart ret'     # Restart Retire
alias v.sell='bash "$SCRIPT_DIR/remote_vivek.sh" restart sell'   # Restart Selling
alias v.sell_1='bash "$SCRIPT_DIR/remote_oracle.sh" restart selling_1' # Convenience forwarder to Oracle Selling_1
alias v.sen='bash "$SCRIPT_DIR/remote_oracle.sh" restart sensex' # Convenience forwarder to Oracle Sensex
alias v.wa='bash "$SCRIPT_DIR/remote_vivek.sh" restart whatsapp' # Restart WhatsApp
alias v.nifty='bash "$SCRIPT_DIR/remote_vivek.sh" restart nifty' # Restart Nifty
alias v.all='bash "$SCRIPT_DIR/remote_vivek.sh" restart all'     # Restart EVERYTHING

# Vivek Hard Restarts (Clear Logs) - Add '.y'
alias v.ret.y='bash "$SCRIPT_DIR/remote_vivek.sh" restart ret y'
alias v.sell.y='bash "$SCRIPT_DIR/remote_vivek.sh" restart sell y'
alias v.sell_1.y='bash "$SCRIPT_DIR/remote_oracle.sh" restart selling_1 y'
alias v.sen.y='bash "$SCRIPT_DIR/remote_oracle.sh" restart sensex y'
alias v.wa.y='bash "$SCRIPT_DIR/remote_vivek.sh" restart whatsapp y'
alias v.nifty.y='bash "$SCRIPT_DIR/remote_vivek.sh" restart nifty y'
alias v.all.y='bash "$SCRIPT_DIR/remote_vivek.sh" restart all y'

# Vivek Single Bot Sync
alias v.ret.u='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/retire/ deshpande_vivek@35.237.249.135:/home/deshpande_vivek/retire/'
alias v.ret.d='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store deshpande_vivek@35.237.249.135:/home/deshpande_vivek/retire/ $HOME/ICICI_Direct/Google/retire/'
alias v.sell.u='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/selling/ deshpande_vivek@35.237.249.135:/home/deshpande_vivek/selling/'
alias v.sell.d='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store deshpande_vivek@35.237.249.135:/home/deshpande_vivek/selling/ $HOME/ICICI_Direct/Google/selling/'
alias v.wa.u='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/whatsapp/ deshpande_vivek@35.237.249.135:/home/deshpande_vivek/whatsapp/'
alias v.wa.d='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store deshpande_vivek@35.237.249.135:/home/deshpande_vivek/whatsapp/ $HOME/ICICI_Direct/Google/whatsapp/'
alias v.nifty.u='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --exclude="*" $HOME/ICICI_Direct/nifty/ deshpande_vivek@35.237.249.135:/home/deshpande_vivek/nifty/'
alias v.nifty.d='rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store deshpande_vivek@35.237.249.135:/home/deshpande_vivek/nifty/ $HOME/ICICI_Direct/Google/nifty/'

# Upload then restart only if upload succeeds
alias v.ret.ur='v.ret.u && v.ret'
alias v.sell.ur='v.sell.u && v.sell'
alias v.wa.ur='v.wa.u && v.wa'
alias v.nifty.ur='v.nifty.u && v.nifty'

alias s.rsi.ur='s.rsi.u && s.rs'
alias s.sen.ur='s.sen.u && s.sen'

alias o.rsi.ur='o.rsi.u && o.rsi'
alias o.sell_1.ur='o.sell_1.u && o.sell_1'
alias o.sen.ur='o.sen.u && o.sen'

# --- SURESH (AWS) ---
alias s.st='bash "$SCRIPT_DIR/remote_suresh.sh" status'
alias s.rs='bash "$SCRIPT_DIR/remote_suresh.sh" restart'          # Restart Algo
alias s.rs.y='bash "$SCRIPT_DIR/remote_suresh.sh" restart y'      # Restart + Clear Logs
alias s.sen='bash "$SCRIPT_DIR/remote_suresh.sh" restart sensex'  # Restart Sensex
alias s.sen.y='bash "$SCRIPT_DIR/remote_suresh.sh" restart sensex y'
alias s.setup='bash "$SCRIPT_DIR/remote_suresh.sh" setup'

# Suresh Single Bot Sync
alias s.rsi.u='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/mod_rsi/ ubuntu@140.245.15.195:/home/ubuntu/mod_rsi/'
alias s.rsi.d='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store ubuntu@140.245.15.195:/home/ubuntu/mod_rsi/ $HOME/ICICI_Direct/Ubentu/suresh/algo_suresh/'
alias s.sen.u='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/sensex_suresh/ ubuntu@140.245.15.195:/home/ubuntu/sensex_suresh/'
alias s.sen.d='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store ubuntu@140.245.15.195:/home/ubuntu/sensex_suresh/ $HOME/ICICI_Direct/Ubentu/suresh/sensex_suresh/'

# Oracle Single Bot Sync
alias o.bin.u='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/binance/ ubuntu@80.225.215.187:/home/ubuntu/binance/'
alias o.bin.d='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store ubuntu@80.225.215.187:/home/ubuntu/binance/ $HOME/ICICI_Direct/Google/binance/'
alias o.rsi.u='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/mod_rsi/ ubuntu@80.225.215.187:/home/ubuntu/mod_rsi/'
alias o.rsi.d='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store ubuntu@80.225.215.187:/home/ubuntu/mod_rsi/ $HOME/ICICI_Direct/Google/mod_rsi/'
alias o.sell_1.u='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/selling_1/ ubuntu@80.225.215.187:/home/ubuntu/selling_1/'
alias o.sell_1.d='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store ubuntu@80.225.215.187:/home/ubuntu/selling_1/ $HOME/ICICI_Direct/Google/selling_1/'
alias o.sen.u='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=FONSEScripMaster.csv --include="*.py" --include="*.json" --include="*.sh" --include="*.csv" --include="requirements.txt" --exclude="*" $HOME/ICICI_Direct/sensex/ ubuntu@80.225.215.187:/home/ubuntu/sensex/'
alias o.sen.d='rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store ubuntu@80.225.215.187:/home/ubuntu/sensex/ $HOME/ICICI_Direct/Google/sensex/'

# --- BANDU (GCP) ---
alias b.st='bash "$SCRIPT_DIR/remote_bandu.sh" status'
alias b.setup='bash "$SCRIPT_DIR/remote_bandu.sh" setup'
# NOTE: Restart aliases for Bandu are in the 'RECENTLY ADDED' section at the end of this file.

# === ⚡ QUICK ACCESS & KILL ===
alias v='bash "$SCRIPT_DIR/remote_vivek.sh"'
alias b='bash "$SCRIPT_DIR/remote_bandu.sh"'
alias s='bash "$SCRIPT_DIR/remote_suresh.sh"'
alias o='bash "$SCRIPT_DIR/remote_oracle.sh"'

alias v.k='bash "$SCRIPT_DIR/remote_vivek.sh" kill'
alias v.k.all='bash "$SCRIPT_DIR/remote_vivek.sh" kill all'

alias b.k='bash "$SCRIPT_DIR/remote_bandu.sh" kill'
alias b.k.all='bash "$SCRIPT_DIR/remote_bandu.sh" kill all'

alias s.k='bash "$SCRIPT_DIR/remote_suresh.sh" kill'
alias s.k.all='bash "$SCRIPT_DIR/remote_suresh.sh" kill all'

alias o.k='bash "$SCRIPT_DIR/remote_oracle.sh" kill'
alias o.k.all='bash "$SCRIPT_DIR/remote_oracle.sh" kill all'

# Base Commands (for manual args)
alias rvivek='bash "$SCRIPT_DIR/remote_vivek.sh"'
alias rsuresh='bash "$SCRIPT_DIR/remote_suresh.sh"'
alias rbandu='bash "$SCRIPT_DIR/remote_bandu.sh"'

# === 🛠️ MAINTENANCE & LEGACY ===
alias cleanhist='bash "$SCRIPT_DIR/remove_duplicate.sh"'

# Legacy Syncs (For reference)
alias syncgemini='bash "$SCRIPT_DIR/sync_gemini.sh"'
alias syncgdrive='bash "$SCRIPT_DIR/syn_vivek.sh"'
alias syncbandu='bash "$SCRIPT_DIR/bandu_vivekmac.sh"'
alias syncsuresh='bash "$SCRIPT_DIR/suresh_vivekmac.sh"'
alias syncvivek='bash "$SCRIPT_DIR/vivek_vivekmac.sh"'

# Google/AWS Direct Uploads
alias to_vivek='bash "$SCRIPT_DIR/to_google.sh"'
alias to_bandu='bash "$SCRIPT_DIR/to_google_bandu.sh"'
alias to_suresh='bash "$SCRIPT_DIR/ToAWS_suresh.sh"'

# === 🆕 RECENTLY ADDED ALIASES (for Bandu) ===
# Refactored aliases to support multiple projects on the Bandu remote.

# Bandu Restarts (Default: Keep Logs)
alias b.rsi='bash "$SCRIPT_DIR/remote_bandu.sh" restart rsi'
alias b.sell_1='bash "$SCRIPT_DIR/remote_bandu.sh" restart sell_1'
alias b.all='bash "$SCRIPT_DIR/remote_bandu.sh" restart all'

# Bandu Hard Restarts (Clear Logs) - Add '.y'
alias b.rsi.y='bash "$SCRIPT_DIR/remote_bandu.sh" restart rsi y'
alias b.sell_1.y='bash "$SCRIPT_DIR/remote_bandu.sh" restart sell_1 y'
alias b.all.y='bash "$SCRIPT_DIR/remote_bandu.sh" restart all y'

# === 🖥️ DIRECT SSH CONNECTIONS ===
alias ssh_o='ssh oracle' # Oracle VM via ~/.ssh/config
alias ssh_s_o='ssh suresh_oracle' # Suresh Oracle VM via ~/.ssh/config
alias ssh_o2='ssh -i /Users/vivek/icici_direct/key/oracle2/ssh-key-2026-02-11.key ubuntu@155.248.244.211' # second oracle VM instantance

# --- ORACLE (GCP) ---
alias o.st='bash "$SCRIPT_DIR/remote_oracle.sh" status'            # Check Health
alias o.setup='bash "$SCRIPT_DIR/remote_oracle.sh" setup'

# Oracle Restarts (Default: Keep Logs)
alias o.rsi='bash "$SCRIPT_DIR/remote_oracle.sh" restart rsi'        # Restart mod_rsi
alias o.sell_1='bash "$SCRIPT_DIR/remote_oracle.sh" restart selling_1' # Restart Selling_1
alias o.sen='bash "$SCRIPT_DIR/remote_oracle.sh" restart sensex'     # Restart Sensex

# Oracle Hard Restarts (Clear Logs) - Add '.y'
alias o.rsi.y='bash "$SCRIPT_DIR/remote_oracle.sh" restart rsi y'
alias o.sell_1.y='bash "$SCRIPT_DIR/remote_oracle.sh" restart selling_1 y'
alias o.sen.y='bash "$SCRIPT_DIR/remote_oracle.sh" restart sensex y'

# Oracle Combined Restarts (mod_rsi + Selling_1)
alias o.r='o.rsi && o.sell_1 && o.sen'
alias o.r.y='o.rsi.y && o.sell_1.y && o.sen.y'

# === 📦 MANUAL INDIVIDUAL BOT SYNC COMMANDS ===
# Use these when you want to sync only one bot, without changing existing aliases like `v.d`.

# --- Vivek GCP: RETIRE only ---
# Download only RETIRE
# rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" \
#   --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
#   deshpande_vivek@35.237.249.135:/home/deshpande_vivek/retire/ \
#   $HOME/ICICI_Direct/Google/retire/

# Upload only RETIRE
# rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" \
#   --exclude=FONSEScripMaster.csv \
#   --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
#   --exclude='*' \
#   $HOME/ICICI_Direct/retire/ \
#   deshpande_vivek@35.237.249.135:/home/deshpande_vivek/retire/

# --- Suresh Oracle: mod_rsi only ---
# Download only mod_rsi
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" \
#   --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
#   ubuntu@80.225.197.254:/home/ubuntu/mod_rsi/ \
#   $HOME/ICICI_Direct/Ubentu/suresh/algo_suresh/

# Upload only mod_rsi
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" \
#   --exclude=FONSEScripMaster.csv \
#   --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
#   --exclude='*' \
#   $HOME/ICICI_Direct/algo_suresh/ \
#   ubuntu@80.225.197.254:/home/ubuntu/mod_rsi/

# --- Oracle: mod_rsi only ---
# Download only mod_rsi
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" \
#   --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
#   ubuntu@80.225.215.187:/home/ubuntu/mod_rsi/ \
#   $HOME/ICICI_Direct/Google/mod_rsi/

# Upload only mod_rsi
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" \
#   --exclude=FONSEScripMaster.csv \
#   --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
#   --exclude='*' \
#   $HOME/ICICI_Direct/mod_rsi/ \
#   ubuntu@80.225.215.187:/home/ubuntu/mod_rsi/

# --- Oracle: selling_1 only ---
# Download only selling_1
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" \
#   --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
#   ubuntu@80.225.215.187:/home/ubuntu/selling_1/ \
#   $HOME/ICICI_Direct/Google/selling_1/

# Upload only selling_1
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" \
#   --exclude=FONSEScripMaster.csv \
#   --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
#   --exclude='*' \
#   $HOME/ICICI_Direct/selling_1/ \
#   ubuntu@80.225.215.187:/home/ubuntu/selling_1/

# --- Oracle: binance only ---
# Download only binance
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" \
#   --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
#   ubuntu@80.225.215.187:/home/ubuntu/binance/ \
#   $HOME/ICICI_Direct/Google/binance/

# Upload only binance
# rsync -avz -e "ssh -i $HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" \
#   --exclude=FONSEScripMaster.csv \
#   --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
#   --exclude='*' \
#   $HOME/ICICI_Direct/binance/ \
#   ubuntu@80.225.215.187:/home/ubuntu/binance/



# Download:

# rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=.git --exclude=__pycache__ --exclude=.DS_Store deshpande_vivek@35.237.249.135:/home/deshpande_vivek/whatsapp/ $HOME/ICICI_Direct/Google/whatsapp/

 # Upload:

# rsync -avz -e "ssh -i $HOME/.ssh/gcp_key" --exclude=FONSEScripMaster.csv --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' --exclude='*' $HOME/ICICI_Direct/whatsapp/ deshpande_vivek@35.237.249.135:/home/deshpande_vivek/whatsapp/
