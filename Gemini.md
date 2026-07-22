## Gemini Added Memories
- The user has instructed me to not make changes to the code without confirmation. I must only log to change.txt without permission.

# 1. CORE WORKFLOW & BEHAVIORAL RULES (GEMINI.MD & AGENTS.MD)

## A. Core Workflow Steps
1.  **Analyze and Propose:** First, analyze the request and the relevant code. Present a clear proposal for the code modifications, explaining what will be changed and why. Do not make any changes to the code at this stage.
2.  **User Approval:** Do not proceed with any code modification until you receive explicit "go ahead" or clarification.
3.  **Implement and Verify Code Change:** After receiving approval, implement the code changes. Immediately after making the code changes, run the project's compilation/syntax checking, testing, or linting commands to verify that the changes are safe, syntactically correct, and adhere to project standards. For flag-dependent logic changes, syntax/compile checks must be done first. Run a small offline smoke test with fake parameter values for important flag combinations, without connecting to Breeze, Google Sheets, or placing orders, to confirm the changed logic path executes before live use.
4.  **Final Logging:** Only after the code changes have been successfully implemented and verified, prepare the log entry for `change.txt` as per the logging procedure below. This ensures `change.txt` only contains records of successful and final versions, preventing logging of failed attempts or intermediate code versions.
5.  **Multi-Folder Logging:** Use the respective folder's `change.txt` and `gemini_log_update.tmp` depending on where the changes are being made!

## B. Code Change Guidelines
- **Comments:** Ensure any related comments are updated to reflect the changes. Add new comments sparingly, focusing only on the 'why' behind complex logic, not the 'what'. Always match the existing comment style and format of the file.
- **Security:** Never hardcode sensitive information like API keys or passwords in the source code. Be mindful of security best practices and avoid introducing common vulnerabilities.
- **Conventions:** Rigorously adhere to the project's existing conventions, including naming, formatting, and architectural patterns. Analyze the surrounding code to ensure changes are idiomatic.
- **Constants Section:** Place all constants and configuration variables in a dedicated section at the top of the file. Use `ALL_CAPS_WITH_UNDERSCORES` for naming (e.g., `SQUARE_OFF_TIME = '15:25'`). This avoids hardcoded 'magic values' in the logic and makes reconfiguration easy.
- **Floats & Precision:** For display purposes (e.g., logging or printing), format floating-point numbers to a consistent number of decimal places. To preserve precision, do not round or format values that are being stored for future calculations.

## C. `change.txt` Logging Procedure
This procedure is for logging final, successfully implemented, and verified code changes only. Intermediate versions or failed attempts will not be logged.
1.  **Prepare Content & Ask for Approval:** Save the full content for the new log entry directly to a temporary file (`gemini_log_update.tmp`) with exactly **two newlines at the end**. This must include:
    *   A timestamp line at the very top (e.g., `Date: YYYY-MM-DD HH:MM:SS`).
    *   The original user `query`.
    *   The `logic` and `explanation` of the change.
    *   A description of the `final code change`.
    After writing to the tmp file, ask the user for their "ok" on this file.
2.  **Automated Prepending & Git Push Process:**
    *   As soon as the user gives "ok" on the tmp file, **automatically** (without asking for further approval) use a shell command (`cat` and `mv`) to prepend the temporary content to `change.txt`.
    *   Immediately after, **automatically** run `git add .`, `git commit` (using the log entry as the body), and `git push`. Do not ask for further permissions.

## D. Critical Operating Procedures
- **DO NOT DEVIATE:** Certain tasks have specific, multi-step procedures outlined in instructions (e.g., logging to `change.txt`, deployments). These procedures must be followed exactly as described, without substitution or simplification.
- **DEBUG, DO NOT REPLACE:** If a command within a critical procedure fails, the only goal is to fix that command so the original procedure can run successfully. Never replace a prescribed complex procedure with a simpler but incorrect one to bypass an error.

