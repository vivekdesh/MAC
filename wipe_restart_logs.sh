#!/bin/bash

echo "======================================"
echo "🧹 WIPING RESTART AGENT LOGS 🧹"
echo "======================================"

# [1/5] Truncate restart agent logs to 0 bytes on remote Oracle VM
echo "[1/5] Wiping Oracle VM logs..."
ssh -i /Users/vivek/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key -o StrictHostKeyChecking=no ubuntu@80.225.215.187 'truncate -s 0 /home/ubuntu/Program_restart/restart_agent*.log'

# [2/5] Truncate restart agent logs to 0 bytes on remote Oracle2 VM
echo "[2/5] Wiping Oracle2 VM logs..."
ssh -i /Users/vivek/ICICI_Direct/Key/oracle2/ssh-key-2026-02-11.key -o StrictHostKeyChecking=no ubuntu@155.248.244.211 'truncate -s 0 /home/ubuntu/Program_restart/restart_agent*.log'

# [3/5] Truncate restart agent logs to 0 bytes on remote Vivek (Google GCP) VM
echo "[3/5] Wiping Vivek (Google) VM logs..."
ssh -i ~/.ssh/gcp_key -o StrictHostKeyChecking=no deshpande_vivek@34.26.75.26 'truncate -s 0 /home/deshpande_vivek/Program_restart/restart_agent*.log'

# [4/5] Truncate restart agent logs to 0 bytes on remote Suresh (AWS) VM
echo "[4/5] Wiping Suresh VM logs..."
ssh -i /Users/vivek/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key -o StrictHostKeyChecking=no ubuntu@140.245.15.195 'truncate -s 0 /home/ubuntu/Program_restart/restart_agent*.log'

# [5/5] Delete locally downloaded log files copied from the remote VMs
echo "[5/5] Deleting local MAC logs..."
rm -f /Users/vivek/ICICI_Direct/Google/Program_restart/restart_agent*.log
rm -f /Users/vivek/ICICI_Direct/Ubentu/suresh/Program_restart/restart_agent*.log

echo "======================================"
echo "✅ All restart logs successfully wiped!"
echo "======================================"
