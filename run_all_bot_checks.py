#!/usr/bin/env python3
"""Run compile, AST and test checks across every ICICI_Direct bot, in parallel.

Replaces the ad-hoc one-off commands previously typed per session. Performs, for
each bot: a py_compile pass, a pyflakes undefined-name (F821) scan, and every
discovered test/smoke file -- with a safety classifier that refuses, by default,
to run any test that could place, cancel or square off a real order.

Usage:
    python3 run_all_bot_checks.py                  # compile + AST + safe tests
    python3 run_all_bot_checks.py --ast-only       # compile + AST only (~2s)
    python3 run_all_bot_checks.py --no-live        # skip broker/Sheets tests
    python3 run_all_bot_checks.py --jobs 9         # parallelism for non-Sheets tests
    python3 run_all_bot_checks.py --sheets-rate 20 # Sheets-touching starts per minute
    python3 run_all_bot_checks.py --bots sensex nifty
    python3 run_all_bot_checks.py --list           # classify tests, run nothing
    python3 run_all_bot_checks.py --include-unsafe # DANGEROUS: order-calling tests

WHY parallel:
    Every bot module runs an unconditional startup stagger in read_function.py
    that sleeps up to ~62s before any test body executes. Run serially, 55 tests
    cost 20-40 minutes of almost pure sleeping. Run concurrently those sleeps
    overlap, so wall time collapses to a few minutes.

WHY rate limited:
    Google Sheets allows only 60 read requests per minute per service account
    across all 4 VMs (AGENTS.md section I), and the live bots are consuming that
    same budget. Parallelism must therefore never apply to Sheets-touching tests
    without a throttle, or the batch starves the running bots and produces
    spurious 404/429 failures that look like real regressions.
"""

import argparse
import multiprocessing
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---------------------------------------------------------
BASE_DIR = "/Users/vivek/ICICI_Direct"

# algo_suresh / sensex_suresh are populated by sync from mod_rsi / sensex, so
# checking them separately just double-reports the same findings.
ALL_BOTS = ["selling", "selling_1", "retire", "mod_rsi", "sensex", "nifty", "whatsapp", "binance"]

# Files that must never be auto-run: they hit order endpoints with no dry-run guard.
EXPLICIT_DENY = {
    "test_easymargin.py": "calls breeze.square_off() at import time, no dry-run flag",
}

# Codebases outside the 8 trading bots. Compile + AST only by default: their
# test suites include backtests that can run for many minutes, so executing them
# is opt-in via --extra-tests.
EXTRA_TARGETS = {
    "Program_restart":   "/Users/vivek/ICICI_Direct/Program_restart",
    "data_extraction":   "/Users/vivek/ICICI_Direct/data_extraction",
    "backtest_ha_ema34": "/Users/vivek/ICICI_Direct/mod_rsi/backtest_ha_ema34",
    "docs_nifty":        "/Users/vivek/Documents/nifty",
    "Algo_1":            "/Users/vivek/ICICI_Direct/Algo_1",
    "vinay":             "/Users/vivek/ICICI_Direct/vinay",
    "session_manager":   "/Users/vivek/ICICI_Direct/session_manager",
    "MF":                "/Users/vivek/ICICI_Direct/MF",
    "Manoj":             "/Users/vivek/ICICI_Direct/Manoj",
}

# Directory fragments never worth compiling: third-party code, caches, VCS,
# agent scratch space and VM download copies.
EXCLUDE_DIR_PARTS = (
    "venv", "site-packages", ".git", "__pycache__", ".claude",
    "node_modules", "backups", ".ipynb_checkpoints",
)

# A script that argparse-requires flags is an operator CLI, not a test: run
# bare it exits rc=2 on missing arguments, which is not a failure of the code.
CLI_REQUIRED_RE = re.compile(r"required\s*=\s*True")
ARGPARSE_RE = re.compile(r"\bargparse\b")

