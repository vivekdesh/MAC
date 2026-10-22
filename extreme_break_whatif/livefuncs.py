"""Load the LIVE bots' own indicator/gate functions without importing their modules.

retire_single_leg.py opens a Google Sheets client and an app_single.log at import,
so the needed function definitions are pulled out of the master source with ast
and executed in an isolated namespace. Nothing at module level runs.
"""
import ast
import datetime
import logging
import math
import time

import numpy as np
import pandas as pd
import pandas_ta as ta

RETIRE_SRC = "/Users/vivek/ICICI_Direct/retire/retire_single_leg.py"
NIFTY_SRC = "/Users/vivek/ICICI_Direct/nifty/nifty_ema34_signal.py"

RETIRE_FUNCS = [
    "resample_dataframe", "compute_supertrend_stateful", "get_supertrend_snapshot",
    "get_ema_snapshot", "should_pass_ema_filter", "_get_ema_gap", "_format_ema_gap_rule",
    "evaluate_momentum_filter", "neutralize_cas_bar_wicks", "_format_signed",
]
NIFTY_FUNCS = [
    "normalize_ohlcv_dataframe", "resample_complete_ohlcv", "calculate_ema34_bands", "check_signal_against_bands",
    "evaluate_momentum_filter", "neutralize_cas_bar_wicks",
]


def _extract(src_path, names, extra_globals):
    tree = ast.parse(open(src_path).read())
    keep = [n for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name in names]
    # Module-level ALL_CAPS constants the functions may read (plain literals/calls only).
    consts = [n for n in tree.body
              if isinstance(n, ast.Assign) and len(n.targets) == 1
              and isinstance(n.targets[0], ast.Name) and n.targets[0].id.isupper()]
    found = {n.name for n in keep}
    missing = set(names) - found
    if missing:
        raise RuntimeError(f"{src_path}: functions not found: {missing}")
    ns = dict(extra_globals)
    for c in consts:
        try:
            exec(compile(ast.Module(body=[c], type_ignores=[]), src_path, "exec"), ns)
        except Exception:
            pass  # constant depends on runtime config; functions here do not need it
    exec(compile(ast.Module(body=keep, type_ignores=[]), src_path, "exec"), ns)
    return ns


_quiet = logging.getLogger("v2-replay")
_quiet.addHandler(logging.NullHandler())
_quiet.propagate = False

retire = _extract(RETIRE_SRC, RETIRE_FUNCS, {
    "pd": pd, "np": np, "math": math, "datetime": datetime, "ta": ta,
    "sl_logger": _quiet, "logger": _quiet, "CAS_WICK_GUARD_ENABLED": 1,
})
nifty = _extract(NIFTY_SRC, NIFTY_FUNCS, {
    "pd": pd, "np": np, "math": math, "dt_module": datetime, "datetime": datetime.datetime,
    "timedelta": datetime.timedelta, "logger": _quiet, "time": time,
    "_last_signal_reject_log_time": 0.0,
})
