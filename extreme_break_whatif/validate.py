#!/usr/bin/env python3
"""Validate the clean-data replay against what each bot actually logged.

Usage: python3 validate.py 21-10-2026 [22-10-2026 ...]   (default: every downloaded log day)

nifty : every `UPDATED EMA BANDS` (bar OHLC + EMA34 bands) and every momentum verdict.
retire: every `[SL_INDICATORS]` (close, ST, EMA gap) and every flat-book verdict.
"""
import datetime as dt
import glob
import os
import re
import sys

import pandas as pd

import bars as B

GOOGLE = "/Users/vivek/ICICI_Direct/Google"
TOL_PX = 0.06       # bar OHLC: clean data vs broker candles (rounding)
TOL_EMA = 0.5       # EMA34 / ST / EMA gap: seed-window differences allowed
# Current rule (flag=0, "break not required") is continuous from 01-10-2026 13:20 (last
# "intact" 13:15:21, first "not required" 14:25:24). Before that the rule itself differed
# (01-10 morning: "Floor check skipped", red-candle only), so those bars are judged with
# flag=1 for information only and never counted as issues.
FLAG0_LIVE = dt.datetime(2026, 10, 1, 13, 20)


def live_flag(bar_time):
    return 1 if pd.Timestamp(bar_time) < pd.Timestamp(FLAG0_LIVE) else 0


def log_path(bot, day, single=False):
    tag = day.strftime("%d%b%y")
    return f"{GOOGLE}/{bot}/{'app_single_' if single else 'app_'}{tag}.log"


def validate_nifty(day, extra=None):
    path = log_path("nifty", day)
    logged = B.sensex_bars_from_nifty_log(path)
    logged = logged[logged["datetime"].dt.date == day]
    calc = B.nifty_day_bars(day, extra).set_index("datetime")
    rows, bad = 0, []
    for _, r in logged.iterrows():
        if r["datetime"] not in calc.index:
            bad.append((r["datetime"], "bar missing in clean data"))
            continue
        c = calc.loc[r["datetime"]]
        rows += 1
        for k, tol in (("open", TOL_PX), ("high", TOL_PX), ("low", TOL_PX), ("close", TOL_PX),
                       ("ema_high", TOL_EMA), ("ema_low", TOL_EMA)):
            if abs(c[k] - r[k]) > tol:
                bad.append((r["datetime"], f"{k} log {r[k]:.2f} calc {c[k]:.2f} diff {c[k]-r[k]:+.2f}"))
    # verdicts: each momentum line is preceded by its bar's UPDATED EMA BANDS line
    verdicts, vbad = 0, []
    cur_bar = None
    for line in open(path, errors="replace"):
        if "Message logged" in line:
            continue
        m = re.search(r"UPDATED EMA BANDS .*Time=(\S+ \S+)", line)
        if m:
            cur_bar = pd.Timestamp(m.group(1))
            continue
        m = re.search(r"\[INDEX-MOMENTUM\] (LONG|SHORT) (CONFIRMED|SUPPRESSED)", line)
        if m and cur_bar is not None and cur_bar.date() == day and cur_bar in calc.index:
            verdicts += 1
            row = calc.loc[cur_bar].copy()
            row["datetime"] = cur_bar
            side, stage = B.nifty_gate(row, day, flag=live_flag(row["eval_time"]))
            logged_ok = m.group(2) == "CONFIRMED"
            calc_ok = stage in ("pass", "cutoff") and side == m.group(1) if logged_ok else stage == "momentum"
            if not calc_ok:
                vbad.append((cur_bar, f"log {m.group(1)} {m.group(2)} / calc side={side} stage={stage}"))
    return rows, bad, verdicts, vbad