ORDER_CALL_RE = re.compile(
    r"\b(place_order|place_trade|cancel_order|modify_order|square_off|place_gtt|place_child)\s*\("
)
MOCK_RE = re.compile(r"unittest\.mock|MagicMock|monkeypatch|@patch|sys\.modules\[")
LIVE_RE = re.compile(
    r"get_breeze\s*\(|breeze_connect|ws_connect|get_historical_data_v2|"
    r"get_google_sheet_client|get_parameters\s*\("
)

# Files a test may overwrite as a side effect. test_read_function.py in several
# bots writes placeholder values ("SPREADSHEET_KEY": "test_sheet") into para.json
# and never restores them, which silently breaks the live bot's config until
# someone notices a 404. Every one of these is snapshotted before the sweep and
# restored afterwards, plus immediately after any test that touches them.
CONFIG_FILES = ("para.json", "parameters_cache.json")

PER_TEST_TIMEOUT_SEC = 180
DEFAULT_SHEETS_RATE_PER_MIN = 20   # conservative share of the 60/min global budget
DEFAULT_LIVE_JOBS = 3              # concurrent Sheets/broker tests

_print_lock = threading.Lock()


def emit(text):
    """Print a line immediately, safely from any worker thread.

    Args:
        text (str): Line to print.

    WHY:
        Output must stream while the sweep runs, not appear at the end. Workers
        print concurrently, so the lock keeps lines from interleaving mid-string.
    """
    with _print_lock:
        print(text, flush=True)


class RateLimiter:
    """Token-bucket limiter for Sheets-touching test launches.

    Args:
        per_minute (int): Maximum starts allowed in any rolling 60-second window.

    WHY:
        Google Sheets caps reads at 60/min per service account across all VMs,
        shared with the live bots. Without this, parallel test launches exhaust
        the budget and generate false 404/429 failures.
    """

    def __init__(self, per_minute):
        self.per_minute = max(1, int(per_minute))
        self._starts = deque()
        self._lock = threading.Lock()

    def acquire(self):
        """Block until a start is permitted inside the rolling window."""
        while True:
            with self._lock:
                now = time.time()
                while self._starts and now - self._starts[0] >= 60.0:
                    self._starts.popleft()
                if len(self._starts) < self.per_minute:
                    self._starts.append(now)
                    return
                wait = 60.0 - (now - self._starts[0]) + 0.05
            time.sleep(max(0.05, wait))


def discover_tests(bot_dir):
    """List candidate test files in a bot folder (non-recursive).

    Args:
        bot_dir (str): Absolute path to the bot folder.

    Returns:
        list[str]: Sorted basenames of test_*.py and smoke*.py files.
    """
    if not os.path.isdir(bot_dir):
        return []
    return sorted(
        f for f in os.listdir(bot_dir)
        if (f.startswith("test_") or f.startswith("smoke")) and f.endswith(".py")
    )


def snapshot_config(root):
    """Capture the byte content of a target's config files.

    Args:
        root (str): Absolute path to the bot/codebase folder.

    Returns:
        dict[str, bytes|None]: filename -> content, None when the file is absent
        (so a test that *creates* one can also be undone).
    """
    snap = {}
    for name in CONFIG_FILES:
        path = os.path.join(root, name)
        try:
            with open(path, "rb") as fh:
                snap[name] = fh.read()
        except FileNotFoundError:
            snap[name] = None
        except OSError:
            snap[name] = None
    return snap


def restore_config(root, snap):
    """Put config files back exactly as snapshotted, if a test changed them.

    Args:
        root (str): Absolute path to the folder.
        snap (dict): Result of a previous snapshot_config() call.

    Returns:
        list[str]: Filenames that had to be restored (empty when untouched).

    WHY:
        A test mutating para.json is far more damaging than a failing assertion:
        it swaps the live spreadsheet key for a placeholder, so the bot 404s and
        silently falls back to stale cache. Restoring is therefore mandatory, not
        best-effort, and runs even when the sweep is interrupted.
    """
    restored = []
    for name, original in snap.items():
        path = os.path.join(root, name)
        try:
            current = None
            if os.path.exists(path):
                with open(path, "rb") as fh:
                    current = fh.read()
            if current == original:
                continue
            if original is None:
                os.remove(path)
            else:
                with open(path, "wb") as fh:
                    fh.write(original)
            restored.append(name)
        except OSError as exc:                      # pragma: no cover - defensive
            emit(f"   !! FAILED to restore {root}/{name}: {exc}")
    return restored


