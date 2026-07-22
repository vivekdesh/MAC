# Google Cloud Billing, Pub/Sub Safety, & Infrastructure Migration Learnings
**Date:** July 20, 2026
**Author:** AI Assistant / Vivek Deshpande

## 1. Google Cloud IPv4 Pricing Rules (2024 Update)
Google changed their global IP address pricing in February 2024. 
- **Before 2024:** Ephemeral IPs and Static IPs attached to a running VM were free.
- **After 2024:** **ALL** public IPv4 addresses are charged a base rate of ~$0.005/hour (approx ₹10 to ₹25 per day).
- **The Lesson:** Because an Ephemeral IP and a Static IP now cost the exact same amount of money, you should **always** use a Static IP for trading bots. Ephemeral IPs offer zero cost savings and introduce the massive risk of your IP randomly changing (which breaks your ICICI Direct whitelist).

## 2. How to Monitor and Investigate Billing Spikes
When you see an unexpected spike in your bill (like the jump to ₹132/day), do not panic. Use the Google Cloud Billing console to break down the exact source of the charge:
1. Go to **Google Cloud Console > Billing > Reports**.
2. Look at the **"Group by"** filter on the right side and set it to **"Service"**.
3. This will separate your bill into buckets. You will clearly see if a spike belongs to **Compute Engine** (your VMs) or **Cloud Run** (your serverless apps/PubSub listeners).
4. If the spike is in Cloud Run, it means a background process is looping.

## 3. The Cloud Run / Pub/Sub Infinite Loop Danger
During this session, we discovered a massive ₹118/day spike caused by Cloud Run. 
- **The Cause:** When a VM is turned off (like Vivek VM), it stops acknowledging Cloud Pub/Sub messages (like the emergency stop messages from `program_restart`). 
- **The Danger:** By default, Google Cloud retains unacknowledged messages for **7 days** and will aggressively retry sending them to Cloud Run, causing hundreds of thousands of unnecessary invocations and skyrocketing your bill.
- **The Fix:** We permanently updated all 5 of your Pub/Sub subscriptions (`icici-stop-ack-cloud-run`, `icici-stop-google-vm`, etc.) to have a **1-day maximum message retention duration (86,400 seconds)** and enabled exponential backoff. Now, even if a VM is offline, the retries will safely expire before they can ever cross the 2-million free tier threshold.

## 4. Temporary Traffic Migration (ICICI Unblocking)
When an IP address is blocked by ICICI and you are forced to wait for it to be unblocked (e.g., waiting for July 23rd at 10:38), you do not need complex network tunneling.
- **The Strategy:** Temporarily deploy the affected bots (`selling`, `retire`, `nifty`) to an already-whitelisted server (like Oracle2).
- **Execution:**
  1. **CRITICAL:** Kill the tmux sessions on the original VM first so bots do not run in duplicate.
  2. Add the bot folders to the `sync_master.sh` configuration for the new target VM.
  3. Run the sync command (e.g., `bash MAC/sync_master.sh oracle2 up`).
  4. Manually start the TMUX sessions on the new VM.
- **Rollback:** Once the original IP is unblocked, kill the temporary sessions, revert `sync_master.sh`, and restart the bots on their original home.

## 5. CPU & Memory Load Monitoring Plan
When running multiple bots on a single server, you must monitor resources to prevent freezes.
1. Open a terminal and run `htop` (or `top`).
2. Monitor the **MEM%** (Memory/RAM) and **CPU%**.
3. **Thresholds:**
   - If **RAM exceeds 90%**, the VM is at risk of completely freezing. You must immediately press `q` to exit htop and run `tmux kill-session -t <bot_name>` to kill a non-essential bot (like whatsapp) to free up memory.
   - If **CPU stays pinned at 100%**, trade execution latency will increase. Stop a non-critical bot to prioritize the main trading bots.
