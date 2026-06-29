# Instructions for OHLCV Resampling Refactor

You are refactoring the resampling logic of the trading bot: **[INSERT_BOT_NAME_HERE]** (e.g., `mod_rsi`, `sensex`, `selling`, `retire`, `nifty`).
We want to replace its current resampling logic with the standard forward-fill and gap-filling design pattern defined in the master document:
`/Users/vivek/ICICI_Direct/MAC/ohlcv_resampling_standard.md`

Please follow these instructions step-by-step to implement this change safely and correctly.

---

## 1. Locate Master Source Files
* Locate the signal generation or indicator calculation script in the master directory:
  * For mod_rsi: `/Users/vivek/ICICI_Direct/mod_rsi/`
  * For sensex: `/Users/vivek/ICICI_Direct/sensex/`
  * For retire: `/Users/vivek/ICICI_Direct/retire/`
  * For selling: `/Users/vivek/ICICI_Direct/selling/`
  * For nifty: `/Users/vivek/ICICI_Direct/nifty/`
  * For selling_1: `/Users/vivek/ICICI_Direct/selling_1/`
  * For binance: `/Users/vivek/ICICI_Direct/binance/`
  * *(Note: `whatsapp` bot is a notification relay and does not process market OHLCV data, so it is excluded from resampling refactoring).*
* Search the codebase for existing resampling routines. Common keywords to search for: `resample`, `resample_complete_ohlcv`, `pd.DataFrame.resample`, `bar_count`.
* **CRITICAL RULE:** Never edit files inside the download directories (e.g., `/Users/vivek/ICICI_Direct/Google/` or `/Users/vivek/ICICI_Direct/Ubentu/`). Always edit the master source files.

---

## 2. Analyze the Existing Logic & Function Signatures
Before writing code, analyze:
1. **Function Signature:** What arguments does the existing resampling function take, and what does it return? Ensure the new function matches the exact signature and return format (e.g. index reset with a `'datetime'` column or index kept as datetime).
2. **Column Casing:** Does the bot use lowercase (`open`, `high`, `low`, `close`, `volume`) or uppercase/title case (`Open`, `High`, `Low`, `Close`, `Volume`)? The refactored function must match this casing.
3. **Volume Column:** Does the data contain a volume column? If not, exclude volume logic or check if it exists dynamically.
4. **Timeframe Dynamic:** Verify if the target timeframe (`interval_min`) is passed dynamically or hardcoded, and preserve that behavior.

---

## 3. Formulate the Refactoring Proposal
Propose the changes before writing them:
* Show the exact diff between the existing resampling function and the new gap-filled function adapted from `/Users/vivek/ICICI_Direct/MAC/ohlcv_resampling_standard.md`.
* Explain the change using simple human language first, followed by a practical example with sample inputs.
* Wait for the user's explicit approval before modifying the file.

---

## 4. Implementation Details to Incorporate
When adapting the template from `/Users/vivek/ICICI_Direct/MAC/ohlcv_resampling_standard.md`:
* **Reindexing to 1m grid:**
  ```python
  full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='1min')
  df = df.reindex(full_range)
  ```
* **Forward Filling Prices:**
  ```python
  df['close'] = df['close'].ffill()
  df['open'] = df['open'].fillna(df['close'])
  df['high'] = df['high'].fillna(df['close'])
  df['low'] = df['low'].fillna(df['close'])
  if 'volume' in df.columns:
      df['volume'] = df['volume'].fillna(0)
  ```
* **Aggregation & Bar Count Filter:**
  Ensure the aggregation uses `closed='left', label='left'` and drops the incomplete live boundary candle via `bar_count >= interval_min`.

---

## 5. Verification Plan
After modifying the file:
1. **Static Analysis & Syntax check:** Run `python -m py_compile <file_path>` or a linter to ensure no syntax errors.
2. **Smoke Test:** Create a temporary test script in `scratch/` that loads mock 1-minute sparse data (containing a gap) and passes it through the refactored function. Print the result and verify:
   * The gap is filled correctly with the previous close.
   * Volume during the gap is set to 0.
   * The incomplete live boundary candle is dropped correctly.
   * The output dataframe is structured exactly as expected by the rest of the bot.

---

## 6. Logging & Deployment Procedures
After successful verification:
1. **Log the change to `change.txt`:**
   * Prepare a detailed log entry showing the timestamp, original query, logic explanation, and the final code change.
   * Get user approval for the log content.
   * Write content to `/Users/vivek/ICICI_Direct/<bot>/gemini_log_update.tmp` and atomically prepend to `/Users/vivek/ICICI_Direct/<bot>/change.txt`.
2. **Commit and Push:**
   * Commit all modified files and `change.txt` using the log entry as the commit message, and push.
3. **Deploy & Sync to VMs (Required for trading bots running on VM servers):**
   * Run the smart sync upload command: `sm all_u` (or `v.u` / `s.u` / `o.u` / `b.u` depending on where the bot is hosted).
   * Restart the respective bot session using the specific script aliases (e.g., `v.ret`, `o.rsi`, `s.sen`, etc.).