def validate_retire(day, extra=None):
    path = log_path("retire", day, single=True)
    calc = B.retire_day_bars(day, extra)
    by_eval = {r["eval_time"]: r for _, r in calc.iterrows()}
    prev_day_last = calc[calc["datetime"].dt.date < day].iloc[-1]
    pat = re.compile(r"(\d{4}-\d{2}-\d{2}) [\d:,]+ - RetireSingleLegLogger - INFO - \[SL_INDICATORS\] NIFTY (\d\d:\d\d):\d\d \| "
                     r"Close ([\d.]+) [<>=]+ ST ([\d.]+) .*EMA gap ([-+][\d.]+)")
    rows, bad, verdicts, vbad = 0, [], 0, []
    pending = None
    for line in open(path, errors="replace"):
        m = pat.search(line)
        if m:
            slot = pd.Timestamp(f"{m.group(1)} {m.group(2)}")
            slot = (slot - pd.Timedelta(minutes=5)).floor("10min") + pd.Timedelta(minutes=5)
            if slot.time() > dt.time(15, 15):
                pending = None      # post-session cycles re-read the 15:05 bar; no entry gate runs
                continue
            r = prev_day_last if slot.time() == dt.time(9, 15) else by_eval.get(slot)
            if r is None:
                bad.append((slot, "no computed bar for slot"))
                pending = None
                continue
            rows += 1
            lc, lst, lgap = float(m.group(3)), float(m.group(4)), float(m.group(5))
            for name, lv, cv, tol in (("close", lc, r["close"], TOL_PX), ("ST", lst, r["st"], TOL_EMA),
                                      ("EMA gap", lgap, r["ema_gap"], TOL_EMA)):
                if abs(cv - lv) > tol:
                    bad.append((slot, f"{name} log {lv:.2f} calc {cv:.2f} diff {cv-lv:+.2f}"))
            pending = r
            continue
        if pending is None:
            continue
        verdict = None
        if "[SL_ENTRY_BLOCKED_EMA]" in line:
            verdict = "ema"
        elif "[SL_ENTRY_BLOCKED_MOMENTUM]" in line:
            verdict = "momentum"
        elif "[SL_MOM_PASS]" in line:
            verdict = "pass"
        elif "[SL_ENTRY_BLOCKED_POSITION]" in line:
            pending = None      # in a position: gate not evaluated
            continue
        if verdict and "Message logged" not in line:
            verdicts += 1
            opt, stage = B.retire_gate(pending, flag=live_flag(pending["eval_time"]))
            if stage != verdict:
                vbad.append((pending["eval_time"], f"log {verdict} / calc {stage}"))
            pending = None
    return rows, bad, verdicts, vbad


def main(days):
    issues = 0
    for day in days:
        print(f"\n######## {day:%d-%m-%Y} ########")
        for bot, fn in (("nifty", validate_nifty), ("retire", validate_retire)):
            try:
                rows, bad, verdicts, vbad = fn(day)
            except FileNotFoundError:
                print(f"{bot:6}: no log")
                continue
            except (ValueError, IndexError) as e:
                print(f"{bot:6}: day not in clean data ({e})")
                continue
            pre = [b for b in bad + vbad if pd.Timestamp(b[0]) < pd.Timestamp(FLAG0_LIVE)]
            issues += len(bad) + len(vbad) - len(pre)
            if pre:
                print(f"{bot:6}: {len(pre)} mismatch(es) before {FLAG0_LIVE:%d-%m %H:%M} (older rule version, informational)")
            print(f"{bot:6}: bars checked {rows:3}, value mismatches {len(bad):3} | verdicts checked {verdicts:3}, verdict mismatches {len(vbad)}")
            for b in bad[:8] + vbad[:8]:
                print(f"         {b[0]}  {b[1]}")
    print(f"\nVALIDATION {'CLEAN: replay matches every logged bar and verdict' if issues == 0 else f'FOUND {issues} ISSUE(S) - do not trust today until explained'}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ds = [dt.datetime.strptime(a, "%d-%m-%Y").date() for a in sys.argv[1:]]
    else:
        ds = sorted({dt.datetime.strptime(re.search(r"(\d\d\w{3}\d\d)", os.path.basename(p)).group(1), "%d%b%y").date()
                     for p in glob.glob(f"{GOOGLE}/nifty/app_[0-9]*.log")})
    main(ds)
