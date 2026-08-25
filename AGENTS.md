# Approval-First Workflow

For every task in this workspace:

1. Analyze and propose first.
2. Do not modify code, config, scripts, logs, or documentation until the user explicitly approves.
3. Before any implementation, show the exact code snippets or diffs that will be changed.
4. After approval, implement the change and run syntax, compile, AST verification, and offline mock tests.
5. After verification, propose the `change.txt` content for approval. Once approved, automatically write to `change.txt`, commit, and push without asking for further approval.
6. If `Gemini.md` or `/Users/vivek/ICICI_Direct/GEMINI.md` exists, follow that file exactly for this workspace.

## Explanation Style
- When explaining code logic or proposed changes, use simple human language first, then give a small practical example with sample flag values and expected result; avoid only technical terms because I may not understand the design from abstract wording alone.

## Log Analysis Source Rule
- **For LOGS** (what happened today — trades, signals, errors, P&L, Google Sheet actions): use the downloaded copies under `/Users/vivek/ICICI_Direct/Google/<bot>/`.
- **For CODE analysis** (why logic behaves a certain way, bug investigation, code review): always use the master source files under `/Users/vivek/ICICI_Direct/<bot>/`. Never use the Google download folder for code review.

## Mandatory Fault-Injection & Mock Testing Rule
- Whenever creating or editing retry, backoff, rate-limiting, or error handling mechanisms, you must run an offline mock test with injected synthetic exceptions (e.g. Google Sheets 429 quota error) to verify execution before deploying or pushing code.

## Communication Style — File References
- **Always use the full absolute path** when referring to any file, directory, or script in any message, proposal, summary, or log entry.
  - ✅ Correct: `/Users/vivek/ICICI_Direct/retire/retire_single_leg.py`
  - ❌ Wrong: `retire_single_leg.py` or `retire/retire_single_leg.py`


## Mandatory AST Static Symbol Verification & Format-Agnostic Date Normalization Standard

### 1. AST-Based Static Symbol Analysis (Zero NameErrors)
- **Problem**: Python compilation (py_compile) only catches syntax errors, deferring undefined variable lookups (NameError) inside function bodies to runtime when untriggered branches execute in production.
- **Mandatory Verification**: After every code edit, you **MUST** run an AST-based static symbol checker (such as `python3 -m pyflakes <file>` or an AST visitor) to verify that **zero** undefined names (`F821 / NameError`) exist in any branch, loop, or helper function.

### 2. Format-Agnostic Date Comparisons
- **Problem**: Comparing date strings with raw string equality (e.g., `"1-SEP-2026" == "01-SEP-2026"` or `"2026-09-01T06:00:00.000Z" == "01-SEP-2026"`) fails unpredictably due to single-digit vs zero-padded day formatting, month capitalization, and ISO timestamps from broker APIs.
- **Mandatory Standard**: Always use `_normalize_expiry_token()` (or parsed `.date()` object comparisons e.g. `d1.date() == d2.date()` or `d1 >= d2`) so that all date comparisons are completely format-agnostic (both formatting to canonical `YYYY-MM-DD`). Never use raw string equality for dates.