## E. Enhanced Code Review Process
1.  **Integrated Static Analysis:** For tasks involving code modifications or review for potential bugs, proactively suggest and utilize static analysis tools (e.g., `pylint`, `flake8`, `mypy`) via shell commands to reliably identify syntax errors, basic runtime issues, and common smells.
2.  **Exhaustive Search for Critical Patterns:** Following significant changes to imports (e.g., `datetime` module handling) or when critical patterns are identified as potential sources of bugs, perform a systematic, file-wide search for all affected keywords, function calls, or variable usages. Ensure every instance is correctly qualified, aligned with current imports, and adheres to new standards.
3.  **Explicit Scope Tracing:** When dealing with variables that are passed through multiple function calls or that operate in different scopes (e.g., global vs. local, function parameters), explicitly trace their definitions, assignments, and usage through each step of the call chain to prevent `NameError` or `UnboundLocalError`.
4.  **Layered Review Structure:**
    *   *Layer 1 (Syntax & Basic Runtime):* Prioritize checks for fundamental Python syntax correctness, import qualification, and potential immediate runtime errors.
    *   *Layer 2 (Logical Flow & Intent):* Verify that the implemented logic correctly addresses the user's request, matches the proposed solution, and avoids unintended side effects.
    *   *Layer 3 (Best Practices & Conventions):* Ensure adherence to project-specific coding standards, style guides, and general software engineering best practices.

## F. Log Analysis Source Rule
- **For LOGS** (what happened today — trades, signals, errors, P&L, Google Sheet actions): use the downloaded copies under `/Users/vivek/ICICI_Direct/Google/`:
  - `selling` bot: `/Users/vivek/ICICI_Direct/Google/selling/`
  - `sensex` bot: `/Users/vivek/ICICI_Direct/Google/sensex/`
  - `mod_rsi` bot: `/Users/vivek/ICICI_Direct/Google/mod_rsi/`
  - `retire` bot: `/Users/vivek/ICICI_Direct/Google/retire/`
  - `whatsapp` bot: `/Users/vivek/ICICI_Direct/Google/whatsapp/`
  - `nifty` bot: `/Users/vivek/ICICI_Direct/Google/nifty/`
  - `binance` bot: `/Users/vivek/ICICI_Direct/Google/binance/`
  - `selling_1` bot: `/Users/vivek/ICICI_Direct/Google/selling_1/`
- **For CODE analysis** (why logic behaves a certain way, bug investigation, code review): always use the **master source files**:
  - `selling` bot: `/Users/vivek/ICICI_Direct/selling/`
  - `sensex` bot: `/Users/vivek/ICICI_Direct/sensex/`
  - `mod_rsi` bot: `/Users/vivek/ICICI_Direct/mod_rsi/`
  - `retire` bot: `/Users/vivek/ICICI_Direct/retire/`
  - `whatsapp` bot: `/Users/vivek/ICICI_Direct/whatsapp/`
  - `nifty` bot: `/Users/vivek/ICICI_Direct/nifty/`
  - `binance` bot: `/Users/vivek/ICICI_Direct/binance/`
  - `selling_1` bot: `/Users/vivek/ICICI_Direct/selling_1/`
  - **Never use `/Users/vivek/ICICI_Direct/Google/<bot>/` for code review** — those are VM download copies and may be outdated.

## G. Explanation Style
- When explaining code logic or proposed changes, use simple human language first, then give a small practical example with sample flag values and expected result; avoid only technical terms.

## H. Communication Style — File References
- **Always use the full absolute path** when referring to any file, directory, or script in any message, proposal, summary, or log entry.
  - ✅ Correct: `/Users/vivek/ICICI_Direct/retire/retire_single_leg.py`
  - ❌ Wrong: `retire_single_leg.py` or `retire/retire_single_leg.py`
- This rule is mandatory because the same filename (e.g. `google_sheet_utils.py`, `retire_trade.py`) exists in multiple bot folders (`/Users/vivek/ICICI_Direct/retire/`, `/Users/vivek/ICICI_Direct/Google/retire/`, etc.) and short paths cause serious confusion about which file is being discussed.

---

# 2. VM ARCHITECTURE & MAC OPERATIONS REFERENCE

You have access to 4 remote virtual machines managed by scripts in `/Users/vivek/ICICI_Direct/MAC`. Use these details when executing syncs, status checks, or restarts.

