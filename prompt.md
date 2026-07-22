discussion mode, re-read agents.md, gemini.md.
no code changes before approval and human way of telling

Improve the documentation only—do not change behavior.

Add or enhance a docstring for every function describing:
Purpose: what the function does.
Parameters: each input, its meaning, and expected type.
Returns: what is returned, including type and meaning.
Raises: any exceptions that may be intentionally raised (if applicable).
Side effects: file I/O, network calls, database updates, global state changes, etc. (if applicable).
Add WHY comments before every non-obvious block of logic, explaining the reasoning behind the implementation or algorithm—not merely describing what the code does.
Do not add comments for trivial or self-explanatory code.
Do not modify any executable code, function signatures, control flow, or formatting except where necessary to insert documentation.
Follow PEP 257 for Python docstrings and keep comments concise, accurate, and maintenance-friendly.


Latest Logs are downloded in respective google folder, please refer the same for analysis!


sir, yesterdays data is avialble. all options from 9:15 to 3:30 are available in log_backup of B column. Please analyse sensex and nifty trades, and anlyse in quant way. Backtest with option price lab and all paramters to be calibrated for option price lab model!!

# CORE BEHAVIOR RULES
1. Discussion Mode Active: Re-read agents.md and gemini.md.
2. No blind execution: Do not make any code, script, or cloud infrastructure changes without my explicit approval first.
3. Human-first explanations: Before asking for permission to run a command, explain exactly what the command does in simple, non-technical human language so I understand what I am approving.
4. Show your work: Always present the exact code snippets or diffs before implementation.
5. Improve documentation only: Unless asked otherwise, do not change bot behavior.
6. Latest Logs are downloded in respective google folder, please refer the same for analysis!


Please refer /Users/vivek/Documents/MASTER_PROMPT_TEMPLATE.md 

Todays data is available column B of log_single and   Till yesterday data is available. all options from 9:15 to 3:30 are available in log_backup of B column.
Please analyse sensex and nifty trades, and anlyse in quant way.
log sheet and Live Paramters references can be derived from sensex and mod_rsi (LIVE BOT) and its respective google folder!!
Backtest with option price lab and all parameters to be calibrated for option price lab model!!


Ah, excellent question!

Here is the complete list of critical Memory files from `/Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/` that must be used for Option Pricing Lab calibration, smile fitting, and engine learnings:

---

### 📚 Essential Memory Files from `/Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/`

1. **`leg_aware_iv_calibration_memory.md`** *(Created Today - July 21, 2026)*
   - **Key Role:** Authoritative source for **Leg-Aware Implied Volatility Scaling**.
   - **Core Learning:** Flat Black-Scholes pricing overestimates Call options by 4–5% and underestimates Put options by 4–7% due to market put-skew. Leg-aware multipliers ($\text{Nifty CE } 0.82 / \text{PE } 0.94$, $\text{Sensex CE } 0.92 / \text{PE } 1.04$) eliminate this model bias and produce accurate synthetic option prices.

2. **`calibration_discovery_realdata.md`**
   - **Key Role:** Empirical validation comparing real live option chain quotes against Black-Scholes model predictions.
   - **Core Learning:** Documents the VIX corruption bug (VIX prints $\times 100$ data errors in raw logs), contract selection rules (DTE $\le 1$ roll logic), and the baseline IV/VIX ratios.

3. **`memory1.md`**
   - **Key Role:** Comprehensive Engine Bugfixes & Pricing Calibration Audit.
   - **Core Learning:** Documents 3 critical engine fixes required for accurate backtesting:
     * **Phantom Expiry Roll Fix:** Live bots roll to next week's expiry when DTE $\le 1$.
     * **Expiry Anchor Alignment Fix:** Anchors option expiry to current session date (prevents day-after-expiry fantasy pricing).
     * **Strike Scanning Window Expansion:** Widened strike candidate window to ATM $\pm 8$ steps ($\pm 800$ pts) because real live executions frequently occur 500+ points OTM during high DTE.

4. **`memory_backetst.md`**
   - **Key Role:** Premium Selection & Parameter State Rules.
   - **Core Learning:** Demonstrates how `desired_premium` (85 vs 100 vs 125) impacts win rate and drawdown. Enforces **Memory Rule 5**: runtime Google Sheet state cells (e.g. `PE_same_leg_reentry`, `Reentry_counter`) must **never** be copied into static backtest configs—they must re-initialize to 0 on every trading day.

5. **`MEMORY.md`**
   - **Key Role:** Master Index file linking all active memory documents.

---

### 🗺️ Master Mapping of All Required Files for Serious Backtest Work:

| Category | Primary Backtest Engine Script | Core Memory Documentation Files |
| :--- | :--- | :--- |
| **Option Selling Bot** | [`selling_engine_bs.py`](file:///Users/vivek/ICICI_Direct/selling/backtest_ha_ema34_selling/selling_engine_bs.py) | • [`BACKTEST_DESIGN_DOC.md`](file:///Users/vivek/ICICI_Direct/selling/backtest_ha_ema34_selling/BACKTEST_DESIGN_DOC.md)<br>• [`SELLING_MODEL_COMPARISON.md`](file:///Users/vivek/ICICI_Direct/selling/backtest_ha_ema34_selling/SELLING_MODEL_COMPARISON.md) |
| **Nifty Live Simulator** | [`backtest_live_bot.py`](file:///Users/vivek/Documents/nifty/live_bot_sim/backtest_live_bot.py) | • [`claude_nifty_backtesting.md`](file:///Users/vivek/Documents/nifty/live_bot_sim/Memory/claude_nifty_backtesting.md)<br>• [`claude_memory.md`](file:///Users/vivek/Documents/nifty/live_bot_sim/Memory/claude_memory.md) |
| **Option Pricing Lab & Engine Calibration** | [`ha_ema34_engine_bs_combined.py`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/ha_ema34_engine_bs_combined.py)<br>[`pricing_wrapper.py`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/pricing_wrapper.py) | • [`leg_aware_iv_calibration_memory.md`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/leg_aware_iv_calibration_memory.md)<br>• [`calibration_discovery_realdata.md`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/calibration_discovery_realdata.md)<br>• [`memory1.md`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/memory1.md)<br>• [`memory_backetst.md`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/memory_backetst.md)<br>• [`MEMORY.md`](file:///Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34/Memory/MEMORY.md) |