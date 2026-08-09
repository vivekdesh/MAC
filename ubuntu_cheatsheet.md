# Ubuntu & Remote Server Cheatsheet

## Table of Contents

- [1. Connecting via SSH](#1-connecting-via-ssh)
  - [Google Cloud Platform (GCP)](#google-cloud-platform-gcp)
  - [Amazon Web Services (AWS) & Other SSH Connections](#amazon-web-services-aws--other-ssh-connections)
  - [SSH Config for Simpler Connections](#ssh-config-for-simpler-connections)
- [2. File Transfer (SCP)](#2-file-transfer-scp)
- [2A. File Transfer (RSYNC Bot Sync)](#2a-file-transfer-rsync-bot-sync)
  - [Quick Setup Variables](#quick-setup-variables)
  - [Download One Bot](#download-one-bot)
  - [Upload One Bot](#upload-one-bot)
  - [2B. Program Restart Agent Deploy](#2b-program-restart-agent-deploy)
  - [Local Sync](#local-sync)
  - [One-Shot Verification](#one-shot-verification)
  - [Google VM systemd](#google-vm-systemd)
  - [Oracle VM systemd](#oracle-vm-systemd)
  - [Suresh VM systemd](#suresh-vm-systemd)
  - [Logs and Control](#logs-and-control)
  - [Current Bot Paths](#current-bot-paths)
- [3. Process Management](#3-process-management)
  - [Finding Processes](#finding-processes)
  - [Killing Processes](#killing-processes)
- [4. Using Tmux (Terminal Multiplexer)](#4-using-tmux-terminal-multiplexer)
  - [Session Management](#session-management)
  - [Attaching to Sessions](#attaching-to-sessions)
  - [Interacting with Sessions](#interacting-with-sessions)
  - [Capturing a Pane's Content](#capturing-a-panes-content)
- [5. Common Workflow Scripts](#5-common-workflow-scripts)
  - [Running Paper Trade](#running-paper-trade)
  - [Running Single Leg Trader](#running-single-leg-trader)
  - [Running mod_rsi Scripts](#running-mod_rsi-scripts)
- [6. General System Commands](#6-general-system-commands)
  - [System Maintenance](#system-maintenance)
  - [File Operations](#file-operations)
  - [Environment](#environment)
- [7. Bash History Commands](#7-bash-history-commands)
  - [Extra Useful History Commands](#extra-useful-history-commands)
  
  nano commands for editing files in the terminal:
  ngrok session details and its TMUX:

  # 🛠 Terminal Log Cleanup Guide
  



This document provides a quick reference for common commands used to manage and interact with remote Ubuntu servers on GCP and AWS.

---

## 1. Connecting via SSH

### Google Cloud Platform (GCP)

These commands are for setting up and connecting to a GCP instance via the `gcloud` CLI.

1.  **Log in to your Google Account:**
    ```bash
    gcloud auth login
    ```

2.  **Configure the `gcloud` CLI for your project:**
    ```bash
    # List available projects (optional)
    gcloud projects list

    # Set your project ID
    gcloud config set project composed-night-352914

    # Set the default region and zone
    gcloud config set compute/region us-east1
    gcloud config set compute/zone us-east1-c
    ```

3.  **List your VM instances to get their IP addresses:**
    ```bash
    gcloud compute instances list
    ```
    *Example Output:*
    ```
    NAME                      ZONE        MACHINE_TYPE  PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP     STATUS
    instance-20251009-150038  us-east1-c  e2-micro                   10.142.0.2   35.231.255.150  RUNNING
    ```

4.  **Add your local SSH public key to the instance's metadata:**
    ```bash
    gcloud compute instances add-metadata instance-20251009-150038 \
      --zone=us-east1-c \
      --metadata ssh-keys="deshpande_vivek:$(cat ~/.ssh/gcp_key.pub)"
    ```

5.  **Connect to the instance:**
    ```bash
    ssh -o ServerAliveInterval=60 -i ~/.ssh/gcp_key deshpande_vivek@34.26.75.26
    ```

### Amazon Web Services (AWS) & Other SSH Connections

This section contains connection strings for various users and servers.

*   **Suresh's AWS:**
    ```bash
    # From Windows
    ssh -i "C:\Users\1087135\AWS\soch12.pem" ubuntu@16.171.172.182
    ssh -i "C:\Users\Developer\AWS\soch12.pem" ubuntu@16.171.172.182

    # From Vivek's MAC
    ssh -i "/Users/vivek/ICICI_Direct/Key/soch12.pem" ubuntu@16.171.172.182
    ```

*   **Vivek's AWS:**
    ```bash
    # From Windows
    ssh -i "C:\Users\1087135\AWS\vivek.pem" ubuntu@3.107.179.177
    ssh -i "C:\Users\Developer\AWS\vivek.pem" ubuntu@3.107.179.177

    # From Vivek's MAC
    ssh -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" ubuntu@52.63.40.205
    ssh -o ServerAliveInterval=60 -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" ubuntu@52.63.40.205
    ssh -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" ubuntu@3.27.146.97
    ```

*   **Priya's MAC:**
    ```bash
    ssh -i "/Users/priyadeshpande/Desktop/ICICI_Direct/Key/vivek.pem" ubuntu@13.55.94.0
    ssh -i "/Users/priyadeshpande/Desktop/ICICI_Direct/Key/soch12.pem" ubuntu@16.171.172.182
    ```

### SSH Config for Simpler Connections

To avoid typing the full command every time, you can create an alias in your `~/.ssh/config` file.

1.  **Edit the config file:**
    ```bash
    nano ~/.ssh/config
    ```
## Public key on MAC
vivek@vivek mac % cat ~/.ssh/gcp_key.pub

ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCUuTdy8IiCdC/wP/9WG3mq7smUCmCZqvgX9xJJPsJdUuLrGUxuFHFlGkb533TL1CqdUvu3rthZu/G3NNyF//+SemXy0xmKcvmB+06xgROyzmCgwZYxm/bAnkWG6ZSlTDKxMCpjohp4/jUW0suMU8LX49NE0g4kR1p7Y1Rft+HlEcvQBsei5MngZkqdtLBSXbvkIHhjj6h6RcDAOok961MWf4NtIecp595dEJzvIuEc2snKl7a2Hx+/GfFryJSwTJWfGknhb9OAtRYIBqhd71q8XbcyZdI9Q6OBmzELOFtKfOtUpYVOGUxEoKkvkZfR29/tqoAVMCsD/2PIcK/AJaM7Hcb2Xk9ByGUKhEiU+vyBzRzataBa/mJxpNUEK1efM+94PbYH8vt2OSoTsEFR1OwMYVHhef0mILEg/tsp6haI/uRFhRF5TvRldA0OBQZ/L2JcA2i0KQHsbcnPrxn4Hq5fPaLLzW8mmBLPLQuz+UwsA4qNU9fgHWhisUmzj8SrGBU= vivek@gcp

2.  **Add a host entry:**
    ```
    Host vivek     
    HostName 34.26.75.26
    User deshpande_vivek
    IdentityFile ~/.ssh/gcp_key
    ServerAliveInterval 60

Host vinay
        HostName 35.196.102.57
        User vivek
        IdentityFile ~/.ssh/gcp_key
        ServerAliveInterval 60

3.  **Connect with the alias:**
    ```bash
    ssh vivek 
    ssh vinay 
    vivek - for vivek and Vinay for vinay
    
    ```

---

## 2. File Transfer (SCP)

Use `scp` (secure copy) to transfer files between your local machine and the remote server.

*   **Syntax:** `scp -i <key_file> <local_path> <user>@<host>:<remote_path>`

*   **Example (MAC to Ubuntu):**
    ```bash
    # Copy all .py files from local webhook dir to remote webhook dir
    scp -i "/Users/priyadeshpande/Desktop/ICICI_Direct/Key/vivek.pem" "/Users/priyadeshpande/Desktop/ICICI_Direct/webhook/*.py" ubuntu@54.206.20.57:/home/ubuntu/webhook

    # Copy all .json files
    scp -i "/Users/priyadeshpande/Desktop/ICICI_Direct/Key/vivek.pem" "/Users/priyadeshpande/Desktop/ICICI_Direct/webhook/*.json" ubuntu@54.206.20.57:/home/ubuntu/webhook

    # Copy specific symbol and xlsx files
    scp -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" /Users/vivek/ICICI_Direct/Ubentu/webhook/symbol*.json ubuntu@54.206.20.57:/home/ubuntu/webhook/
    scp -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" /Users/vivek/ICICI_Direct/Ubentu/webhook/*.xlsx ubuntu@54.206.20.57:/home/ubuntu/webhook/
    ```

---

## 2A. File Transfer (RSYNC Bot Sync)

Use `rsync` when you want to download or upload a single bot without running the full sync scripts.

Why `rsync`:
- faster than repeated `scp`
- updates only changed files
- safer for bot-by-bot work

### Quick Setup Variables

Set these once in the terminal before running the commands below:

```bash
KEY_GCP="$HOME/.ssh/gcp_key"
GCP="deshpande_vivek@34.26.75.26:/home/deshpande_vivek"

KEY_SUR="$HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key"
SUR="ubuntu@80.225.197.254:/home/ubuntu"

KEY_ORA="$HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key"
ORA="ubuntu@80.225.215.187:/home/ubuntu"
```

Common pattern:

```bash
# Download one bot
rsync -avz -e "ssh -i <KEY>" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  <USER@HOST:/remote/path/> \
  <local/path/>

# Upload one bot
rsync -avz -e "ssh -i <KEY>" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  <local/path/> \
  <USER@HOST:/remote/path/>
```

### Download One Bot

Examples:

```bash
# Vivek GCP: whatsapp
rsync -avz -e "ssh -i $KEY_GCP" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $GCP/whatsapp/ \
  $HOME/ICICI_Direct/Google/whatsapp/

# Vivek GCP: retire
rsync -avz -e "ssh -i $KEY_GCP" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $GCP/retire/ \
  $HOME/ICICI_Direct/Google/retire/

# Vivek GCP: selling
rsync -avz -e "ssh -i $KEY_GCP" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $GCP/selling/ \
  $HOME/ICICI_Direct/Google/selling/

# Suresh Oracle: mod_rsi
rsync -avz -e "ssh -i $KEY_SUR" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $SUR/mod_rsi/ \
  $HOME/ICICI_Direct/Ubentu/suresh/algo_suresh/

# Suresh Oracle: sensex_suresh
rsync -avz -e "ssh -i $KEY_SUR" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $SUR/sensex_suresh/ \
  $HOME/ICICI_Direct/Ubentu/suresh/sensex_suresh/

# Oracle: mod_rsi
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $ORA/mod_rsi/ \
  $HOME/ICICI_Direct/Google/mod_rsi/

# Oracle: selling_1
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $ORA/selling_1/ \
  $HOME/ICICI_Direct/Google/selling_1/

# Oracle: binance
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $ORA/binance/ \
  $HOME/ICICI_Direct/Google/binance/

# Oracle: sensex
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=.git --exclude=__pycache__ --exclude=.DS_Store \
  $ORA/sensex/ \
  $HOME/ICICI_Direct/Google/sensex/
```

### Upload One Bot

Examples:

```bash
# Vivek GCP: whatsapp
rsync -avz -e "ssh -i $KEY_GCP" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/whatsapp/ \
  $GCP/whatsapp/

# Vivek GCP: retire
rsync -avz -e "ssh -i $KEY_GCP" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/retire/ \
  $GCP/retire/

# Vivek GCP: selling
rsync -avz -e "ssh -i $KEY_GCP" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/selling/ \
  $GCP/selling/

# Suresh Oracle: mod_rsi
rsync -avz -e "ssh -i $KEY_SUR" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/algo_suresh/ \
  $SUR/mod_rsi/

# Suresh Oracle: sensex_suresh
rsync -avz -e "ssh -i $KEY_SUR" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/sensex_suresh/ \
  $SUR/sensex_suresh/

# Oracle: mod_rsi
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/mod_rsi/ \
  $ORA/mod_rsi/

# Oracle: selling_1
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/selling_1/ \
  $ORA/selling_1/

# Oracle: binance
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/binance/ \
  $ORA/binance/

# Oracle: sensex
rsync -avz -e "ssh -i $KEY_ORA" \
  --exclude=FONSEScripMaster.csv \
  --include='*.py' --include='*.json' --include='*.sh' --include='*.csv' \
  --exclude='*' \
  $HOME/ICICI_Direct/sensex/ \
  $ORA/sensex/
```

## 2B. Program Restart Agent Deploy

This is for the Google-Sheet-driven `Program_restart` controller.

Notes:
- local source folder: `/Users/vivek/ICICI_Direct/Program_restart`
- remote target on Google VM: `/home/deshpande_vivek/Program_restart`
- remote target on Oracle VM: `/home/ubuntu/Program_restart`
- both VMs already have `~/myenv` with `gspread`, `google-auth`, and `requests`
- use `~/myenv/bin/python`, not system `python3`

### Local Sync

Use the existing sync aliases after updating `sync_master.sh`:

```bash
v.u
o.u
```

These now copy `Program_restart` to both required VMs.

For Suresh VM:

```bash
s.u
```

### One-Shot Verification

Run once manually before enabling `systemd`.

Google VM:

```bash
ssh -i "$HOME/.ssh/gcp_key" deshpande_vivek@34.26.75.26
cd /home/deshpande_vivek
/home/deshpande_vivek/myenv/bin/python /home/deshpande_vivek/Program_restart/restart_agent.py --vm google_vm --once
```

Oracle VM:

```bash
ssh -i "$HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" ubuntu@80.225.215.187
cd /home/ubuntu
/home/ubuntu/myenv/bin/python /home/ubuntu/Program_restart/restart_agent.py --vm oracle_vm --once
```

Suresh VM:

```bash
ssh -i "$HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" ubuntu@80.225.197.254
cd /home/ubuntu
/home/ubuntu/venv/bin/python /home/ubuntu/Program_restart/restart_agent.py --vm suresh_vm --once
```

### Google VM systemd

```bash
sudo tee /etc/systemd/system/program-restart-google.service >/dev/null <<'EOF'
[Unit]
Description=Program Restart Agent (Google VM)
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=deshpande_vivek
WorkingDirectory=/home/deshpande_vivek
ExecStart=/home/deshpande_vivek/myenv/bin/python /home/deshpande_vivek/Program_restart/restart_agent.py --vm google_vm
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now program-restart-google.service
sudo systemctl status program-restart-google.service
```

### Oracle VM systemd

```bash
sudo tee /etc/systemd/system/program-restart-oracle.service >/dev/null <<'EOF'
[Unit]
Description=Program Restart Agent (Oracle VM)
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/myenv/bin/python /home/ubuntu/Program_restart/restart_agent.py --vm oracle_vm
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now program-restart-oracle.service
sudo systemctl status program-restart-oracle.service
```

### Suresh VM systemd

```bash
sudo tee /etc/systemd/system/program-restart-suresh.service >/dev/null <<'EOF'
[Unit]
Description=Program Restart Agent (Suresh VM)
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/venv/bin/python /home/ubuntu/Program_restart/restart_agent.py --vm suresh_vm
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now program-restart-suresh.service
sudo systemctl status program-restart-suresh.service
```

### Logs and Control

Purpose:
- use these commands after the service is already installed
- use `status` to check whether the agent is alive
- use `journalctl` to read recent logs and errors
- use `restart` only if you intentionally want to restart the sheet agent service
- use `stop` only if you intentionally want to stop the sheet agent service

Important warning:
- on the current Google and Oracle setup, the restart agent may still own child tmux/bot processes it started
- because of that, `systemctl stop` or `systemctl restart` can affect running bot processes
- for normal trading control, use the Google Sheet rows, not `systemctl restart`

Google VM:

```bash
sudo systemctl restart program-restart-google.service
sudo systemctl stop program-restart-google.service
sudo systemctl status program-restart-google.service
journalctl -u program-restart-google.service -f
```

Oracle VM:

```bash
sudo systemctl restart program-restart-oracle.service
sudo systemctl stop program-restart-oracle.service
sudo systemctl status program-restart-oracle.service
journalctl -u program-restart-oracle.service -f
```

Suresh VM:

```bash
sudo systemctl restart program-restart-suresh.service
sudo systemctl stop program-restart-suresh.service
sudo systemctl status program-restart-suresh.service
journalctl -u program-restart-suresh.service -f
```

### Remote Checks From Mac

Purpose:
- use these from your Mac when you want a quick remote health check
- these do not require opening an interactive SSH shell
- first run the `systemctl status` command
- if the output is not clear, run the matching `journalctl` command

What the commands mean:
- `systemctl status ...` shows whether the service is `active`, `failed`, or `stopped`
- `journalctl -u ... -n 50` shows the last 50 service log lines
- `--no-pager` prints directly to the terminal
- `-l` shows full log lines without truncation

Suresh VM:

```bash
ssh -i "$HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" ubuntu@80.225.197.254 'systemctl status program-restart-suresh.service --no-pager -l'
ssh -i "$HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" ubuntu@80.225.197.254 'journalctl -u program-restart-suresh.service -n 50 --no-pager'
```

Google VM:

```bash
ssh -i "$HOME/.ssh/gcp_key" deshpande_vivek@34.26.75.26 'systemctl status program-restart-google.service --no-pager -l'
ssh -i "$HOME/.ssh/gcp_key" deshpande_vivek@34.26.75.26 'journalctl -u program-restart-google.service -n 50 --no-pager'
```

Oracle VM:

```bash
ssh -i "$HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" ubuntu@80.225.215.187 'systemctl status program-restart-oracle.service --no-pager -l'
ssh -i "$HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" ubuntu@80.225.215.187 'journalctl -u program-restart-oracle.service -n 50 --no-pager'
```

Oracle2 VM! 

```bash
ssh -i "$HOME/ICICI_Direct/Key/oracle2/ssh-key-2026-02-11.key" ubuntu@155.248.244.211 'systemctl status program-restart-oracle2.service --no-pager -l'
ssh -i "$HOME/ICICI_Direct/Key/oracle2/ssh-key-2026-02-11.key" ubuntu@155.248.244.211 'journalctl -u program-restart-oracle2.service -n 50 --no-pager'
```

### Remote Restart From Mac

Purpose:
- use these from your Mac when you need to restart only the `Program_restart` agent service on a VM
- use this after syncing updated `Program_restart` code to the VM
- for Google and Oracle, do this only in a safe window because the current service can still have attached bot processes

Google VM:

```bash
ssh -i "$HOME/.ssh/gcp_key" deshpande_vivek@34.26.75.26 'sudo systemctl restart program-restart-google.service'
```

Oracle VM:

```bash
ssh -i "$HOME/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key" ubuntu@80.225.215.187 'sudo systemctl restart program-restart-oracle.service'
```

Suresh VM:

```bash
ssh -i "$HOME/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key" ubuntu@80.225.197.254 'sudo systemctl restart program-restart-suresh.service'
```


Because the Pub/Sub listener is running as a systemd background service (and not inside the tmux sessions where your main trading bots live), you can restart it anytime using sudo systemctl restart without interrupting the bots.

1. Google VM (Selling / Retire / Nifty) (Note: Replace the IP below with your current Google VM IP if it changes).

bash


ssh -i ~/.ssh/gcp_key deshpande_vivek@34.26.75.26 'sudo systemctl restart icici-fast-param-subscriber'

2. Suresh VM (AWS - Suresh Mod RSI / Sensex)

bash


ssh -i /Users/vivek/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key ubuntu@140.245.15.195 'sudo systemctl restart icici-fast-param-subscriber'
3. Oracle VM (Mod RSI / Sensex / Selling 1)

bash


ssh -i /Users/vivek/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key ubuntu@80.225.215.187 'sudo systemctl restart icici-fast-param-subscriber'

Cheatbook Addition (Oracle2 - Whatsapp)
Since whatsapp lives on oracle2, here are the specific cheatbook commands to manage its subscriber if you ever face parameter freezes in the future (this doesn't require killing tmux either!):

bash


# 1. SSH into Oracle2
ssh -i /Users/vivek/ICICI_Direct/Key/oracle2/ssh-key-2026-02-11.key ubuntu@155.248.244.211
# 2. Restart the Fast Parameter Service
sudo systemctl restart icici-fast-param-subscriber.service
# 3. Check Live Logs (Press Ctrl+C to exit)
sudo journalctl -u icici-fast-param-subscriber.service -f


You can run these commands from your local Mac terminal anytime you push changes to fast_parameter_handler.py or want to clear out a stuck Pub/Sub queue!

Google Sheet test rows:
- `17` = `google_vm status` = equivalent to `v.st`
- `18` = `google_vm setup` = equivalent to `v.setup`
- `19` = `oracle_vm status` = equivalent to `o.st`
- `20` = `oracle_vm setup` = equivalent to `o.setup`
- `21` = `suresh_vm all Y` = equivalent to `s.rs.y`
- `22` = `suresh_vm all N` = equivalent to `s.rs`
- `23` = `suresh_vm status` = equivalent to `s.st`
- `24` = `suresh_vm setup` = equivalent to `s.setup`

How to use the sheet rows:
- set the row `Execute` cell from `0` to `1`
- wait up to `60` seconds for the poll cycle
- do not fill `Status`, `Ack_Time`, `Ack_By`, or `Result_Message` yourself
- for `status` and `setup` rows, leave `Clear_Logs` as `N`
- for `all` rows, use `Y` if you want log clearing and `N` if you do not

What each row type does:
- `status` checks tmux/process health and writes readable output to `Results`
- `setup` runs the tmux/session setup script on that VM
- `all Y` runs the full restart with log clearing
- `all N` runs the full restart without log clearing

Expected behavior after setting `Execute=1`:
- the agent runs the local VM command
- `Execute` returns to `0`
- `Commands` gets `Status`, `Ack_Time`, `Ack_By`, `Result_Message`
- `Status` sheet updates latest state
- `Results` sheet gets readable output/history

### Current Bot Paths

Use this table to map each bot quickly.

| Server | Bot | Remote Path | Local Path |
|---|---|---|---|
| Vivek GCP | `retire` | `/home/deshpande_vivek/retire/` | `$HOME/ICICI_Direct/Google/retire/` for download, `$HOME/ICICI_Direct/retire/` for upload |
| Vivek GCP | `whatsapp` | `/home/deshpande_vivek/whatsapp/` | `$HOME/ICICI_Direct/Google/whatsapp/` for download, `$HOME/ICICI_Direct/whatsapp/` for upload |
| Vivek GCP | `selling` | `/home/deshpande_vivek/selling/` | `$HOME/ICICI_Direct/Google/selling/` for download, `$HOME/ICICI_Direct/selling/` for upload |
| Suresh Oracle | `mod_rsi` | `/home/ubuntu/mod_rsi/` | `$HOME/ICICI_Direct/Ubentu/suresh/algo_suresh/` for download, `$HOME/ICICI_Direct/algo_suresh/` for upload |
| Suresh Oracle | `sensex_suresh` | `/home/ubuntu/sensex_suresh/` | `$HOME/ICICI_Direct/Ubentu/suresh/sensex_suresh/` for download, `$HOME/ICICI_Direct/sensex_suresh/` for upload |
| Oracle | `mod_rsi` | `/home/ubuntu/mod_rsi/` | `$HOME/ICICI_Direct/Google/mod_rsi/` for download, `$HOME/ICICI_Direct/mod_rsi/` for upload |
| Oracle | `selling_1` | `/home/ubuntu/selling_1/` | `$HOME/ICICI_Direct/Google/selling_1/` for download, `$HOME/ICICI_Direct/selling_1/` for upload |
| Oracle | `binance` | `/home/ubuntu/binance/` | `$HOME/ICICI_Direct/Google/binance/` for download, `$HOME/ICICI_Direct/binance/` for upload |
| Oracle | `sensex` | `/home/ubuntu/sensex/` | `$HOME/ICICI_Direct/sensex/` for both download and upload |

---

## 3. Process Management

### Finding Processes

*   **Find processes by name or command:**
    ```bash
    # Show all processes containing the word "python"
    ps aux | grep python

    # Show processes containing "webhook"
    ps aux | grep webhook

    # Find PIDs of all processes with "vivek" in the command
    pgrep -f "vivek"

    # Find PIDs and show the full command line
    pgrep -af single
    ```

### Killing Processes

*   **Kill a specific PID:**
    ```bash
    kill <PID>
    kill -9 <PID> # Force kill
    ```

*   **Kill all processes matching a name (use with caution):**
    ```bash
    # Kill all processes with "paper_trade" in the command line
    pkill -f paper_trade
    ```

*   **Safe Kill Pipeline (Recommended):** Find processes, filter out unwanted ones (like `grep` or `tmux`), and then kill.
    ```bash
    # Kill all "vivek" processes except for tmux itself
    pgrep -f "vivek" | grep -v "tmux" | xargs kill -9

    # Kill all "single" processes safely
    ps aux | grep single | grep -v grep | awk '{print $2}' | xargs -r kill -9
    ```

*   **Remote Kill from MAC:** Execute the kill command on the remote server via SSH.
    ```bash
    # Kill "single" processes remotely
    ssh -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" ubuntu@54.206.20.57 'ps aux | grep single | grep -v grep | awk '\''{print $2}'\'' | xargs -r kill -9'

    # Kill "paper" processes remotely
    ssh -i "/Users/vivek/ICICI_Direct/Key/vivek.pem" ubuntu@54.206.20.57 'ps aux | grep paper | grep -v grep | awk '\''{print $2}'\'' | xargs -r kill -9'
    ```

---

## 4. Using Tmux (Terminal Multiplexer)

### Session Management

*   **List running sessions:**
    ```bash
    tmux ls
    ```

*   **Create a new session:**
    ```bash
    tmux new -s <session_name>
    ```

*   **Kill a specific session:**
    ```bash
    tmux kill-session -t <session_name>
    ```

### Attaching to Sessions

*   **Attach to the last used session:**
    ```bash
    tmux attach
    ```

*   **Attach to a specific session by name:**
    ```bash
    tmux attach -t vivek
    ```

### Interacting with Sessions

*   **Send Keys to a Session:** Automate commands without attaching.
    ```bash
    # Send CTRL+C to the session named 'single' to stop a running script
    tmux send-keys -t single C-c

    # Send a series of commands to a session named 'pap'
    tmux send-keys -t pap "cd ~" Enter
    sleep 3
    tmux send-keys -t pap "source myenv/bin/activate" Enter
    sleep 3
    tmux send-keys -t pap "cd Algo_1" Enter
    sleep 3
    tmux send-keys -t pap "python vivek_paper.py" Enter
    ```

*   **Capture a Pane's Content:** Save the visible text in a tmux pane to a file.
    1.  Press `CTRL+B`
    2.  Press `:`
    3.  Type `capture-pane -S -` and press Enter. This captures the entire scrollback buffer.

---

## 5. Common Workflow Scripts

Example scripts for running trading algorithms inside tmux sessions.

### Running Paper Trade
```bash
# Kill previous instances
pkill -f paper_trade
# OR
ps -ef | grep "paper" | grep -v "tmux" | grep -v "grep" | awk '{print $2}' | xargs -r kill -9

# Start new session and run script
tmux new -s pap
sleep 3
tmux send-keys -t pap "cd ~" Enter
sleep 3
tmux send-keys -t pap "source myenv/bin/activate" Enter
sleep 3
tmux send-keys -t pap "cd Algo_1" Enter
sleep 3
tmux send-keys -t pap "python vivek_paper.py" Enter
```

### Running Single Leg Trader
```bash
# Kill previous instances
pkill -f single
# OR
ps -ef | grep "single" | grep -v "tmux" | grep -v "grep" | awk '{print $2}' | xargs -r kill -9

# Start new session and run script
tmux new -s sin
sleep 3
tmux send-keys -t sin "cd ~" Enter
sleep 3
tmux send-keys -t sin "source myenv/bin/activate" Enter
sleep 3
tmux send-keys -t sin "cd Algo_1" Enter
sleep 3
tmux send-keys -t sin "python vivek_single.py" Enter
```

### Running mod_rsi Scripts
```bash
# Kill vivek_RSI.py
pkill -f vivek_RSI.py

# Start vivek_RSI.py
tmux new -s rsi_trade
sleep 3
tmux send-keys -t rsi_trade "cd ~" Enter
sleep 3
tmux send-keys -t rsi_trade "source myenv/bin/activate" Enter
sleep 3
tmux send-keys -t rsi_trade "cd mod_rsi" Enter
sleep 3
tmux send-keys -t rsi_trade "python vivek_RSI.py" Enter

# ---

# Kill vivek_RSI_single.py
pkill -f vivek_RSI_single.py

# Start vivek_RSI_single.py
tmux new -s rsi_sin
sleep 3
tmux send-keys -t rsi_sin "cd ~" Enter
sleep 3
tmux send-keys -t rsi_sin "source myenv/bin/activate" Enter
sleep 3
tmux send-keys -t rsi_sin "cd mod_rsi" Enter
sleep 3
tmux send-keys -t rsi_sin "python vivek_RSI_single.py" Enter
```
---

## 6. General System Commands

### System Maintenance

# One-liner for regular maintenance

sudo apt update && sudo apt full-upgrade -y && sudo apt autoremove -y && sudo apt autoclean

# Reboot

sudo reboot

*   **Reboot the server:**
    ```bash
    sudo reboot
    ```
*   **Update and upgrade packages:**
    ```bash
    sudo apt update
    sudo apt upgrade
    ```

### File Operations

*   **View large files:**
    ```bash
    less very_large_log.txt
    more very_large_log.txt
    ```
*   **Empty a file without deleting it:**
    ```bash
    > filename.txt
    ```
*   **Rename a file:**
    ```bash
    mv paper_trade.py paper_trade_v2.py
    ```
*   **Check file modification time in seconds:**
    ```bash
    stat -c '%n %y' param*.json
    ```

### Environment

*   **Activate a Python virtual environment:**
    ```bash
    source myenv/bin/activate
    ```
*   **Activate a specific virtual environment from a project directory:**
    ```bash
    cd /Users/vivek/ICICI_Direct/
    source vivekmac/bin/activate
    ```
---

## 7. Bash History Commands

This section explains how to view, clear, back up, edit, and restore your Bash command history.

| Action | Command |
|:---|:---|
| View history | `history` |
| Clear session | `history -c` |
| Delete saved history | `rm ~/.bash_history` |
| Backup history | `history > ~/command_history.log` |
| Append to backup | `history >> ~/command_history.log` |
| Restore history | `cp ~/command_history.log ~/.bash_history` |
| Reload new history | `history -r` |

#### Extra Useful History Commands

*   **Delete a specific entry by line number:**
    ```bash
    history -d <number>
    ```
*   **Remove duplicates automatically:**
    ```bash
    export HISTCONTROL=ignoredups:erasedups
    ```
*   **Prevent saving empty or repeated commands:**
    ```bash
    export HISTIGNORE="&:[ ]*:exit"
    ```
*   **Disable saving history permanently (optional):**
    ```bash
    unset HISTFILE
    ```
### `nano` commands for editing files in the terminal:

On macOS Terminal, the `Option` (⌥) key acts as the `Meta` (Alt) key.

  1. Selection & Copy/Paste
   * Start/Stop Selection: Option + A (or Ctrl + 6)
       * Highlight text using the arrow keys.
   * Copy Selected Text: Option + 6
   * Cut Selected Text: Ctrl + K (Cuts the selection, or the entire line if nothing is selected)
   * Paste: Ctrl + U

  2. Searching
   * Search (Where Is): Ctrl + W
   * Find Next: Option + W
   * Search and Replace: Ctrl + \

  3. Navigation
   * Go to Start of File: Option + \
   * Go to End of File: Option + /
   * Go to Line Number: Ctrl + _ (Hold Control and Shift then press -)

  4. Saving & Exiting
   * Save Changes: Ctrl + O then press Return
   * Exit: Ctrl + X

  5. Undo/Redo
   * Undo: Option + U
   * Redo: Option + E

## ngrok session details and its TMUX
tmux new -s ngrok
ngrok http 3000


# 🛠 Terminal Log Cleanup Guide
**User:** Vivek | **System:** macOS / Ubuntu
**Date:** May 2026

This document serves as a reference for searching, reviewing, and safely deleting application log files across subfolders while managing macOS/Linux permission restrictions.

---

## delete log files in perticular folder (more than 3 days old!)
delete *.log files in /Users/vivek/ICICI_Direct/Google which age is more than 3 days
## Step 1: Test the Command (Dry Run)
find /Users/vivek/ICICI_Direct/Google -name "*.log" -type f -mtime +3

## Step 2: Execute the Deletion
## This will delete files permeantly:
find /Users/vivek/ICICI_Direct/Google -name "*.log" -type f -mtime +3 -delete

## This will Move to Trash
find /Users/vivek/ICICI_Direct/Google -name "*.log" -type f -mtime +3 -exec mv {} ~/.Trash/ \;


-type f: Ensures that only regular files are targeted (ignoring directories or symlinks).

-mtime +3: Filters for files whose content was last modified more than 3 days (3 * 24 hours) ago.

-delete: The action flag that permanently removes the matched files.
-exec: Tells the find utility to execute a secondary command on every single file it matches.

mv: The standard command-line utility used to move files.

{}: A placeholder that find automatically replaces with the name and path of the current file it is processing.

~/.Trash/: The destination path. The tilde (~) represents your home directory, and .Trash is the hidden folder where macOS stores trashed items.

\;: A required syntax marker that signals the end of the -exec command sequence.



## 1. Discovery Phase
Always list files first to ensure you are targeting the correct data.

```bash
# Find all app log files in the current directory and subfolders
find . -name "app_*.log" -type f
```

## 2. Moving to Trash (Reversible)
Use this when you want the safety of the "Recycle Bin" to restore files if needed.

### On macOS
Moves files to the user's local Trash folder.

```bash
# Standard move (may ask for confirmation on duplicates)
find . -name "app_*.log" -type f -exec mv {} ~/.Trash/ \;

# Forced move (overwrites duplicates already in Trash)
find . -name "app_*.log" -type f -exec mv -f {} ~/.Trash/ \;
```

### On Ubuntu/Linux
Uses the native system trash handler (handles naming conflicts better).

```bash
find . -name "app_*.log" -type f -exec gio trash {} \;
```

## 3. Permanent Deletion (Irreversible)
Use this when "Operation not permitted" errors occur or when Trash move fails.

```bash
# Deletes all found files immediately
sudo find . -name "app_*.log" -type f -delete
```

---

## 4. Time-Based Cleanup (Advanced)
Use `! -newermt` to target files older than a specific timestamp. This is useful for clearing logs from previous sessions or before a specific manual restart.

### Verification (Test First)
```bash
find /Users/vivek/ICICI_Direct/Google \
-type f \
-name "*.log" \
! -newermt "2026-05-13 12:35:00" \
-exec ls -lhT {} \;
```

### Execution (Delete)
```bash
find /Users/vivek/ICICI_Direct/Google \
-type f \
-name "*.log" \
! -newermt "2026-05-13 12:35:00" \
-delete
```



## see alias lets say 1 to8:
alias | grep "^alias [1-8]="