## 🛰️ Master Sync Commands (sync_master.sh)
- **`sm`** / `bash "$SCRIPT_DIR/sync_master.sh"`: Smart Sync base command.
- **`all`** / `bash "$SCRIPT_DIR/sync_master.sh" all`: Smart Sync download first, then upload for all targets.
- **`all_u`** / `bash "$SCRIPT_DIR/sync_master.sh" all_u`: Push code/configs to all servers.
- **`all_d`** / `bash "$SCRIPT_DIR/sync_master.sh" all_d`: Pull all logs, data, and code from all servers.
- **`all.st`**: Check health of all remote servers (`v.st && s.st && o.st`).
- **`all.r`**: Restart all projects on all servers (`v.all && o.r`).
- **`all.r.y`**: Hard restart (clear logs) all projects on all servers (`v.all.y && o.r.y`).

---

## 1. Vivek VM (GCP)
- **Connection:** `deshpande_vivek@34.26.75.26`
- **SSH Key:** `~/.ssh/gcp_key`
- **Remote Base:** `/home/deshpande_vivek`
- **Local Download Destination:** `/Users/vivek/ICICI_Direct/Google/`
- **Tracked Subfolders:**
  - `retire` (local) <-> `/home/deshpande_vivek/retire`
  - `whatsapp` (local) <-> `/home/deshpande_vivek/whatsapp`
  - `selling` (local) <-> `/home/deshpande_vivek/selling`
  - `Program_restart` (local) <-> `/home/deshpande_vivek/Program_restart`
- **Quick Operations:**
  - **`v.st`**: Check running tmux sessions and log sizes.
  - **`v.u`** / **`v.d`**: Upload / Download.
  - **`v.ret`** / **`v.ret.y`**: Soft / Hard Restart Retire (clearing logs).
  - **`v.sell`** / **`v.sell.y`**: Soft / Hard Restart Selling (clearing logs).
  - **`v.wa`** / **`v.wa.y`**: Soft / Hard Restart WhatsApp (clearing logs).
  - **`v.all`** / **`v.all.y`**: Soft / Hard Restart Everything.

---

## 2. Suresh VM (AWS)
- **Connection:** `ubuntu@140.245.15.195`
- **SSH Key:** `/Users/vivek/ICICI_Direct/Key/suresh_oracle/ssh_suresh_oracle.key`
- **Remote Base:** `/home/ubuntu`
- **Local Download Destination:** `/Users/vivek/ICICI_Direct/Ubentu/suresh/`
- **Tracked Subfolders:**
  - `algo_suresh` (local) <-> `/home/ubuntu/mod_rsi` (Note: Syncs `mod_rsi/*.py` to `algo_suresh/` first on upload)
  - `sensex_suresh` (local) <-> `/home/ubuntu/sensex_suresh` (Note: Syncs root `sensex/` files first on upload)
  - `Program_restart` (local) <-> `/home/ubuntu/Program_restart`
- **Quick Operations:**
  - **`s.st`**: Check running tmux sessions and log sizes.
  - **`s.u`** / **`s.d`**: Upload / Download.
  - **`s.rs`** / **`s.rs.y`**: Soft / Hard Restart mod_rsi (clearing logs).
  - **`s.sen`** / **`s.sen.y`**: Soft / Hard Restart Sensex (clearing logs).

---

## 3. Oracle Vivek VM (GCP)
- **Connection:** `ubuntu@80.225.215.187`
- **SSH Key:** `/Users/vivek/ICICI_Direct/Key/oracle/ssh-key-2026-02-11.key`
- **Remote Base:** `/home/ubuntu`
- **Local Download Destination:** `/Users/vivek/ICICI_Direct/Google/`
- **Tracked Subfolders:**
  - `binance` (local) <-> `/home/ubuntu/binance`
  - `mod_rsi` (local) <-> `/home/ubuntu/mod_rsi`
  - `selling_1` (local) <-> `/home/ubuntu/selling_1` (Note: Syncs `selling/*.py` to `selling_1/` first on upload)
  - `sensex` (local) <-> `/home/ubuntu/sensex`
  - `Program_restart` (local) <-> `/home/ubuntu/Program_restart`
