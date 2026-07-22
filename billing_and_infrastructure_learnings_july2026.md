# Google Cloud Infrastructure & Billing Learnings
**Date:** July 19, 2026
**Context:** Investigation of a sudden billing spike (₹132/day) on July 16th and securing the trading bot infrastructure.

---

## 1. The Cloud Run Billing Spike (The Root Cause)
The massive, sudden spike in the Google Cloud bill on July 16th was **not** caused by Compute Engine or IP addresses. It was 100% caused by **Cloud Run** and **Pub/Sub**.

### What Happened:
1. The `icici-stop-control` Cloud Run service lost access to a Google Sheet (returning a 404 error).
2. Because it couldn't access the sheet, the Cloud Run service crashed and returned a 500 Internal Server Error to Pub/Sub.
3. **The Fatal Flaw:** The Pub/Sub subscriptions were configured with the default retry policy (Immediate Retry) and a 7-day retention period. 
4. Because the message failed, Pub/Sub immediately hit the Cloud Run URL again. It failed again. It hit it again. This created an infinite, high-speed loop.
5. The loop burned through the massive 2 million "Always Free" Cloud Run requests in a matter of days and racked up over ₹600 in usage costs, leaving a final bill of ₹120.

### The Solution Implemented:
We globally updated all 5 Pub/Sub subscriptions in the project (`icici-stop-ack-cloud-run`, `icici-stop-google-vm`, `icici-stop-oracle-vm`, `icici-stop-suresh-vm`, `oracle-fast-param-sub`) with three critical protections:
*   **Exponential Backoff:** Activated. Failing messages now wait 10 seconds before the first retry, and slowly back off to a maximum wait time of 10 minutes between retries. This reduces spam by 99%.
*   **1-Day Retention:** Activated. The queue will automatically purge failing messages after 1 day (86,400 seconds), preventing 7 days of continuous looping.
*   **Never Expire:** Activated. The subscriptions themselves are marked to never automatically delete.

---

## 2. Google Cloud IP Pricing & The "Free Tier" Exception
Google Cloud changed their global pricing policy on **February 1, 2024**, charging $0.005 per hour (~₹300/month) for **ALL** external IPv4 addresses, regardless of whether they are Static or Ephemeral. 

However, a critical exception was discovered in the documentation:
*   **The e2-micro Exception:** The Google Cloud Free Tier explicitly includes 1 free external IPv4 address for an **e2-micro** instance.
*   Because the Vivek VM is an e2-micro instance operating within the Free Tier limits, **the IP address is completely free.**

### The Mystery of the ₹27 Charge
The Compute Engine billing chart showed a tiny charge of ₹27.73 for the entire year, with ₹0.00 in "Other savings". We initially thought this was the IP address charge escaping the free tier. 
*   **Conclusion:** The ₹27 was **not** an IP address charge. If it were, it would be ~₹300 per month. The ₹27 over a year (and ₹12 forecasted for July) is actually a tiny **Network Egress** charge for sending data across regions (e.g., from Mumbai to US East).

---

## 3. Static vs. Ephemeral IPs
Because the external IP address is covered by the e2-micro Free Tier, it does not cost a single rupee extra to make it a **Static IP**. 

**Why Ephemeral IPs are Dangerous for ICICI Direct:**
*   An Ephemeral IP can change instantly if Google performs forced hardware maintenance or if the VM is stopped.
*   If the IP changes, the ICICI Direct API immediately breaks.
*   Updating the IP in ICICI Direct triggers a **7-day lockout** where trading is disabled.
*   **Best Practice:** Always use a Static IP for trading bots. It costs the exact same (₹0 for e2-micro), but provides 100% stability.

---

## 4. The July 23rd ICICI Gameplan
The old IP (`35.237.249.135`) was lost because it was Ephemeral and given away by Google. 
The new IP is **`34.26.75.26`**. 

1. On **July 19th**, we officially promoted `34.26.75.26` to a **Static IP** in Google Cloud so it will never change again.
2. All local Mac scripts (`sync_master.sh`, `remote_vivek.sh`, etc.) were verified/updated to use the new IP.
3. **ACTION REQUIRED:** On **July 23rd at 10:38**, log into the ICICI Direct portal, enter the new Static IP (`34.26.75.26`) into the whitelist, and the trading bot will instantly resume normal operations.

---

## 5. Billing Monitoring & Alerting Plan
To prevent future surprises and ensure the Free Tier is working as expected, follow this monitoring plan:

### How to Drill Down into Billing (Finding the Exact Charge)
If you see a mysterious charge like the ₹27 Compute Engine bill and want to know exactly what caused it:
1. Open the Google Cloud Console and navigate to **Billing** -> **Reports**.
2. By default, the top-left dropdown says **`Group by (Service)`**. This groups all charges into broad categories (like "Compute Engine" or "Cloud Run").
3. Click that dropdown and change it to **`Group by (SKU)`**.
4. The table will instantly break down every single micro-charge. Instead of just seeing "Compute Engine", you will see exact line items like `"External IP Charge"` or `"Inter-region Data Transfer Out"`. This is how we proved the ₹27 charge was network egress, not an IP address charge.

### How to Monitor the "Always Free" Tier Usage
To verify that Google is actually applying your free tier discounts:
1. Look at the billing table columns.
2. Find your total usage cost under the **`Usage cost`** column.
3. Look at the **`Other savings`** (or `Savings programs`) column.
4. If your usage falls within the Free Tier limits, you will see a negative number in `Other savings` that perfectly cancels out the `Usage cost`, resulting in a ₹0.00 subtotal. If `Other savings` is ₹0.00, it means that specific service/SKU is not covered by the free tier.

### Recommended Alerting Strategy
To prevent another ₹120 spike from going unnoticed for days:
1. Go to **Billing** -> **Budgets & alerts** in the Google Cloud Console.
2. Create a new budget alert.
3. Set the target amount to a low threshold (e.g., **₹50 or ₹100 per month**).
4. Set the alert to trigger at **50%**, **90%**, and **100%** of that threshold.
5. Google will instantly email you if your costs suddenly spike due to a runaway script, giving you time to kill the process before it burns through hundreds of rupees.
