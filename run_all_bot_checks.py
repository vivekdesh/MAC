#!/usr/bin/env python3
"""Run compile, AST and test checks across every ICICI_Direct bot.

Replaces the ad-hoc one-off commands previously typed per session. Performs, for
each bot: a py_compile pass, a pyflakes undefined-name (F821) scan, and every
discovered test/smoke file -- with a safety classifier that refuses, by default,
to run any test that could place, cancel or square off a real order.

Usage:
    python3 run_all_bot_checks.py                  # compile + AST + safe tests
    python3 run_all_bot_checks.py --ast-only       # compile + AST only, no tests
    python3 run_all_bot_checks.py --no-live        # skip tests that call broker/Sheets
    python3 run_all_bot_checks.py --bots sensex nifty
    python3 run_all_bot_checks.py --list           # classify tests, run nothing
    python3 run_all_bot_checks.py --include-unsafe # DANGEROUS: allows order-calling tests

WHY:
    Tests here are not uniformly safe. Some are fully mocked, some read live
    Breeze/Sheets data (quota cost, best run after market close), and at least one
    calls square_off() at import time with no dry-run guard. Classifying before
    running is the difference between a health check and an accidental trade.
"""

import argparse
import os
import re
import subprocess
import sys
import time

# --- Configuration ---------------------------------------------------------
BASE_DIR = "/Users/vivek/ICICI_Direct"

# algo_suresh and sensex_suresh are populated by sync from mod_rsi/sensex, so
# checking them separately just double-reports the same findings.
ALL_BOTS = ["selling", "selling_1", "retire", "mod_rsi", "sensex", "nifty", "whatsapp", "binance"]

# Files that must never be auto-run: they hit order endpoints with no dry-run guard.
EXPLICIT_DENY = {
    "test_easymargin.py": "calls breeze.square_off() at import time, no dry-run flag",
}

ORDER_CALL_RE = re.compile(
    r"\b(place_order|place_trade|cancel_order|modify_order|square_off|place_gtt|place_child)\s*\("
)
MOCK_RE = re.compile(r"unittest\.mock|MagicMock|monkeypatch|@patch|sys\.modules\[")
LIVE_RE = re.compile(
    r"get_breeze\s*\(|breeze_connect|ws_connect|get_historical_data_v2|"
    r"get_google_sheet_client|get_parameters\s*\("
)

PER_TEST_TIMEOUT_SEC = 180


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
    if mocked:
        return "MOCKED", "uses mocks"
    if LIVE_RE.search(src):
        return "LIVE", "touches broker/Sheets APIs"
    return "PURE", "no external calls detected"


def run_cmd(args, cwd, timeout=PER_TEST_TIMEOUT_SEC):
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
        proc = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"


def check_compile_and_ast(bot, bot_dir):
    """Compile every module and scan for undefined names.

    Args:
        bot (str): Bot name.
        bot_dir (str): Absolute path to the bot folder.

    Returns:
        dict: Keys compile_ok (bool), undefined (list[str]).
    """
    py_files = sorted(f for f in os.listdir(bot_dir) if f.endswith(".py"))
    if not py_files:
        return {"compile_ok": True, "undefined": []}

    rc, _ = run_cmd([sys.executable, "-m", "py_compile", *py_files], bot_dir)
    _, out = run_cmd([sys.executable, "-m", "pyflakes", *py_files], bot_dir)
    undefined = [ln for ln in out.splitlines() if "undefined name" in ln.lower()]
    return {"compile_ok": rc == 0, "undefined": undefined}


def main():
    parser = argparse.ArgumentParser(description="Compile/AST/test sweep for all bots.")
    parser.add_argument("--bots", nargs="*", default=ALL_BOTS, help="Subset of bots to check.")
    parser.add_argument("--ast-only", action="store_true", help="Compile + AST only, skip tests.")
    parser.add_argument("--no-live", action="store_true", help="Skip tests that hit broker/Sheets.")
    parser.add_argument("--list", action="store_true", help="Classify tests and exit without running.")
    parser.add_argument("--include-unsafe", action="store_true",
                        help="DANGEROUS: also run tests that call order endpoints.")
    parser.add_argument("--timeout", type=int, default=PER_TEST_TIMEOUT_SEC,
                        help=f"Per-test timeout in seconds (default {PER_TEST_TIMEOUT_SEC}).")
    args = parser.parse_args()

    started = time.time()
    compile_fail, undefined_total = [], 0
    passed, failed, skipped = [], [], []

    for bot in args.bots:
        bot_dir = os.path.join(BASE_DIR, bot)
        if not os.path.isdir(bot_dir):
            print(f"[{bot}] folder missing -- skipped")
            continue

        res = check_compile_and_ast(bot, bot_dir)
        undefined_total += len(res["undefined"])
        if not res["compile_ok"]:
            compile_fail.append(bot)
        status = "OK" if res["compile_ok"] else "FAIL"
        print(f"\n=== {bot} === compile={status} undefined_names={len(res['undefined'])}")
        for line in res["undefined"]:
            print(f"      {line}")

        if args.ast_only:
            continue

        for test_file in discover_tests(bot_dir):
            path = os.path.join(bot_dir, test_file)
            category, reason = classify(path)

            if category == "UNSAFE" and not args.include_unsafe:
                skipped.append((bot, test_file, f"UNSAFE: {reason}"))
                print(f"   SKIP  {test_file:<44} UNSAFE ({reason})")
                continue
            if category == "LIVE" and args.no_live:
                skipped.append((bot, test_file, "LIVE (--no-live)"))
                print(f"   SKIP  {test_file:<44} LIVE (--no-live)")
                continue
            if args.list:
                print(f"   ----  {test_file:<44} {category} ({reason})")
                continue

            rc, out = run_cmd([sys.executable, test_file], bot_dir, timeout=args.timeout)
            if rc == 0:
                passed.append((bot, test_file))
                print(f"   PASS  {test_file:<44} [{category}]")
            else:
                failed.append((bot, test_file, rc))
                tail = " | ".join(out.strip().splitlines()[-3:])[:200]
                print(f"   FAIL  {test_file:<44} [{category}] rc={rc}  {tail}")

    print("\n" + "=" * 78)
    print(f"compile failures : {compile_fail or 'none'}")
    print(f"undefined names  : {undefined_total}")
    if not args.ast_only and not args.list:
        print(f"tests passed     : {len(passed)}")
        print(f"tests failed     : {len(failed)}")
        for bot, name, rc in failed:
            print(f"     - {bot}/{name} (rc={rc})")
        print(f"tests skipped    : {len(skipped)}")
        for bot, name, why in skipped:
            print(f"     - {bot}/{name}: {why}")
    print(f"elapsed          : {time.time() - started:.1f}s")
    print("=" * 78)

    return 1 if (compile_fail or undefined_total or failed) else 0


if __name__ == "__main__":
    sys.exit(main())