- **Quick Operations:**
  - **`o.st`**: Check running tmux sessions and log sizes.
  - **`o.u`** / **`o.d`**: Upload / Download.
  - **`o.rsi`** / **`o.rsi.y`**: Soft / Hard Restart mod_rsi (clearing logs).
  - **`o.sell_1`** / **`o.sell_1.y`**: Soft / Hard Restart Selling_1 (clearing logs).
  - **`o.sen`** / **`o.sen.y`**: Soft / Hard Restart Sensex (clearing logs).
  - **`o.r`** / **`o.r.y`**: Soft / Hard Restart all Oracle projects (RSI, Selling_1, Sensex).
  - **`ssh_o`**: SSH command to connect directly.

---

## 4. Bandu VM (GCP)
- **Connection:** `vivek@35.196.102.57`
- **SSH Key:** `~/.ssh/gcp_key`
- **Remote Base:** `/home/vivek`
- **Local Download Destination:** `/Users/vivek/ICICI_Direct/Google/Bandu/`
- **Tracked Subfolders:**
  - `vinay` (local) <-> `/home/vivek/mod_rsi` (Note: Syncs `mod_rsi/*.py` to `vinay/` first on upload)
  - `selling_1` (local) <-> `/home/vivek/selling_1` (Note: Syncs `selling/*.py` to `selling_1/` first on upload)
- **Quick Operations:**
  - **`b.st`**: Check running tmux sessions and log sizes.
  - **`b.u`** / **`b.d`**: Upload / Download.
  - **`b.rsi`** / **`b.rsi.y`**: Soft / Hard Restart mod_rsi.
  - **`b.sell_1`** / **`b.sell_1.y`**: Soft / Hard Restart Selling_1.
  - **`b.all`** / **`b.all.y`**: Soft / Hard Restart both.

---

# 3. NIFTY BOT ARCHITECTURE & STRUCTURE

This section outlines the specific design and state management of the **Nifty EMA34 Band Futures Bot**.

## 1. Core Scripts
- **`nifty_ema34_signal.py`**: The signal generator. It downloads the last 3 days of 1-minute futures data from Breeze, resamples it into completed timeframe candles (e.g., 5-min), calculates the EMA34 High and Low bands, and checks if the `close` price crosses the bands within the `max_distance` threshold.
- **`nifty_ema34_trade.py`**: The main execution daemon. Handles API connections, reads parameters from Google Sheets, executes limit and stop-loss orders, and continuously manages the `Trade_State` state machine (CLOSED -> ENTRY_PENDING -> ACTIVE -> CLOSED).

## 2. State & Parameter Management
- **Local State (`parameters_cache.json` / `para.json`)**: Critical live trade state (e.g., `Trade_State`, `Entry_Order_ID`, `SL_Trigger_Price`) is continuously saved locally. This ensures the bot remembers exactly what it was doing if it crashes or restarts.
- **Google Sheets Parameters**: Parameters like `Reentry_counter`, `Delete_logs`, and `Max_Reentries` are fully synced with Google Sheets.
  - `Reentry_counter` increments automatically on every trade and is pushed to the sheet. The bot reads `params.get("Reentry_counter")` to enforce limits, allowing the user to view or override the counter live. It automatically resets to 0 on a new trading day.
  - Setting `Delete_logs` to 1 in the sheet will dynamically truncate the local `app.log`.

## 3. Graceful Recovery & Reboots
- **Session Token Changes**: The bot continually monitors the `session_token` parameter. If a new token is detected, it logs the change to Google Sheets and calls `sys.exit(1)`. The external tmux/bash wrapper script automatically detects the exit and reboots the bot with the new token.
- **Startup Diagnostics**: On a fresh boot, the bot verifies the Breeze API connection and logs `[NIFTY-TRADE] Breeze Connect initialized successfully.` to `log_single` to confirm recovery.
- **Broker Reconciliation**: On startup, it checks the live broker position. If an active futures position exists but the local state is missing a Stop Loss, it attempts an emergency SL repair.