def discover_py_files(root, recursive):
    """List Python files under a target, skipping vendored/cache directories.

    Args:
        root (str): Absolute path to the target folder.
        recursive (bool): Walk subdirectories when True; top level only when False.

    Returns:
        list[str]: Paths relative to root, sorted.

    WHY:
        Bots are flat, but the backtester and data pipelines nest several levels
        deep and vendor a virtualenv. Compiling site-packages would report
        thousands of irrelevant third-party findings.
    """
    if not os.path.isdir(root):
        return []
    if not recursive:
        return sorted(f for f in os.listdir(root) if f.endswith(".py"))

    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not any(part in d for part in EXCLUDE_DIR_PARTS)
        ]
        if any(part in dirpath for part in EXCLUDE_DIR_PARTS):
            continue
        for fn in filenames:
            if fn.endswith(".py"):
                found.append(os.path.relpath(os.path.join(dirpath, fn), root))
    return sorted(found)


def classify(path):
    """Categorise a test file by what it will touch when executed.

    Args:
        path (str): Absolute path to the test file.

    Returns:
        tuple[str, str]: (category, reason). Category is one of
        UNSAFE / MOCKED / LIVE / PURE.

    WHY:
        An order-calling test that also mocks is normally asserting against a
        fake, but we do not try to prove that statically -- anything on the
        explicit deny list, or calling an order endpoint without any mocking,
        is treated as UNSAFE and skipped unless the operator opts in.
    """
    name = os.path.basename(path)
    if name in EXPLICIT_DENY:
        return "UNSAFE", EXPLICIT_DENY[name]
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        return "UNSAFE", f"unreadable: {exc}"

    mocked = bool(MOCK_RE.search(src))
    calls = sorted({m.group(1) for m in ORDER_CALL_RE.finditer(src)})
    if calls and not mocked:
        return "UNSAFE", f"unmocked order calls: {', '.join(calls)}"
    if ARGPARSE_RE.search(src) and CLI_REQUIRED_RE.search(src):
        return "CLI", "operator CLI: argparse requires flags, not a runnable test"
    if mocked:
        return "MOCKED", "uses mocks"
    if LIVE_RE.search(src):
        return "LIVE", "touches broker/Sheets APIs"
    return "PURE", "no external calls detected"


def run_cmd(args, cwd, timeout):
    """Run a subprocess, capturing output and never raising on failure.

    Args:
        args (list[str]): Command and arguments.
        cwd (str): Working directory.
        timeout (int): Seconds before the child is killed.

    Returns:
        tuple[int, str]: (returncode, combined stdout+stderr). Returncode is
        -1 on timeout.
    """
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"
    except Exception as exc:                      # pragma: no cover - defensive
        return -2, f"runner error: {exc}"


def check_compile_and_ast(bot_dir, recursive=False):
    """Compile every module in a bot and scan for undefined names.

    Args:
        bot_dir (str): Absolute path to the bot folder.

    Returns:
        dict: Keys compile_ok (bool), undefined (list[str]).
    """
    py_files = discover_py_files(bot_dir, recursive)
    if not py_files:
        return {"compile_ok": True, "undefined": []}
    rc, _ = run_cmd([sys.executable, "-m", "py_compile", *py_files], bot_dir, 300)
    _, out = run_cmd([sys.executable, "-m", "pyflakes", *py_files], bot_dir, 300)
    undefined = [ln for ln in out.splitlines() if "undefined name" in ln.lower()]
    return {"compile_ok": rc == 0, "undefined": undefined}


