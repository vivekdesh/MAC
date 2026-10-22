#!/usr/bin/env python3
"""What-if Momentum_Extreme_Break_enabled=1, from the Google Sheets (read-only).

Signals: Log_backup (log_single history) + today's log_single.
P&L:     Results sheet (every closed trade, incl. rollover legs).
Each Results row is attributed to the latest fresh signal on its side with
signal time <= entry time. A chain is "waived" when the momentum line just
before that signal says "break not required" (flag=1 would have blocked it).
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime

import gspread

START = datetime(2026, 10, 1)
WINDOW_START = datetime(2026, 9, 28)   # Momentum_Extreme_Break_enabled introduced 30-09-2026
WAIVED_TOKEN = "break not required"


def _dt(s):
    s = (s or "").strip().lstrip("'")
    for fmt in ("%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


def _num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return None


def load(bot):
    base = f"/Users/vivek/ICICI_Direct/{bot}"
    key = json.load(open(f"{base}/para.json"))["SPREADSHEET_KEY"]
    sh = gspread.service_account(filename=f"{base}/service_account.json").open_by_key(key)
    logs = sh.worksheet("Log_backup").get_all_values() + sh.worksheet("log_single").get_all_values()
    results = sh.worksheet("Results").get_all_values()
    return logs, results


def _log_dt(s):
    """Log_backup dates: Sheets flipped some cells to MM-DD. Pick the reading inside the window."""
    s = (s or "").strip().lstrip("'")
    parts = s.split(" ", 1)
    if len(parts) != 2:
        return _dt(s)
    d, t = parts
    cands = []
    for fmt in ("%d-%m-%Y %H:%M:%S", "%m-%d-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            cands.append(datetime.strptime(f"{d} {t}", fmt))
        except ValueError:
            pass
    ok = [c for c in cands if WINDOW_START <= c <= datetime.now()]
    return ok[0] if ok else None


def signals(bot, logs):
    """Return list of (time, side, waived, text) fresh-signal events, deduped."""
    out, last_mom, seen = [], {}, set()
    started = False
    for r in logs:
        if len(r) < 2:
            continue
        t, msg = _log_dt(r[0]), r[1]
        if t and t.date() == WINDOW_START.date():
            started = True   # rows are appended in time order; skip older MM-DD look-alikes
        if not started or not t or t < START:
            continue
        if bot == "nifty":
            if "[INDEX-MOMENTUM]" in msg and "CONFIRMED" in msg:
                side = "SHORT" if "SHORT CONFIRMED" in msg else "LONG"
                last_mom[side] = (t, WAIVED_TOKEN in msg)
            m = re.search(r"\[NIFTY-TRADE\] New (SHORT|LONG) signal detected", msg)
            if m:
                side = m.group(1)
                mom = last_mom.pop(side, None)
                waived = bool(mom and (t - mom[0]).total_seconds() < 120 and mom[1])
                key = (t.replace(microsecond=0), side)
                if key not in seen:
                    seen.add(key)
                    out.append((t, side, waived, msg))
        else:
            m = re.search(r"\[SL_ENTRY_SIGNAL\] SELL (CE|PE) (\d+)", msg)
            if m:
                key = (t.strftime("%Y-%m-%d %H:%M"), m.group(1))
                if key not in seen:
                    seen.add(key)
                    out.append((t, m.group(1), WAIVED_TOKEN in msg, msg))
    out.sort(key=lambda e: e[0])
    return out


def trades(bot, results):
    out = []
    for r in results[1:]:
        if bot == "nifty":
            if len(r) < 10:
                continue
            et, xt, side, pnl, reason, inst = _dt(r[0]), _dt(r[1]), r[4].strip(), _num(r[8]), r[9], r[2]
        else:
            if len(r) < 12:
                continue
            et, xt, side, pnl, reason, inst = _dt(r[0]), _dt(r[1]), r[10].strip(), _num(r[5]), r[11], r[6] or r[7]
        if not et or not xt or pnl is None or xt < START:
            continue
        out.append({"entry": et, "exit": xt, "side": side, "pnl": pnl, "reason": reason.strip(), "inst": inst})
    out.sort(key=lambda x: x["entry"])
    return out


def attribute(sigs, trs):
    for tr in trs:
        cands = [s for s in sigs if s[1] == tr["side"] and s[0] <= tr["entry"]]
        tr["sig"] = cands[-1] if cands else None
        tr["waived"] = bool(tr["sig"] and tr["sig"][2])


def report(bot, sigs, trs):
    print(f"\n===== {bot.upper()} (from Google Sheets) =====")
    print(f"fresh signals since {START:%d-%m-%Y}: {len(sigs)}, waived: {sum(1 for s in sigs if s[2])}")
    print("Waived chains (flag=1 would have blocked):")
    chains = defaultdict(list)
    for tr in trs:
        if tr["waived"]:
            chains[tr["sig"][0]].append(tr)
    for st in sorted(chains):
        legs = chains[st]
        print(f"  {st:%d-%m %H:%M} {legs[0]['side']:5} chain={sum(l['pnl'] for l in legs):>10.2f} | "
              + "; ".join(f"{l['inst']} {l['pnl']:.0f} {l['reason'][:22]}" for l in legs))
    waived_sigs_without_trade = [s for s in sigs if s[2] and s[0] not in chains]
    for s in waived_sigs_without_trade:
        print(f"  {s[0]:%d-%m %H:%M} {s[1]:5} waived signal with NO closed trade in Results (open / unfilled)")
    days = defaultdict(lambda: [0.0, 0.0, 0, 0])
    for tr in trs:
        d = days[tr["exit"].date()]
        d[0] += tr["pnl"]
        d[2] += 1
        if tr["waived"]:
            d[1] += tr["pnl"]
            d[3] += 1
    print(f"\n{'Date':10} {'trades':>6} {'waived':>6} {'Actual':>10} {'Waived':>10} {'IfFlag=1':>10} "
          f"{'CumActual':>10} {'CumFlag=1':>10} {'Flag=1 gain':>11}")
    ca = cf = 0.0
    for day in sorted(days):
        a, w, n, nw = days[day]
        ca += a
        cf += a - w
        print(f"{day:%d-%m-%Y} {n:>6} {nw:>6} {a:>10.0f} {w:>10.0f} {a - w:>10.0f} {ca:>10.0f} {cf:>10.0f} {cf - ca:>11.0f}")
    unattributed = [t for t in trs if t["sig"] is None]
    if unattributed:
        print(f"  NOTE {len(unattributed)} trade(s) had no fresh signal on/after {START:%d-%m} (carried in): "
              + ", ".join(f"{t['entry']:%d-%m %H:%M} {t['pnl']:.0f}" for t in unattributed))


if __name__ == "__main__":
    for b in (sys.argv[1:] or ["nifty", "retire"]):
        logs, results = load(b)
        sigs, trs = signals(b, logs), trades(b, results)
        attribute(sigs, trs)
        report(b, sigs, trs)