def main():
    cpu_default = max(1, multiprocessing.cpu_count() - 1)
    parser = argparse.ArgumentParser(description="Parallel compile/AST/test sweep for all bots.")
    parser.add_argument("--bots", nargs="*", default=ALL_BOTS)
    parser.add_argument("--ast-only", action="store_true")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--include-unsafe", action="store_true",
                        help="DANGEROUS: also run tests that call order endpoints.")
    parser.add_argument("--jobs", type=int, default=cpu_default,
                        help=f"Parallel workers for non-Sheets tests (default {cpu_default}).")
    parser.add_argument("--live-jobs", type=int, default=DEFAULT_LIVE_JOBS,
                        help=f"Concurrent Sheets/broker tests (default {DEFAULT_LIVE_JOBS}).")
    parser.add_argument("--sheets-rate", type=int, default=DEFAULT_SHEETS_RATE_PER_MIN,
                        help=f"Sheets test starts per minute (default {DEFAULT_SHEETS_RATE_PER_MIN}).")
    parser.add_argument("--timeout", type=int, default=PER_TEST_TIMEOUT_SEC)
    parser.add_argument("--no-extra", action="store_true",
                        help="Skip the non-bot codebases (backtester, Program_restart, etc).")
    parser.add_argument("--extra-tests", action="store_true",
                        help="Also RUN tests inside the non-bot codebases (can be slow).")
    parser.add_argument("--no-config-guard", dest="config_guard", action="store_false",
                        help="Do NOT snapshot/restore para.json around tests (unsafe).")
    parser.add_argument("--include-cli", action="store_true",
                        help="Also run operator CLIs that argparse-require flags.")
    args = parser.parse_args()

    started = time.time()
    emit(f"jobs={args.jobs}  live-jobs={args.live_jobs}  sheets-rate={args.sheets_rate}/min  "
         f"timeout={args.timeout}s")

    # ---- Phase 1: compile + AST (fast, sequential, no network) ----
    compile_fail, undefined_total, tasks, skipped = [], 0, [], []
    for bot in args.bots:
        bot_dir = os.path.join(BASE_DIR, bot)
        if not os.path.isdir(bot_dir):
            emit(f"[{bot}] folder missing -- skipped")
            continue
        res = check_compile_and_ast(bot_dir)
        undefined_total += len(res["undefined"])
        if not res["compile_ok"]:
            compile_fail.append(bot)
        emit(f"=== {bot} === compile={'OK' if res['compile_ok'] else 'FAIL'} "
             f"undefined_names={len(res['undefined'])}")
        for line in res["undefined"]:
            emit(f"      {line}")

        if args.ast_only:
            continue
        for test_file in discover_tests(bot_dir):
            path = os.path.join(bot_dir, test_file)
            category, reason = classify(path)
            if category == "UNSAFE" and not args.include_unsafe:
                skipped.append((bot, test_file, f"UNSAFE: {reason}"))
                continue
            if category == "CLI" and not args.include_cli:
                skipped.append((bot, test_file, f"CLI: {reason}"))
                continue
            if category == "LIVE" and args.no_live:
                skipped.append((bot, test_file, "LIVE (--no-live)"))
                continue
            if args.list:
                emit(f"   ----  {bot}/{test_file:<42} {category} ({reason})")
                continue
            tasks.append((bot, bot_dir, test_file, category))

    # --- Non-bot codebases: compile + AST always, tests only on request ---
    if not args.no_extra:
        for label, root in EXTRA_TARGETS.items():
            if not os.path.isdir(root):
                emit(f"[{label}] folder missing -- skipped")
                continue
            res = check_compile_and_ast(root, recursive=True)
            n_py = len(discover_py_files(root, recursive=True))
            undefined_total += len(res["undefined"])
            if not res["compile_ok"]:
                compile_fail.append(label)
            emit(f"=== {label} (extra) === files={n_py} "
                 f"compile={'OK' if res['compile_ok'] else 'FAIL'} "
                 f"undefined_names={len(res['undefined'])}")
            for line in res["undefined"]:
                emit(f"      {line}")

            if not args.extra_tests or args.ast_only or args.list:
                continue
            for rel in discover_py_files(root, recursive=True):
                base = os.path.basename(rel)
                if not (base.startswith("test_") or base.startswith("smoke")):
                    continue
                category, reason = classify(os.path.join(root, rel))
                if category in ("UNSAFE", "CLI") and not (args.include_unsafe or args.include_cli):
                    skipped.append((label, rel, f"{category}: {reason}"))
                    continue
                if category == "LIVE" and args.no_live:
                    skipped.append((label, rel, "LIVE (--no-live)"))
                    continue
                tasks.append((label, root, rel, category))

    for bot, name, why in skipped:
        emit(f"   SKIP  {bot}/{name}: {why}")

    if args.ast_only or args.list:
        emit(f"\ncompile failures : {compile_fail or 'none'}")
        emit(f"undefined names  : {undefined_total}")
        emit(f"elapsed          : {time.time() - started:.1f}s")
        return 1 if (compile_fail or undefined_total) else 0

    # ---- Phase 2: run tests in parallel, throttling Sheets-touching ones ----
    limiter = RateLimiter(args.sheets_rate)
    live_slots = threading.Semaphore(max(1, args.live_jobs))
    total = len(tasks)
    done_count = [0]
    passed, failed, mutated = [], [], []

    # Snapshot every target's config BEFORE a single test runs, and hold a lock
    # per folder so concurrent tests in the same bot cannot race the restore.
    roots = sorted({root for _, root, _, _ in tasks})
    snapshots = {root: snapshot_config(root) for root in roots}
    dir_locks = {root: threading.Lock() for root in roots}
    if args.config_guard:
        emit(f"config guard: snapshotted {', '.join(CONFIG_FILES)} for {len(roots)} folder(s)")

    def worker(task):
        bot, bot_dir, test_file, category = task
        throttled = category == "LIVE"
        if throttled:
            live_slots.acquire()
            limiter.acquire()
        try:
            t0 = time.time()
            rc, out = run_cmd([sys.executable, test_file], bot_dir, args.timeout)
        finally:
            if throttled:
                live_slots.release()
        restored = []
        if args.config_guard:
            with dir_locks[bot_dir]:
                restored = restore_config(bot_dir, snapshots[bot_dir])
        return bot, test_file, category, rc, out, time.time() - t0, restored

    emit(f"\nrunning {total} tests in parallel...\n")
    try:
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            futures = [pool.submit(worker, t) for t in tasks]
            for fut in as_completed(futures):
                bot, test_file, category, rc, out, secs, restored = fut.result()
                done_count[0] += 1
                tag = f"[{done_count[0]:>2}/{total}]"
                note = ""
                if restored:
                    mutated.append((bot, test_file, restored))
                    note = f"  !! MUTATED CONFIG ({', '.join(restored)}) - restored"
                if rc == 0:
                    passed.append((bot, test_file))
                    emit(f"{tag} PASS  {bot}/{test_file:<42} [{category}] {secs:.0f}s{note}")
                else:
                    failed.append((bot, test_file, rc, out))
                    tail = " | ".join(out.strip().splitlines()[-2:])[:160]
                    emit(f"{tag} FAIL  {bot}/{test_file:<42} [{category}] rc={rc} {secs:.0f}s  {tail}{note}")
    finally:
        # Mandatory: runs on success, failure, exception or Ctrl-C.
        if args.config_guard:
            for root in roots:
                left = restore_config(root, snapshots[root])
                if left:
                    emit(f"config guard: final restore of {root}: {', '.join(left)}")

    emit("\n" + "=" * 78)
    emit(f"compile failures : {compile_fail or 'none'}")
    emit(f"undefined names  : {undefined_total}")
    emit(f"tests passed     : {len(passed)}")
    emit(f"tests failed     : {len(failed)}")
    for bot, name, rc, _ in failed:
        emit(f"     - {bot}/{name} (rc={rc})")
    if mutated:
        emit(f"config mutations : {len(mutated)}  (all restored)")
        for bot, name, files in mutated:
            emit(f"     - {bot}/{name} wrote {', '.join(files)}")
    emit(f"tests skipped    : {len(skipped)}")
    for bot, name, why in skipped:
        emit(f"     - {bot}/{name}: {why}")
    emit(f"elapsed          : {time.time() - started:.1f}s")
    emit("=" * 78)
    if failed:
        emit("\nNOTE: a test that fails here but passes when run alone is usually a\n"
             "batch artifact (Sheets quota), not a regression. Re-run failures\n"
             "individually before treating them as real.")
    return 1 if (compile_fail or undefined_total or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
